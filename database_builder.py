"""Safe ETL entry point for the existing PostgreSQL diabetes database.

Replaces the original destructive version that called Base.metadata.drop_all().

Commands:
    python database_builder.py --validate-csv  # source-only verification
    python database_builder.py --check         # database preflight, no persistent changes
    python database_builder.py --apply         # explicit transactional backfill

This script populates only the eight fields introduced by migration 001 on an
already-initialized five-table database. It does not initialize an empty schema.
"""
from scripts.backfill_clinical_columns import main


if __name__ == "__main__":
    main()
