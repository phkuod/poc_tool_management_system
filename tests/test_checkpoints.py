import unittest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from outsourcing_qc_check_points import OutsourcingQcCheckPoints
from pathlib import Path

class TestOutsourcingQcCheckPoints(unittest.TestCase):

    def setUp(self):
        # Create a sample DataFrame for testing
        self.today = datetime.now()
        data = {
            'Tool_Number': ['T001', 'T002'],
            'Tool Column': ['ProjectA', 'ProjectB'],
            'Customer schedule': [
                self.today + timedelta(days=5),
                self.today + timedelta(days=15)
            ],
            'Responsible User': ['user1', 'user2'],
            'Project Start Date': [
                self.today - timedelta(days=5),
                self.today - timedelta(days=1)
            ]
        }
        self.df = pd.DataFrame(data)

    @patch('pathlib.Path.glob')
    def test_get_failures(self, mock_glob):
        # Mock the filesystem interaction
        # T001 should fail package readiness, T002 should not
        # T001 should fail final report, T002 should not
        def glob_side_effect(pattern):
            if 'T001' in pattern and "Final_Report" not in pattern:
                return []  # No package for T001
            if 'T002' in pattern and "Final_Report" not in pattern:
                return [MagicMock()] # Package exists for T002
            if 'T001' in pattern and "Final_Report" in pattern:
                return [] # No report for T001
            if 'T002' in pattern and "Final_Report" in pattern:
                return [MagicMock()] # Report exists for T002
            return []
        
        mock_glob.side_effect = glob_side_effect

        # Run the checker
        checker = OutsourcingQcCheckPoints(self.df)
        failures = checker.get_failures()

        # Assertions
        self.assertEqual(len(failures['Package Readiness']), 1)
        self.assertEqual(failures['Package Readiness'][0]['Tool_Number'], 'T001')
        self.assertEqual(len(failures['Final Report']), 1)
        self.assertEqual(failures['Final Report'][0]['Tool_Number'], 'T001')


if __name__ == '__main__':
    unittest.main()
