"""Milestone 1: verified, non-destructive backfill of migration 001 columns.

Safety properties:
- validates the source CSV before any database connection;
- stages only encounter-level data in a PostgreSQL TEMP table;
- verifies complete matching encounter/patient IDs and absence of conflicts;
- leaves existing values unchanged; writes only currently NULL destination fields;
- does not create/drop/truncate/recreate any persistent table;
- defaults to preview mode; requires explicit --apply to change persistent data.

This script assumes the existing five-table baseline and migration 001 have already
been applied. It is NOT a fresh-database loader.
"""
from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path
from typing import Any, TextIO

from dotenv import load_dotenv

STAGING_TABLE = "clinical_backfill_stage"
STAGING_COLUMNS = (
    "encounter_id", "patient_nbr", "readmitted", "number_outpatient",
    "number_emergency", "number_inpatient", "num_procedures",
    "race_at_encounter", "gender_at_encounter", "age_at_encounter",
)
BACKFILL_COLUMNS = STAGING_COLUMNS[2:]
SOURCE_TO_TARGET = {
    "encounter_id": "encounter_id",
    "patient_nbr": "patient_nbr",
    "readmitted": "readmitted",
    "number_outpatient": "number_outpatient",
    "number_emergency": "number_emergency",
    "number_inpatient": "number_inpatient",
    "num_procedures": "num_procedures",
    "race": "race_at_encounter",
    "gender": "gender_at_encounter",
    "age": "age_at_encounter",
}
INTEGER_COLUMNS = frozenset({
    "encounter_id", "patient_nbr", "number_outpatient",
    "number_emergency", "number_inpatient", "num_procedures",
})
LABELS = frozenset({"<30", ">30", "NO"})


def normalize_record(row: dict[str, str]) -> tuple[Any, ...]:
    """Return data ordered exactly as STAGING_COLUMNS; no SQL involved."""
    result: dict[str, Any] = {}
    for source, target in SOURCE_TO_TARGET.items():
        raw = row[source].strip()
        value = None if raw in ("", "?") else raw
        if target in INTEGER_COLUMNS:
            if value is None and target in ("encounter_id", "patient_nbr"):
                raise ValueError(f"Required identifier {target} is missing")
            if value is not None:
                try:
                    value = int(value)
                except ValueError as exc:
                    raise ValueError(f"Invalid integer in {source}") from exc
                if value < 0:
                    raise ValueError(f"Negative value in {source}")
        result[target] = value
    if result["readmitted"] not in LABELS:
        raise ValueError("Unrecognised or missing readmission label")
    return tuple(result[column] for column in STAGING_COLUMNS)


def prepare_csv(source: Path, destination: TextIO) -> int:
    """Validate CSV and spool a COPY-ready file; no persistent output files."""
    rows = 0
    writer = csv.writer(destination, lineterminator="\n")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(SOURCE_TO_TARGET).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV does not include expected columns: {sorted(missing)}")
        for row in reader:
            try:
                record = normalize_record(row)
            except (ValueError, KeyError, AttributeError) as exc:
                raise ValueError(f"Input validation failed at CSV line {rows + 2}: {exc}") from exc
            # COPY FORMAT CSV treats empty unquoted fields as SQL NULL.  All
            # source placeholders '?' and empty strings were normalised above.
            writer.writerow(record)
            rows += 1
    if rows == 0:
        raise ValueError("Source CSV has no rows")
    destination.flush()
    destination.seek(0)
    return rows


def database_settings() -> dict[str, str]:
    load_dotenv()
    env_map = {
        "dbname": "DB_NAME", "user": "DB_USER", "password": "DB_PASSWORD",
        "host": "DB_HOST", "port": "DB_PORT",
    }
    absent = [value for value in env_map.values() if not os.getenv(value)]
    if absent:
        raise RuntimeError(f"Missing database configuration in .env: {', '.join(absent)}")
    return {key: os.environ[source] for key, source in env_map.items()}


def validate_schema(cursor: Any) -> None:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name='admissions'
    """)
    names = {record[0] for record in cursor.fetchall()}
    required = set(STAGING_COLUMNS)
    missing = required.difference(names)
    if missing:
        raise RuntimeError(
            "Migration 001 is missing or incomplete. Missing admissions columns: "
            + ", ".join(sorted(missing))
        )


def stage_data(cursor: Any, stream: TextIO) -> None:
    cursor.execute("""
        CREATE TEMP TABLE clinical_backfill_stage (
            encounter_id INTEGER PRIMARY KEY,
            patient_nbr INTEGER NOT NULL,
            readmitted VARCHAR(3) NOT NULL,
            number_outpatient INTEGER,
            number_emergency INTEGER,
            number_inpatient INTEGER,
            num_procedures INTEGER,
            race_at_encounter VARCHAR,
            gender_at_encounter VARCHAR,
            age_at_encounter VARCHAR
        ) ON COMMIT DROP
    """)
    columns = ", ".join(STAGING_COLUMNS)
    cursor.copy_expert(
        f"COPY {STAGING_TABLE} ({columns}) FROM STDIN WITH (FORMAT csv)",
        stream,
    )


def preflight(cursor: Any, expected_rows: int) -> tuple[int, int]:
    cursor.execute(f"SELECT COUNT(*) FROM {STAGING_TABLE}")
    staged = cursor.fetchone()[0]
    if staged != expected_rows:
        raise RuntimeError(f"Staging count mismatch: {staged} versus {expected_rows}")
    cursor.execute("SELECT COUNT(*) FROM public.admissions")
    existing = cursor.fetchone()[0]
    if existing != staged:
        raise RuntimeError(
            f"Source and admissions row counts differ ({staged} vs {existing}). "
            "Stop: this backfill requires a complete existing baseline."
        )
    cursor.execute(f"""
        SELECT
            (SELECT COUNT(*) FROM {STAGING_TABLE} s
             LEFT JOIN public.admissions a ON a.encounter_id = s.encounter_id
             WHERE a.encounter_id IS NULL),
            (SELECT COUNT(*) FROM public.admissions a
             LEFT JOIN {STAGING_TABLE} s ON s.encounter_id = a.encounter_id
             WHERE s.encounter_id IS NULL),
            (SELECT COUNT(*) FROM {STAGING_TABLE} s
             JOIN public.admissions a ON a.encounter_id = s.encounter_id
             WHERE a.patient_nbr IS DISTINCT FROM s.patient_nbr)
    """)
    missing_in_db, missing_in_source, patient_mismatch = cursor.fetchone()
    if any((missing_in_db, missing_in_source, patient_mismatch)):
        raise RuntimeError(
            "Source/DB identifier verification failed "
            f"(missing in DB: {missing_in_db}; missing in CSV: {missing_in_source}; "
            f"patient mismatches: {patient_mismatch}). No data was changed."
        )
    conflict_conditions = " OR ".join(
        f"(a.{col} IS NOT NULL AND a.{col} IS DISTINCT FROM s.{col})"
        for col in BACKFILL_COLUMNS
    )
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM public.admissions a
        JOIN {STAGING_TABLE} s ON a.encounter_id = s.encounter_id
        WHERE {conflict_conditions}
    """)
    conflicting = cursor.fetchone()[0]
    if conflicting:
        raise RuntimeError(
            f"Backfill conflict: {conflicting} admission(s) contain non-NULL "
            "values different from this CSV. No data was changed."
        )
    cursor.execute("SELECT COUNT(*) FROM public.admissions WHERE readmitted IS NOT NULL")
    filled_before = cursor.fetchone()[0]
    return existing, filled_before


def apply_backfill(cursor: Any) -> int:
    assignments = ", ".join(
        f"{col} = COALESCE(a.{col}, s.{col})" for col in BACKFILL_COLUMNS
    )
    needs_fill = " OR ".join(
        f"(a.{col} IS NULL AND s.{col} IS NOT NULL)" for col in BACKFILL_COLUMNS
    )
    cursor.execute(f"""
        UPDATE public.admissions AS a
        SET {assignments}
        FROM {STAGING_TABLE} AS s
        WHERE a.encounter_id = s.encounter_id
          AND ({needs_fill})
    """)
    return cursor.rowcount


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("raw_data/diabetic_data.csv"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-csv", action="store_true", help="validate local CSV only")
    mode.add_argument("--check", action="store_true", help="preview without updating admissions (default)")
    mode.add_argument("--apply", action="store_true", help="explicitly backfill admissions (transactional)")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Source CSV is missing: {args.input}")

    with tempfile.SpooledTemporaryFile(
        mode="w+", encoding="utf-8", newline="", max_size=16 * 1024 * 1024
    ) as stream:
        count = prepare_csv(args.input, stream)
        print(f"CSV validated: {count:,} encounter rows. No raw rows printed or saved.")
        if args.validate_csv:
            return

        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError("psycopg2-binary is required for the database step") from exc

        # psycopg2's transaction context automatically rolls back on any exception.
        # The temporary staging table disappears when the transaction commits/rolls back.
        with psycopg2.connect(**database_settings(), connect_timeout=10) as connection:
            with connection.cursor() as cursor:
                validate_schema(cursor)
                if args.apply:
                    # Prevent a concurrent writer from changing admissions during
                    # preflight and the subsequent UPDATE.
                    cursor.execute("SET LOCAL lock_timeout = '15s'")
                    cursor.execute("LOCK TABLE public.admissions IN SHARE ROW EXCLUSIVE MODE")
                stage_data(cursor, stream)
                existing, loaded = preflight(cursor, count)
                print(f"Database matches CSV IDs: {existing:,} admissions; labels already set: {loaded:,}.")
                if args.apply:
                    updated = apply_backfill(cursor)
                    cursor.execute("SELECT COUNT(*) FROM public.admissions WHERE readmitted IS NOT NULL")
                    result = cursor.fetchone()[0]
                    if result != count:
                        raise RuntimeError(
                            f"Post-update check failed ({result:,} labels vs {count:,} rows); "
                            "all updates will be rolled back."
                        )
                    print(f"Backfill successful: {updated:,} admission rows updated; "
                          f"{result:,} labels populated. Transaction will be committed.")
                else:
                    print("CHECK ONLY: no persistent database rows were changed.")


if __name__ == "__main__":
    main()
