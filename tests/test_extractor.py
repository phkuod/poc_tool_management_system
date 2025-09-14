import unittest
import pandas as pd
from outsourcing_qc_extractor import OutsourcingQcExtractor
import os

class TestOutsourcingQcExtractor(unittest.TestCase):

    def setUp(self):
        # Create a dummy Excel file for testing
        self.test_file = 'test_schedule.xlsx'
        data = {
            'Tool_Number': ['T001'],
            'Tool Column': ['ProjectA'],
            'Customer schedule': ['2025-07-15'],
            'Responsible User': ['test@example.com'],
            'Vendor': ['vendor_a']
        }
        df = pd.DataFrame(data)
        df.to_excel(self.test_file, index=False)

    def tearDown(self):
        # Remove the dummy Excel file
        os.remove(self.test_file)

    def test_get_raw_data_success(self):
        # Test successful data extraction
        extractor = OutsourcingQcExtractor(self.test_file)
        df = extractor.get_raw_data()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)

    def test_get_raw_data_file_not_found(self):
        # Test FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            extractor = OutsourcingQcExtractor('non_existent_file.xlsx')
            extractor.get_raw_data()

    def test_get_raw_data_missing_columns(self):
        # Test missing columns validation
        data = {
            'Tool_Number': ['T001'],
            'Tool Column': ['ProjectA'],
        }
        df = pd.DataFrame(data)
        df.to_excel(self.test_file, index=False)

        with self.assertRaises(ValueError):
            extractor = OutsourcingQcExtractor(self.test_file)
            extractor.get_raw_data()

if __name__ == '__main__':
    unittest.main()
