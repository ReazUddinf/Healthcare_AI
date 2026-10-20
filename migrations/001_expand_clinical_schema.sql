

BEGIN;

SET LOCAL lock_timeout = '15s';
SET LOCAL statement_timeout = '120s';


ALTER TABLE public.admissions
    ADD COLUMN IF NOT EXISTS readmitted VARCHAR(3),
    ADD COLUMN IF NOT EXISTS number_outpatient INTEGER,
    ADD COLUMN IF NOT EXISTS number_emergency INTEGER,
    ADD COLUMN IF NOT EXISTS number_inpatient INTEGER,
    ADD COLUMN IF NOT EXISTS num_procedures INTEGER,
    ADD COLUMN IF NOT EXISTS race_at_encounter VARCHAR,
    ADD COLUMN IF NOT EXISTS gender_at_encounter VARCHAR,
    ADD COLUMN IF NOT EXISTS age_at_encounter VARCHAR;


DO $constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.admissions'::regclass
          AND conname = 'fk_admissions_patients'
    ) THEN
        ALTER TABLE public.admissions
            ADD CONSTRAINT fk_admissions_patients
            FOREIGN KEY (patient_nbr)
            REFERENCES public.patients(patient_nbr);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.diagnoses'::regclass
          AND conname = 'fk_diagnoses_admissions'
    ) THEN
        ALTER TABLE public.diagnoses
            ADD CONSTRAINT fk_diagnoses_admissions
            FOREIGN KEY (encounter_id)
            REFERENCES public.admissions(encounter_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.medications'::regclass
          AND conname = 'fk_medications_admissions'
    ) THEN
        ALTER TABLE public.medications
            ADD CONSTRAINT fk_medications_admissions
            FOREIGN KEY (encounter_id)
            REFERENCES public.admissions(encounter_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.lab_tests'::regclass
          AND conname = 'fk_lab_tests_admissions'
    ) THEN
        ALTER TABLE public.lab_tests
            ADD CONSTRAINT fk_lab_tests_admissions
            FOREIGN KEY (encounter_id)
            REFERENCES public.admissions(encounter_id);
    END IF;
END
$constraints$;

COMMIT;
