# Dataset baseline audit — UCI Diabetes 130-US Hospitals

Generated: 2026-10-20
Source: `raw_data/diabetic_data.csv` (local, unmodified input)

## Provenance

UCI dataset: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
License: CC BY 4.0. Keep appropriate attribution in the project documentation.
SHA-256 (CSV): `0689e7ec031237dc63031b938805c48377748761a3b26acab621567afa24df97`

## Structure and target

- Encounters (rows): **101,766**
- Unique encounter identifiers: **101,766**
- Duplicate encounter IDs: **0**
- Unique patient identifiers: **71,518**
- Patients with multiple encounters: **16,773**
- Largest encounter count for any patient: **40**
- Source columns: **50**

| `readmitted` value | Encounter count | Share |
|---|---:|---:|
| `<30` | 11,357 | 11.16% |
| `>30` | 35,545 | 34.93% |
| `NO` | 54,864 | 53.91% |

Proposed primary outcome: **30-day readmission** (`<30` = 1, `>30` or `NO` = 0).
Observed positive class rate: **11.16%**.
Confirm outcome eligibility and prediction-time definition before training.

## Missing-value markers (`?` or empty)

| Field | Count | Share |
|---|---:|---:|
| `weight` | 98,569 | 96.86% |
| `medical_specialty` | 49,949 | 49.08% |
| `payer_code` | 40,256 | 39.56% |
| `race` | 2,273 | 2.23% |
| `diag_1` | 21 | 0.02% |
| `diag_2` | 358 | 0.35% |
| `diag_3` | 1,423 | 1.40% |

## Demographics vary between encounters

Count of unique patients with more than one observed value:

- `race`: **249**
- `gender`: **3**
- `age`: **1,574**

## Pre-training decisions to record

- Preserve `readmitted` as a LABEL, never as an input feature.
- Restore relevant history and medication fields in a versioned, non-destructive ETL refactor.
- Define the prediction moment (e.g. at discharge for readmission).
- Use patient-grouped train/validation/test splits to limit cross-encounter leakage.
- Assess PR-AUC, ROC-AUC, recall, precision, calibration, and subgroup performance.
- Length-of-stay prediction needs an earlier prediction moment to avoid label leakage.
- Cardiovascular risk and a clinically valid composite risk score are not labelled here.
- This is retrospective research data, not a clinically validated decision-support system.

## Security

This report contains aggregates only; patient identifiers and patient-level records are never emitted.
