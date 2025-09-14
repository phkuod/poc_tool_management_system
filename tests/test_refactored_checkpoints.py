import unittest
import pandas as pd
from datetime import datetime, timedelta
from outsourcing_qc_check_points import OutsourcingQcCheckPoints
from checkpoint_strategies import QualityAssuranceCheckpoint, CustomerApprovalCheckpoint


class TestRefactoredCheckpoints(unittest.TestCase):

    def setUp(self):
        today = datetime.now()
        self.test_data = {
            'Tool_Number': ['T001', 'T002'],
            'Tool Column': ['ProjectA', 'ProjectB'],
            'Customer schedule': [
                today + timedelta(days=5),
                today + timedelta(days=2)
            ],
            'Project Start Date': [
                today - timedelta(weeks=3),
                today - timedelta(weeks=2)
            ],
            'Responsible User': ['user1@test.com', 'user2@test.com'],
            'Vendor': ['vendor_a', 'vendor_b']
        }
        self.df = pd.DataFrame(self.test_data)

    def test_default_checkpoints_still_work(self):
        """Test that default behavior is unchanged."""
        checker = OutsourcingQcCheckPoints(self.df)
        failures = checker.get_failures()
        
        # Should have the same default checkpoints
        self.assertIn('Package Readiness', failures)
        self.assertIn('Final Report', failures)
        self.assertEqual(len(failures), 2)

    def test_can_add_new_checkpoints(self):
        """Test that we can now add new checkpoints to the legacy class."""
        checker = OutsourcingQcCheckPoints(self.df)
        
        # Initially 2 checkpoints
        self.assertEqual(len(checker.list_checkpoints()), 2)
        
        # Add Quality Assurance checkpoint
        checker.add_checkpoint(QualityAssuranceCheckpoint())
        
        # Should now have 3
        self.assertEqual(len(checker.list_checkpoints()), 3)
        self.assertIn('Quality Assurance', checker.list_checkpoints())
        
        # Get failures should include new checkpoint
        failures = checker.get_failures()
        self.assertIn('Quality Assurance', failures)

    def test_can_remove_checkpoints(self):
        """Test that we can remove checkpoints."""
        checker = OutsourcingQcCheckPoints(self.df)
        
        # Remove Package Readiness
        checker.remove_checkpoint('Package Readiness')
        
        # Should have only Final Report now
        checkpoints = checker.list_checkpoints()
        self.assertEqual(len(checkpoints), 1)
        self.assertNotIn('Package Readiness', checkpoints)
        self.assertIn('Final Report', checkpoints)
        
        # Failures should not include removed checkpoint
        failures = checker.get_failures()
        self.assertNotIn('Package Readiness', failures)
        self.assertIn('Final Report', failures)

    def test_multiple_checkpoints_can_be_added(self):
        """Test adding multiple new checkpoints."""
        checker = OutsourcingQcCheckPoints(self.df)
        
        # Add multiple checkpoints
        checker.add_checkpoint(QualityAssuranceCheckpoint())
        checker.add_checkpoint(CustomerApprovalCheckpoint())
        
        # Should have 4 total (2 default + 2 new)
        self.assertEqual(len(checker.list_checkpoints()), 4)
        
        expected_checkpoints = [
            'Package Readiness', 'Final Report', 
            'Quality Assurance', 'Customer Approval'
        ]
        
        for checkpoint_name in expected_checkpoints:
            self.assertIn(checkpoint_name, checker.list_checkpoints())
        
        # All should appear in failures
        failures = checker.get_failures()
        for checkpoint_name in expected_checkpoints:
            self.assertIn(checkpoint_name, failures)

    def test_vendor_column_functionality_works(self):
        """Test that vendor column functionality works correctly."""
        checker = OutsourcingQcCheckPoints(self.df)
        
        failures = checker.get_failures()
        
        # Should work without errors
        self.assertIsInstance(failures, dict)
        self.assertIn('Package Readiness', failures)
        self.assertIn('Final Report', failures)


if __name__ == '__main__':
    unittest.main()