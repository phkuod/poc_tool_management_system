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
            ],
            'Vendor': ['vendor_a', 'vendor_b']
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

    def test_vendor_column_usage(self):
        """Test that vendor column from each row is used for final report checking"""
        today = datetime.now()
        data = {
            'Tool_Number': ['T001', 'T002'],
            'Tool Column': ['ProjectA', 'ProjectB'],
            'Customer schedule': [
                today + timedelta(days=3),  # Both within 7 days for final report check
                today + timedelta(days=3)
            ],
            'Project Start Date': [
                today - timedelta(weeks=3),
                today - timedelta(weeks=3)
            ],
            'Responsible User': ['user1@test.com', 'user2@test.com'],
            'Vendor': ['vendor_a', 'vendor_b']  # Different vendors per row
        }
        df = pd.DataFrame(data)
        
        with patch('pathlib.Path.glob') as mock_glob:
            # Mock different vendor file patterns
            def glob_side_effect(pattern):
                if 'vendor_a' in str(pattern) or 'Report_T001_' in pattern:
                    return []  # Vendor A Excel files not found
                if 'vendor_b' in str(pattern) or 'VendorB' in str(pattern):
                    return []  # Vendor B files not found
                return []
            
            mock_glob.side_effect = glob_side_effect
            
            checker = OutsourcingQcCheckPoints(df)
            failures = checker.get_failures()
            
            # Both should fail but with different vendor-specific reasons
            self.assertEqual(len(failures['Final Report']), 2)
            self.assertIn('Vendor', failures['Final Report'][0])
            self.assertIn('Vendor', failures['Final Report'][1])

    def test_unsupported_vendor_fails_fast(self):
        """Test that unsupported vendors fail immediately without file checking"""
        today = datetime.now()
        data = {
            'Tool_Number': ['T001'],
            'Tool Column': ['ProjectA'],
            'Customer schedule': [today + timedelta(days=3)],
            'Project Start Date': [today - timedelta(weeks=3)],
            'Responsible User': ['user1@test.com'],
            'Vendor': ['unsupported_vendor']  # This vendor doesn't exist in VendorRuleRegistry
        }
        df = pd.DataFrame(data)
        
        checker = OutsourcingQcCheckPoints(df)
        failures = checker.get_failures()
        
        # Should fail with unsupported vendor message
        self.assertEqual(len(failures['Final Report']), 1)
        failure = failures['Final Report'][0]
        self.assertEqual(failure['Tool_Number'], 'T001')
        self.assertEqual(failure['Vendor'], 'unsupported_vendor')
        self.assertIn('Unsupported vendor', failure['Fail Reason'])


if __name__ == '__main__':
    unittest.main()
