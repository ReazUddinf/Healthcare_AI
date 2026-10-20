"""Safe structural checks for the read-only schema audit."""
import ast
import unittest
from pathlib import Path


class SchemaInspectionTests(unittest.TestCase):
    def test_expected_tables_and_no_direct_database_mutations(self):
        path = Path(__file__).resolve().parents[1] / 'scripts' / 'inspect_db_schema.py'
        source = path.read_text(encoding='utf-8')
        ast.parse(source)
        for table in ('patients', 'admissions', 'diagnoses', 'medications', 'lab_tests'):
            self.assertIn(f'"{table}"', source)
        self.assertIn('SET TRANSACTION READ ONLY', source)
        self.assertNotIn('metadata.drop_all', source)
        self.assertNotIn('metadata.create_all', source)
        self.assertNotIn('database_builder', source.replace('database_builder.py', ''))


if __name__ == '__main__':
    unittest.main()
