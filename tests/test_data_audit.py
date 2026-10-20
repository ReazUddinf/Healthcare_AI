"""Basic regression tests for the read-only dataset audit."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.audit_dataset import audit


class AuditTests(unittest.TestCase):
    def test_counts_and_missingness(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fake.csv"
            fields = sorted({
                "encounter_id", "patient_nbr", "race", "gender", "age",
                "number_outpatient", "number_emergency", "number_inpatient",
                "time_in_hospital", "readmitted", "diag_1", "diag_2", "diag_3",
                "num_medications", "A1Cresult", "weight",
            })
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for encounter, patient, label, race in [
                    ("1", "100", "<30", "?"),
                    ("2", "100", ">30", "Caucasian"),
                    ("3", "200", "NO", "Caucasian"),
                ]:
                    writer.writerow({
                        "encounter_id": encounter,
                        "patient_nbr": patient,
                        "readmitted": label,
                        "race": race,
                        "gender": "Female",
                        "age": "[40-50)",
                        "weight": "?",
                    })
            stats = audit(path)
            self.assertEqual(stats["rows"], 3)
            self.assertEqual(stats["unique_patients"], 2)
            self.assertEqual(stats["patients_with_multiple_encounters"], 1)
            self.assertEqual(stats["outcomes"]["<30"], 1)
            self.assertEqual(stats["missingness"]["weight"], 3)
            self.assertEqual(stats["missingness"]["race"], 1)
            self.assertEqual(stats["inconsistent_patient_values"]["race"], 1)
            self.assertEqual(stats["duplicate_encounters"], 0)


if __name__ == "__main__":
    unittest.main()
