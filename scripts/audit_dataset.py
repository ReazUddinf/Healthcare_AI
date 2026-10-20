"""Reproducible, read-only audit of the UCI Diabetes 130-US Hospitals dataset.

This program NEVER accesses the project database or writes patient-level data.
Output is restricted to aggregates, schema checks, and dataset provenance.

Run from the project root:
    python scripts/audit_dataset.py --input raw_data/diabetic_data.csv \
      --output reports/data_audit.md
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

EXPECTED_FIELDS = {
    "encounter_id", "patient_nbr", "race", "gender", "age",
    "number_outpatient", "number_emergency", "number_inpatient",
    "time_in_hospital", "readmitted", "diag_1", "diag_2", "diag_3",
    "num_medications", "A1Cresult",
}
MISSINGNESS_FIELDS = [
    "weight", "medical_specialty", "payer_code", "race",
    "diag_1", "diag_2", "diag_3",
]


def digest_file(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def audit(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        required_missing = sorted(EXPECTED_FIELDS.difference(fields))
        if required_missing:
            raise ValueError(f"Expected data fields missing: {required_missing}")
        outcomes = Counter()
        missingness = Counter()
        patient_visits = Counter()
        encounter_ids = set()
        unique_patient_values = defaultdict(set)
        rows = 0
        duplicates = 0
        for row in reader:
            rows += 1
            outcomes[row["readmitted"]] += 1
            for field in MISSINGNESS_FIELDS:
                if field in row and row[field].strip() in ("", "?"):
                    missingness[field] += 1
            patient_id = row["patient_nbr"]
            patient_visits[patient_id] += 1
            for field in ("race", "gender", "age"):
                unique_patient_values[(patient_id, field)].add(row[field])
            encounter_id = row["encounter_id"]
            if encounter_id in encounter_ids:
                duplicates += 1
            encounter_ids.add(encounter_id)
    return {
        "fields": fields,
        "rows": rows,
        "distinct_encounters": len(encounter_ids),
        "duplicate_encounters": duplicates,
        "unique_patients": len(patient_visits),
        "patients_with_multiple_encounters": sum(n > 1 for n in patient_visits.values()),
        "max_encounters_per_patient": max(patient_visits.values(), default=0),
        "outcomes": outcomes,
        "missingness": missingness,
        "inconsistent_patient_values": {
            field: sum(len(values) > 1 for (patient, name), values in unique_patient_values.items() if name == field)
            for field in ("race", "gender", "age")
        },
        "sha256": digest_file(path),
    }


def make_report(stats: dict, source: str = "raw_data/diabetic_data.csv") -> str:
    rows = stats["rows"]
    outcomes = stats["outcomes"]
    positive = outcomes["<30"]
    lines = [
        "# Dataset baseline audit — UCI Diabetes 130-US Hospitals",
        "",
        f"Generated: {date.today().isoformat()}",
        f"Source: `{source}` (local, unmodified input)",
        "",
        "## Provenance",
        "",
        "UCI dataset: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008",
        "License: CC BY 4.0. Keep appropriate attribution in the project documentation.",
        f"SHA-256 (CSV): `{stats['sha256']}`",
        "",
        "## Structure and target",
        "",
        f"- Encounters (rows): **{rows:,}**",
        f"- Unique encounter identifiers: **{stats['distinct_encounters']:,}**",
        f"- Duplicate encounter IDs: **{stats['duplicate_encounters']:,}**",
        f"- Unique patient identifiers: **{stats['unique_patients']:,}**",
        f"- Patients with multiple encounters: **{stats['patients_with_multiple_encounters']:,}**",
        f"- Largest encounter count for any patient: **{stats['max_encounters_per_patient']:,}**",
        f"- Source columns: **{len(stats['fields'])}**",
        "",
        "| `readmitted` value | Encounter count | Share |",
        "|---|---:|---:|",
    ]
    for label in ("<30", ">30", "NO"):
        count = outcomes[label]
        lines.append(f"| `{label}` | {count:,} | {100 * count / rows:.2f}% |")
    lines += [
        "",
        "Proposed primary outcome: **30-day readmission** (`<30` = 1, `>30` or `NO` = 0).",
        f"Observed positive class rate: **{100 * positive / rows:.2f}%**.",
        "Confirm outcome eligibility and prediction-time definition before training.",
        "",
        "## Missing-value markers (`?` or empty)",
        "",
        "| Field | Count | Share |",
        "|---|---:|---:|",
    ]
    for name in MISSINGNESS_FIELDS:
        if name in stats["fields"]:
            value = stats["missingness"][name]
            lines.append(f"| `{name}` | {value:,} | {100 * value / rows:.2f}% |")
    lines += [
        "",
        "## Demographics vary between encounters",
        "",
        "Count of unique patients with more than one observed value:",
        "",
    ]
    for name, count in stats["inconsistent_patient_values"].items():
        lines.append(f"- `{name}`: **{count:,}**")
    lines += [
        "",
        "## Pre-training decisions to record",
        "",
        "- Preserve `readmitted` as a LABEL, never as an input feature.",
        "- Restore relevant history and medication fields in a versioned, non-destructive ETL refactor.",
        "- Define the prediction moment (e.g. at discharge for readmission).",
        "- Use patient-grouped train/validation/test splits to limit cross-encounter leakage.",
        "- Assess PR-AUC, ROC-AUC, recall, precision, calibration, and subgroup performance.",
        "- Length-of-stay prediction needs an earlier prediction moment to avoid label leakage.",
        "- Cardiovascular risk and a clinically valid composite risk score are not labelled here.",
        "- This is retrospective research data, not a clinically validated decision-support system.",
        "",
        "## Security",
        "",
        "This report contains aggregates only; patient identifiers and patient-level records are never emitted.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("raw_data/diabetic_data.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/data_audit.md"))
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"CSV not found: {args.input}")
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output paths must differ")
    stats = audit(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(make_report(stats), encoding="utf-8")
    print(f"Audit complete: {stats['rows']:,} encounters, {stats['unique_patients']:,} patients.")
    print(f"Read-only report saved to: {args.output}")


if __name__ == "__main__":
    main()
