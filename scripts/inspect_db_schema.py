"""Read-only PostgreSQL schema and row-count audit for Healthcare_AI.

Usage (run from repository root):
    python scripts/inspect_db_schema.py

This tool NEVER imports database_builder.py, alters SQL objects, or exports
row-level records. It reports only table definitions and aggregate counts.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

SCHEMA = "public"
EXPECTED_TABLES = (
    "patients",
    "admissions",
    "diagnoses",
    "medications",
    "lab_tests",
)
EXPECTED_PK = {
    "patients": "patient_nbr",
    "admissions": "encounter_id",
    "diagnoses": "encounter_id",
    "medications": "encounter_id",
    "lab_tests": "encounter_id",
}
REQUIRED_FOR_ML = {
    "admissions": (
        "readmitted",
        "number_outpatient",
        "number_emergency",
        "number_inpatient",
    ),
}


def make_url():
    load_dotenv()
    needed = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    missing = [name for name in needed if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )


def audit_database() -> tuple[list[str], list[str]]:
    """Return Markdown report lines and warnings; no user records are fetched."""
    lines = [
        "# Milestone 1 — PostgreSQL schema baseline",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Read-only inspection of the five existing public tables. ",
        "No patient-level rows, secrets, or connection strings are included.",
        "",
    ]
    warnings: list[str] = []
    engine = create_engine(make_url(), connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as conn:
            with conn.begin():
                # Must be the first SQL statement in the transaction.
                conn.exec_driver_sql("SET TRANSACTION READ ONLY")
                inspector = inspect(conn)
                existing = set(inspector.get_table_names(schema=SCHEMA))
                for table in EXPECTED_TABLES:
                    lines.append(f"## {table}")
                    lines.append("")
                    if table not in existing:
                        warnings.append(f"Missing table: {table}")
                        lines += ["**MISSING TABLE**", ""]
                        continue

                    # The SQL identifiers are fixed constants in EXPECTED_TABLES.
                    count = conn.exec_driver_sql(
                        f'SELECT COUNT(*) FROM "{SCHEMA}"."{table}"'
                    ).scalar_one()
                    columns = inspector.get_columns(table, schema=SCHEMA)
                    actual_names = {col["name"] for col in columns}
                    pk_columns = inspector.get_pk_constraint(table, schema=SCHEMA).get(
                        "constrained_columns", []
                    ) or []
                    fks = inspector.get_foreign_keys(table, schema=SCHEMA)

                    lines += [
                        f"Rows: **{count:,}**",
                        f"Primary key: `{', '.join(pk_columns) or 'NONE'}`",
                        f"Foreign keys: **{len(fks)}**",
                        "",
                        "| Column | SQL type | Nullable |",
                        "|---|---|---|",
                    ]
                    for col in columns:
                        lines.append(
                            f"| `{col['name']}` | `{col['type']}` | "
                            f"{'yes' if col['nullable'] else 'no'} |"
                        )
                    lines.append("")
                    if pk_columns != [EXPECTED_PK[table]]:
                        warnings.append(f"Unexpected primary key: {table} => {pk_columns}")
                    for name in REQUIRED_FOR_ML.get(table, ()):
                        if name not in actual_names:
                            warnings.append(f"Not yet present: {table}.{name}")
                    if table != "patients" and not fks:
                        warnings.append(f"No foreign keys defined on {table}")

                # Require correct row counts only as advisory checks: the user
                # might have loaded a subset or rerun a different ETL.
                lines.append("## Follow-up items")
                lines.append("")
                lines.extend(f"- {item}" for item in warnings)
                if not warnings:
                    lines.append("- No schema warnings found")
                lines.append("")
    finally:
        engine.dispose()
    return lines, warnings


def main() -> None:
    try:
        lines, warnings = audit_database()
    except (SQLAlchemyError, OSError, ValueError) as exc:
        # Do not print SQLAlchemy DSNs or passwords in logs.
        raise SystemExit(
            f"Schema audit could not complete ({type(exc).__name__}). "
            "Check that PostgreSQL is running and your .env settings are valid."
        ) from None
    output = Path("reports/db_schema_audit.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Read-only database inspection completed. Warnings: {len(warnings)}")
    print(f"Report saved to: {output}")
    for warning in warnings:
        print(f"  - {warning}")


if __name__ == "__main__":
    main()
