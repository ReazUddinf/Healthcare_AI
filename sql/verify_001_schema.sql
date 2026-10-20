

-- Query A: Expect eight rows (the columns added to admissions).
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'admissions'
  AND column_name IN (
    'readmitted', 'number_outpatient', 'number_emergency',
    'number_inpatient', 'num_procedures', 'race_at_encounter',
    'gender_at_encounter', 'age_at_encounter'
  )
ORDER BY column_name;

-- Query B: Expect four rows, one for each intended FK.
SELECT conrelid::regclass AS child_table,
       conname AS foreign_key_name,
       pg_get_constraintdef(oid) AS definition,
       convalidated AS validated
FROM pg_constraint
WHERE contype = 'f'
  AND conname IN (
    'fk_admissions_patients',
    'fk_diagnoses_admissions',
    'fk_medications_admissions',
    'fk_lab_tests_admissions'
  )
ORDER BY 1;

-- Query C: All counts should remain exactly as in the schema baseline.
SELECT
 (SELECT count(*) FROM public.patients) AS patients,
 (SELECT count(*) FROM public.admissions) AS admissions,
 (SELECT count(*) FROM public.diagnoses) AS diagnoses,
 (SELECT count(*) FROM public.medications) AS medications,
 (SELECT count(*) FROM public.lab_tests) AS lab_tests;

-- Query D: New readmission values should still be NULL before the ETL backfill.
SELECT COUNT(*) AS admissions_total,
       COUNT(readmitted) AS readmission_labels_loaded
FROM public.admissions;
