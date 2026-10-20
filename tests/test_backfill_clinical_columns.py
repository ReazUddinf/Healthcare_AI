"""Offline regression tests for migration 001 ETL transformation and safety."""
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

from scripts.backfill_clinical_columns import (
    BACKFILL_COLUMNS,
    STAGING_COLUMNS,
    normalize_record,
    prepare_csv,
)


BASE_ROW = {
    "encounter_id": "123", "patient_nbr": "456", "readmitted": "<30",
    "number_outpatient": "0", "number_emergency": "2", "number_inpatient": "3",
    "num_procedures": "0", "race": "?", "gender": "Female", "age": "[50-60)",
}


class BackfillTransformTests(unittest.TestCase):
    def test_normalises_missing_markers_and_preserves_zero(self):
        row = dict(zip(STAGING_COLUMNS, normalize_record(BASE_ROW)))
        self.assertEqual(len(BACKFILL_COLUMNS), 8)
        self.assertEqual(row["readmitted"], "<30")
        self.assertEqual(row["number_outpatient"], 0)
        self.assertEqual(row["number_emergency"], 2)
        self.assertIsNone(row["race_at_encounter"])
        self.assertEqual(row["age_at_encounter"], "[50-60)")

    def test_rejects_unrecognised_labels(self):
        with self.assertRaisesRegex(ValueError, "readmission label"):
            normalize_record({**BASE_ROW, "readmitted": "UNKNOWN"})

    def test_rejects_invalid_nonnegative_counts(self):
        with self.assertRaisesRegex(ValueError, "Negative value"):
            normalize_record({**BASE_ROW, "number_inpatient": "-1"})
        with self.assertRaisesRegex(ValueError, "Invalid integer"):
            normalize_record({**BASE_ROW, "num_procedures": "invalid"})

    def test_spools_csv_without_creating_database(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "tiny.csv"
            with path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(BASE_ROW))
                writer.writeheader()
                writer.writerow(BASE_ROW)
                writer.writerow({**BASE_ROW, "encounter_id": "124", "readmitted": "NO"})
            with io.StringIO() as output:
                self.assertEqual(prepare_csv(path, output), 2)
                copy_rows = list(csv.reader(io.StringIO(output.getvalue())))
                self.assertEqual(len(copy_rows), 2)
                self.assertEqual(copy_rows[0][0], "123")
                self.assertEqual(copy_rows[0][7], "")
                self.assertEqual(copy_rows[1][2], "NO")

    def test_copy_output_handles_empty_fields(self):
        row = normalize_record({**BASE_ROW, "gender": "?", "age": "?"})
        self.assertIsNone(row[-2])
        self.assertIsNone(row[-1])


if __name__ == "__main__":
    unittest.main()
