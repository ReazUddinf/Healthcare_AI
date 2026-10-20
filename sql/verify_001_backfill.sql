

-- Query A: labels should equal admissions total (expected 101,766).
-- The 0-valued number_* fields are VALID populated values, not missing.
SELECT
 COUNT(*) AS admissions,
 COUNT(readmitted) AS labelled_encounters,
 COUNT(number_outpatient) AS outpatient_present,
 COUNT(number_emergency) AS emergency_present,
 COUNT(number_inpatient) AS inpatient_present,
 COUNT(num_procedures) AS procedures_present,
 COUNT(race_at_encounter) AS race_present,
 COUNT(gender_at_encounter) AS gender_present,
 COUNT(age_at_encounter) AS age_present
FROM public.admissions;

-- Query B: labels should match the source aggregate distribution:
-- <30 = 11,357; >30 = 35,545; NO = 54,864.
SELECT readmitted, COUNT(*) AS encounters
FROM public.admissions
GROUP BY readmitted
ORDER BY readmitted;

-- Query C: original row counts should NOT change.
SELECT
 (SELECT COUNT(*) FROM public.patients) AS patients,
 (SELECT COUNT(*) FROM public.admissions) AS admissions,
 (SELECT COUNT(*) FROM public.diagnoses) AS diagnoses,
 (SELECT COUNT(*) FROM public.medications) AS medications,
 (SELECT COUNT(*) FROM public.lab_tests) AS lab_tests;

-- Query D: no orphan rows (expected all zeros).
SELECT
 (SELECT COUNT(*) FROM public.admissions a LEFT JOIN public.patients p
  ON a.patient_nbr = p.patient_nbr WHERE p.patient_nbr IS NULL) AS orphan_admissions,
 (SELECT COUNT(*) FROM public.diagnoses d LEFT JOIN public.admissions a
  ON d.encounter_id = a.encounter_id WHERE a.encounter_id IS NULL) AS orphan_diagnoses,
 (SELECT COUNT(*) FROM public.medications m LEFT JOIN public.admissions a
  ON m.encounter_id = a.encounter_id WHERE a.encounter_id IS NULL) AS orphan_medications,
 (SELECT COUNT(*) FROM public.lab_tests l LEFT JOIN public.admissions a
  ON l.encounter_id = a.encounter_id WHERE a.encounter_id IS NULL) AS orphan_lab_tests;
