# Milestone 1 — PostgreSQL schema baseline

Generated: 2026-10-20

Read-only inspection of the five existing public tables. 
No patient-level rows, secrets, or connection strings are included.

## patients

Rows: **71,518**
Primary key: `patient_nbr`
Foreign keys: **0**

| Column | SQL type | Nullable |
|---|---|---|
| `patient_nbr` | `INTEGER` | no |
| `race` | `VARCHAR` | yes |
| `gender` | `VARCHAR` | yes |
| `age` | `VARCHAR` | yes |

## admissions

Rows: **101,766**
Primary key: `encounter_id`
Foreign keys: **0**

| Column | SQL type | Nullable |
|---|---|---|
| `encounter_id` | `INTEGER` | no |
| `patient_nbr` | `INTEGER` | yes |
| `admission_type_id` | `INTEGER` | yes |
| `discharge_disposition_id` | `INTEGER` | yes |
| `admission_source_id` | `INTEGER` | yes |
| `time_in_hospital` | `INTEGER` | yes |

## diagnoses

Rows: **101,766**
Primary key: `encounter_id`
Foreign keys: **0**

| Column | SQL type | Nullable |
|---|---|---|
| `encounter_id` | `INTEGER` | no |
| `diag_1` | `VARCHAR` | yes |
| `diag_2` | `VARCHAR` | yes |
| `diag_3` | `VARCHAR` | yes |
| `number_diagnoses` | `INTEGER` | yes |

## medications

Rows: **101,766**
Primary key: `encounter_id`
Foreign keys: **0**

| Column | SQL type | Nullable |
|---|---|---|
| `encounter_id` | `INTEGER` | no |
| `num_medications` | `INTEGER` | yes |
| `diabetesMed` | `VARCHAR` | yes |
| `change` | `VARCHAR` | yes |
| `insulin` | `VARCHAR` | yes |

## lab_tests

Rows: **101,766**
Primary key: `encounter_id`
Foreign keys: **0**

| Column | SQL type | Nullable |
|---|---|---|
| `encounter_id` | `INTEGER` | no |
| `num_lab_procedures` | `INTEGER` | yes |
| `max_glu_serum` | `VARCHAR` | yes |
| `A1Cresult` | `VARCHAR` | yes |

## Follow-up items

- Not yet present: admissions.readmitted
- Not yet present: admissions.number_outpatient
- Not yet present: admissions.number_emergency
- Not yet present: admissions.number_inpatient
- No foreign keys defined on admissions
- No foreign keys defined on diagnoses
- No foreign keys defined on medications
- No foreign keys defined on lab_tests

