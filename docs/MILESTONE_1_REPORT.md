# Milestone 1 — PostgreSQL schema and ETL reliability

**Project:** Healthcare AI — Clinical Decision Support Research Prototype  
**Status:** Implementation verified locally; Git commit/push pending  
**Date:** 2026-10-20  
**Scope:** Retrospective UCI Diabetes 130-US Hospitals dataset; research and portfolio use only.

## Purpose

Replace the destructive database-refresh workflow with an additive schema migration and an explicit, repeatable ETL backfill. Preserve existing encounters and relational integrity while making the admission-level 30-day readmission target and relevant predictors available for later experiments.

## Work completed

1. **Read-only database audit.** Inspected the five existing tables and identified missing outcomes/features and absent foreign-key constraints.
2. **Integrity precheck.** Confirmed zero missing patient IDs and zero orphan rows across admissions, diagnoses, medications and lab tests.
3. **Backup.** Created a pre-migration PostgreSQL backup outside the Git repository.
4. **Additive migration.** Ran `migrations/001_expand_clinical_schema.sql` to add eight columns to `admissions` and four foreign-key constraints without dropping or recreating tables.
5. **Safer ETL entry point.** Replaced the original `database_builder.py` with an interface supporting `--validate-csv`, `--check` and explicit `--apply` modes.
6. **Transactional backfill.** Populated eight new admission fields from the existing local CSV. Subsequent execution detected no changes to apply.
7. **SQL verification.** User reported that all four queries in `sql/verify_001_backfill.sql` passed after backfill.

## Implemented admission fields

- **Outcome label:** `readmitted` (source categories `<30`, `>30`, and `NO`; never treat as an input feature).
- **Hospital utilization:** `number_outpatient`, `number_emergency`, `number_inpatient`.
- **Encounter attributes:** `num_procedures`, `race_at_encounter`, `gender_at_encounter`, `age_at_encounter`.

## Evidence from local execution

| Check | Observed result |
|---|---|
| Unit tests | 7 passed (`python -m unittest discover -s tests -v`) |
| CSV validation | 101,766 encounter rows |
| Preflight | 101,766 admission IDs matched; zero labels initially populated |
| Initial `--apply` | 101,766 admissions updated; 101,766 labels populated |
| Second `--apply` | Zero admissions updated; 101,766 labels populated |
| SQL checks A–D | Reported passed by user |
| Migration integrity | Four foreign keys were added, and earlier orphan checks returned zero |

These are checks of ETL correctness and reproducibility, **not** evidence of clinical safety or predictive performance.

## Commands for reproducibility

From the project root on a machine configured with the original dataset, an appropriate `.env`, and a PostgreSQL database with migration 001 already applied:

```powershell
python -m unittest discover -s tests -v
python database_builder.py --validate-csv
python database_builder.py --check
python database_builder.py --apply
```

Use `sql/verify_001_schema.sql` and `sql/verify_001_backfill.sql` in pgAdmin for post-migration and post-backfill database checks. The `--apply` mode writes to PostgreSQL; always run `--check` first. The current loader **does not create a new database from scratch**.

## Important limitations and work still pending

- Only the eight migration-001 admission fields are added/backfilled at this milestone. A complete import of all source medication variables, and a fully initialized fresh-database workflow, are not implemented.
- The database includes a retrospective *recorded readmission* outcome; its prediction horizon, eligibility rules, potential data leakage and model usefulness still require careful definition and evaluation.
- One patient can have multiple encounters. In Milestone 2, split data by patient to prevent the same patient entering both training and test datasets.
- Decide which variables would have been available at the selected prediction time, such as discharge, before constructing features.
- No ML classifier, local open-weight LLM, SHAP explanations or clinical dashboard has been evaluated as part of this milestone.
- This system is **not clinically validated**, not medical advice, and not suitable for real clinical deployment.

## Version control and data handling

Commit only source code, migration SQL, tests, aggregate audit results and documentation. Do **not** commit `.env`, credentials, virtual environments, the raw CSV, row-level data, database backups, model weights or sensitive logs. Do not use `git add .` without first auditing every staged file.

**Suggested commit:** `refactor(etl): preserve readmission labels and enforce database integrity`

## Next milestone

**Milestone 2 — Prediction cohort and feature engineering.** Define the intended prediction time, cohort and target; build a single encounter-level view from SQL joins; select leakage-safe predictors; introduce patient-grouped train/validation/test partitions; and record feature provenance with repeatable data checks.
