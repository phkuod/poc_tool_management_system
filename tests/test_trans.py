import unittest
import pandas as pd
from datetime import datetime, timedelta
from outsourcing_qc_trans import OutsourcingQcTrans
from taiwan_holidays import TaiwanBusinessDay

class TestOutsourcingQcTrans(unittest.TestCase):

    def test_get_transformed_data(self):
        # Create a sample DataFrame for testing
        today = datetime.now()
        data = {
            'Customer schedule': [
                today + timedelta(days=10),
                today + timedelta(days=30), # Should be filtered out (beyond 15 business days)
                today - timedelta(days=5),  # Should be filtered out (in the past)
            ],
            'Tool_Number': ['T001', 'T002', 'T003'],
            'Tool Column': ['ProjectA', 'ProjectB', 'ProjectC'],
            'Responsible User': ['user1', 'user2', 'user3']
        }
        df = pd.DataFrame(data)

        # Apply the transformation (disable Taiwan holidays for consistent test)
        transformer = OutsourcingQcTrans(df, enable_taiwan_holidays=False)
        transformed_df = transformer.get_transformed_data()

        # Assertions
        self.assertEqual(len(transformed_df), 1)
        self.assertIn('Project Start Date', transformed_df.columns)
        
        # Check the 'Project Start Date' calculation using Taiwan business days
        customer_schedule = pd.to_datetime(today + timedelta(days=10))
        taiwan_bday = TaiwanBusinessDay(enable_holiday_checking=False)  # Use simple version for test
        expected_start_date = taiwan_bday.add_business_days(customer_schedule, -15)
        actual_start_date = transformed_df.iloc[0]['Project Start Date']
        self.assertEqual(actual_start_date.date(), expected_start_date.date())

if __name__ == '__main__':
    unittest.main()
