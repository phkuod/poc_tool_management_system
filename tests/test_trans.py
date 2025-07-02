import unittest
import pandas as pd
from datetime import datetime, timedelta
from outsourcing_qc_trans import OutsourcingQcTrans

class TestOutsourcingQcTrans(unittest.TestCase):

    def test_get_transformed_data(self):
        # Create a sample DataFrame for testing
        today = datetime.now()
        data = {
            'Customer schedule': [
                today + timedelta(days=10),
                today + timedelta(days=30), # Should be filtered out
                today - timedelta(days=5),  # Should be filtered out
            ],
            'Tool_Number': ['T001', 'T002', 'T003'],
            'Tool Column': ['ProjectA', 'ProjectB', 'ProjectC'],
            'Responsible User': ['user1', 'user2', 'user3']
        }
        df = pd.DataFrame(data)

        # Apply the transformation
        transformer = OutsourcingQcTrans(df)
        transformed_df = transformer.get_transformed_data()

        # Assertions
        self.assertEqual(len(transformed_df), 1)
        self.assertIn('Project Start Date', transformed_df.columns)
        
        # Check the 'Project Start Date' calculation
        expected_start_date = pd.to_datetime(today + timedelta(days=10)) - timedelta(weeks=3)
        self.assertEqual(transformed_df.iloc[0]['Project Start Date'].date(), expected_start_date.date())

if __name__ == '__main__':
    unittest.main()
