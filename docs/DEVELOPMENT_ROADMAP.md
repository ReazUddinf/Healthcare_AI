# Healthcare AI — engineering and evaluation roadmap

**Purpose:** Research/portfolio prototype for retrospective diabetic hospital readmission analysis, explainable models, and carefully constrained *local* LLM summarisation. **Not** a validated medical device; do not deploy for clinical decision-making.

Source dataset: [UCI Diabetes 130-US Hospitals (1999–2008)](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008) (CC BY 4.0; include attribution). No live patient data.

## Rules for every milestone

1. Make one narrowly scoped change and explain its purpose.
2. Run tests and inspect output. Do not advance on failing checks.
3. Update this roadmap, `README.md`, and a short development log.
4. Stage source and documentation **explicitly**. Inspect `git diff --cached` before commit.
5. Commit using Conventional Commits and push only after reviewing changes. Keep data, `.env`, `venv`, database dumps, model weights, and unredacted logs out of Git.
6. Preserve model/config/library versions, seeds, cohort rules and evaluation settings. Record aggregate metrics, never patient-level examples.

## Milestone definitions and gates

| ID | Milestone | Definition of done | Suggested commit |
|---|---|---|---|
| M0 | Audit and scope | Read-only audit report, working tests, documented outcomes, clean/safe repo | `docs(data): establish reproducible audit baseline` |
| M1 | ETL reliability | Re-run without destructive `drop_all`; versioned schema and constraints; source target and needed features recoverable | `refactor(etl): preserve readmission labels and clinical features` |
| M2 | Prediction cohort and features | Explicit prediction time, patient-grouped split, leakage checks, feature provenance, reproducible train/val/test exports | `feat(features): build leakage-checked discharge cohort` |
| M3 | Readmission baselines | Dummy classifier + logistic regression baseline, fixed split/seed, PR-AUC/ROC-AUC, precision/recall and calibration | `feat(ml): establish readmission baselines` |
| M4 | Model experiments | Gradient-boosting models, selection exclusively on validation, held-out test evaluation, subgroup analysis, documented error analysis | `feat(ml): compare calibrated readmission models` |
| M5 | Explainability and safeguards | SHAP and feature provenance, explain non-causality, threshold choices and uncertainty, no medical recommendations | `feat(xai): add validated feature explanations` |
| M6 | Local open-weight LLM benchmark | Hardware inventory, locked prompt/test set, local-only inference, model and quantisation comparison with hallucination/faithfulness checks | `feat(llm): benchmark local clinical summarizers` |
| M7 | Prototype UI and API | Streamlit dashboard, structured SQL/ML results, opt-in summarization, FastAPI with schema validation and failure-handling | `feat(app): connect evidence-backed dashboard` |
| M8 | Reproducibility and release | Docker/CI where feasible, README and model card, limitations/security checks, safe demo deployment or local instructions | `chore(release): document reproducible research prototype` |

**Scope control:** A cardiovascular-risk predictor is not a justified outcome on this dataset. A general 0–100 'clinical risk score' is not an established measure and must not be represented as validated; it can be omitted until an external labelled outcome and evaluation plan are identified. Length-of-stay modelling can be separate if its prediction time is defined and post-outcome features excluded.

## Benchmark protocol (M6)

- Use the identical input records, factual evidence snippets, safety instructions, response schema, context window, generation settings, and evaluation rubric across models wherever supported.
- Record the Ollama version, exact model tag and hash, quantization, CPU/GPU, RAM/VRAM, context length, temperature, prompt version, and benchmark seed.
- Evaluate groundedness, unsupported claims, omissions, structured-output validity, abstention when fields are absent, mean and p95 latency, token throughput, and observed memory use. Clinician review would be necessary for any clinical adequacy claim.
- Include an extractive/rule-based summariser as a reliability control before attributing improvements to an LLM.
- Do not expose the local Ollama API to the public Internet or send real identifiable records to unapproved providers.

## Local model shortlist (subject to hardware)

- `qwen3:4b` (2.5 GB model download), `phi4-mini` (2.5 GB): smaller baseline candidates.
- `gemma3:4b` (~3.4 GB): alternative family; examine Google Gemma terms before distribution.
- `qwen3:8b` (~5.2 GB): larger counterpart for a quality/latency tradeoff if RAM/VRAM permits.
- Download size is **not** the same as inference RAM/VRAM; context/KV cache and runtime overhead matter. Some tags also change over time: record hashes.
- Qwen3 open weights have Apache 2.0 terms; licenses vary across families. Verify upstream model cards and licenses before sharing.

## Version-control workflow

```bash
git status
git diff
git add scripts/audit_dataset.py tests/test_data_audit.py docs/DEVELOPMENT_ROADMAP.md reports/data_audit.md README.md
git diff --cached --stat
git diff --cached
git commit -m "docs(data): establish reproducible audit baseline"
git push origin main
```

Only stage `README.md` when the user has deliberately accepted the template. Avoid `git add .` while the repository contains secrets or large files. Never force-push in a routine milestone.
