# Healthcare AI — Clinical Decision Support Research Prototype

An experimental, end-to-end pipeline for retrospective readmission modelling on the **UCI Diabetes 130-US Hospitals (1999–2008)** dataset. Planned components include PostgreSQL ETL, leakage-aware readmission prediction, explainability, and an evaluated, locally deployed open-weight LLM for factual record summaries.

> **Research/portfolio prototype only.** It is not clinically validated, not intended for patient treatment or clinical deployment, and must not be presented as a production hospital system.

## Status

- Existing: Python ETL and PostgreSQL table definitions (patients, admissions, diagnoses, medications, lab_tests).
- Current priority: a reproducible, read-only dataset audit and schema review before further ETL updates.
- Next: preserve readmission outcome and omitted predictors; remove destructive database resetting; establish safe patient-grouped evaluation.

See [Development Roadmap](docs/DEVELOPMENT_ROADMAP.md) and [Dataset Baseline Audit](reports/data_audit.md).

## Source dataset

[Diabetes 130-US Hospitals for Years 1999–2008](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008), UCI Machine Learning Repository. DOI: [10.24432/C5230J](https://doi.org/10.24432/C5230J). Licensed **CC BY 4.0**. Retain attribution when using or adapting data.

Your raw CSV is stored locally as `raw_data/diabetic_data.csv` and should not be committed. The dataset includes sensitive demographic variables. We only commit aggregate audit results.

## First safe milestone: audit only

From the project root (with Python 3.11 or equivalent installed):

```bash
python -m unittest discover -s tests -v
python scripts/audit_dataset.py --input raw_data/diabetic_data.csv --output reports/data_audit.md
```

This reads the CSV and writes an aggregate Markdown report. **It never connects to PostgreSQL or modifies source rows.**

## Security and reproducibility

Keep `.env`, database credentials, `venv/`, model weights, datasets, raw encounter logs, and reports containing row-level data off GitHub. Review staged diffs before each commit. Use patient-grouped splits and define the prediction moment before building risk models.
