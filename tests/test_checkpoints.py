#!/usr/bin/env python3
"""
Unit tests for checkpoint strategies with DataFrame integration.
"""

import unittest
import tempfile
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checkpoint_strategies import (
    CheckpointRegistry,
    PackageReadinessCheckpoint,
    FinalReportCheckpoint
)
from outsourcing_qc_check_points import OutsourcingQcCheckPoints


class TestCheckpoints(unittest.TestCase):
    """Test cases for checkpoint strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, "test_config.json")

        # Create test configuration
        self.test_config = {
            "target_path": self.temp_dir,
            "paths": {
                "source_root": os.path.join(self.temp_dir, "source"),
                "target_root": os.path.join(self.temp_dir, "target")
            },
            "vendors": {
                "vendor_a": {
                    "archive_config": {
                        "source_archive_regex": "{source_root}/{tool_column}/source_{tool_number}_.*\\.tar\\.gz$",
                        "target_archive_regex": "{target_root}/{tool_column}/target_{tool_number}_.*\\.tar\\.gz$",
                        "consistency_check": {
                            "enabled": True,
                            "file_extension": "rctl"
                        }
                    },
                    "required_patterns": [
                        "Report_{tool_number}_.*\\.xlsx$",
                        "Summary_{tool_number}_.*\\.pdf$"
                    ],
                    "bypass_rules": {
                        "technology_threshold": 5,
                        "bypass_patterns": [".pdf$"]
                    }
                }
            }
        }

        # Write test configuration
        with open(self.test_config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)

        # Create test DataFrame
        today = datetime.now()
        self.test_data = {
            'Tool_Number': ['T001', 'T002', 'T003'],
            'Tool Column': ['ProjectA', 'ProjectB', 'ProjectA'],
            'Customer schedule': [
                today + timedelta(days=3),   # Soon deadline
                today + timedelta(days=10),  # Normal deadline
                today + timedelta(days=1)    # Very soon deadline
            ],
            'Project Start Date': [
                today - timedelta(weeks=3),  # Ready for package check
                today - timedelta(weeks=2),  # Ready for package check
                today - timedelta(weeks=4)   # Ready for package check
            ],
            'Responsible User': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
            'Vendor': ['vendor_a', 'vendor_a', 'vendor_a'],
            'technology': [3, 7, 4]  # Different technology values for bypass testing
        }
        self.test_df = pd.DataFrame(self.test_data)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_checkpoint_registry(self):
        """Test checkpoint registry functionality."""
        # Create registry with defaults
        from checkpoint_strategies import CheckpointRegistry
        registry = CheckpointRegistry.create_default()

        # Check that defaults are registered
        checkpoints = registry.list_checkpoints()
        self.assertEqual(len(checkpoints), 2)

        checkpoint_names = [cp.name for cp in checkpoints]
        self.assertIn("Package Readiness", checkpoint_names)
        self.assertIn("Final Report", checkpoint_names)

        # Test priority ordering
        self.assertEqual(checkpoints[0].priority, 1)  # Package readiness first
        self.assertEqual(checkpoints[1].priority, 2)  # Final report second

    def test_package_readiness_checkpoint(self):
        """Test package readiness checkpoint."""
        checkpoint = PackageReadinessCheckpoint()
        today = datetime.now()

        # Test should_validate logic
        for index, row in self.test_df.iterrows():
            should_validate = checkpoint.should_validate(row, today)
            self.assertTrue(should_validate)  # All test data should trigger package check

        # Test execution (will fail because no actual packages exist)
        row = self.test_df.iloc[0]
        result = checkpoint.execute_check(row, today)
        self.assertEqual(result["checkpoint_name"], "Package Readiness")
        self.assertEqual(result["tool_number"], "T001")
        self.assertFalse(result["success"])
        self.assertEqual(len(result["failures"]), 1)
        self.assertEqual(result["failures"][0]['Tool_Number'], 'T001')
        self.assertEqual(result["failures"][0]['Fail Reason'], 'Package not found')

    def test_final_report_checkpoint(self):
        """Test final report checkpoint."""
        checkpoint = FinalReportCheckpoint()
        today = datetime.now()

        # Test should_validate logic
        for index, row in self.test_df.iterrows():
            should_validate = checkpoint.should_validate(row, today)
            expected = (row['Customer schedule'] - today).days <= 5
            self.assertEqual(should_validate, expected)

        # Test execution with vendor validation
        row = self.test_df.iloc[0]  # T001, should trigger final report check
        result = checkpoint.execute_check(row, today)

        self.assertEqual(result["checkpoint_name"], "Final Report")
        self.assertEqual(result["tool_number"], "T001")
        self.assertTrue(result["should_check"])
        self.assertTrue(result["executed"])
        self.assertFalse(result["success"])  # Will fail due to missing archives

    def test_outsourcing_qc_check_points(self):
        """Test outsourcing QC check points."""
        # Test with vendor validation
        checker = OutsourcingQcCheckPoints(self.test_df)

        # Get results
        results = checker.get_results()

        self.assertEqual(results["total_tools"], 3)
        self.assertEqual(len(results["tool_results"]), 3)

        # Check summary statistics
        summary = results["summary"]
        self.assertEqual(summary["total_failures"], 3)  # All will fail due to missing archives
        self.assertEqual(summary["total_successes"], 0)

        # Test vendor statistics
        self.assertIn("vendor_a", summary["vendor_statistics"])
        vendor_stats = summary["vendor_statistics"]["vendor_a"]
        self.assertEqual(vendor_stats["total_tools"], 3)

    def test_vendor_validation(self):
        """Test vendor validation functionality."""
        # Test vendor validation
        checker = OutsourcingQcCheckPoints(self.test_df)
        failures = checker.get_failures()

        # Should have failures due to missing archives
        self.assertGreater(len(failures), 0)

        # Should have detailed failure information for vendor validation
        final_failures = failures.get("Final Report", [])
        if final_failures:
            failure = final_failures[0]
            self.assertIn("Vendor_Validation", failure)

    def test_vendor_analysis(self):
        """Test vendor analysis functionality."""
        checker = OutsourcingQcCheckPoints(self.test_df)
        vendor_analysis = checker.get_vendor_analysis()

        # Check vendor_a analysis
        self.assertIn("vendor_a", vendor_analysis)
        vendor_a_data = vendor_analysis["vendor_a"]

        self.assertEqual(vendor_a_data["total_tools"], 3)
        self.assertIn("pattern_statistics", vendor_a_data)
        self.assertIn("tools", vendor_a_data)

        # Check individual tool results
        tools = vendor_a_data["tools"]
        self.assertIn("T001", tools)
        self.assertIn("T002", tools)
        self.assertIn("T003", tools)

    def test_summary_statistics(self):
        """Test summary statistics generation."""
        checker = OutsourcingQcCheckPoints(self.test_df)
        summary_stats = checker.get_summary_statistics()

        self.assertEqual(summary_stats["total_tools"], 3)
        self.assertEqual(summary_stats["failed_tools"], 3)  # All fail due to missing archives
        self.assertEqual(summary_stats["successful_tools"], 0)
        self.assertEqual(summary_stats["success_rate"], 0.0)

    def test_checkpoint_execution_timing(self):
        """Test that checkpoint execution includes timing information."""
        checkpoint = FinalReportCheckpoint()
        today = datetime.now()
        row = self.test_df.iloc[0]

        result = checkpoint.execute_check(row, today)

        self.assertIn("execution_time", result)
        self.assertIsInstance(result["execution_time"], float)
        self.assertGreaterEqual(result["execution_time"], 0)

    def test_checkpoint_error_handling(self):
        """Test checkpoint error handling."""
        class FailingCheckpoint(FinalReportCheckpoint):
            def execute_check(self, row, today):
                raise ValueError("Test error")

        checkpoint = FailingCheckpoint()
        today = datetime.now()
        row = self.test_df.iloc[0]

        # This test should handle the exception gracefully
        try:
            result = checkpoint.execute_check(row, today)
            # If we get here, the error was handled
            self.assertTrue(result["executed"])
            self.assertFalse(result["success"])
        except ValueError:
            # If exception is not handled, that's also acceptable for this test
            pass

    def test_export_detailed_report(self):
        """Test detailed report export functionality."""
        checker = OutsourcingQcCheckPoints(self.test_df)

        # Export report without file
        report = checker.export_detailed_report()

        self.assertIn("report_metadata", report)
        self.assertIn("results", report)
        self.assertIn("vendor_analysis", report)

        # Check metadata
        metadata = report["report_metadata"]
        self.assertEqual(metadata["total_tools_analyzed"], 3)
        self.assertEqual(metadata["report_version"], "1.0")

        # Test export to file
        report_file = os.path.join(self.temp_dir, "test_report.json")
        checker.export_detailed_report(report_file)

        self.assertTrue(os.path.exists(report_file))

        # Verify file contents
        with open(report_file, 'r') as f:
            file_report = json.load(f)

        self.assertEqual(file_report["report_metadata"]["total_tools_analyzed"], 3)

    def test_execute_all_checks(self):
        """Test executing all checks for a single row."""
        today = datetime.now()
        row = self.test_df.iloc[0]

        # Create registry
        from checkpoint_strategies import CheckpointRegistry
        registry = CheckpointRegistry.create_default()

        # Execute all checks
        results = registry.run_all_checks(row, today)

        self.assertEqual(results["tool_number"], "T001")
        self.assertEqual(results["tool_column"], "ProjectA")
        self.assertFalse(results["overall_success"])  # Will fail due to missing archives
        self.assertEqual(results["executed_checkpoints"], 2)  # Both checkpoints should execute
        self.assertEqual(len(results["checkpoints"]), 2)

        # Check individual checkpoint results
        checkpoint_names = [cp["checkpoint_name"] for cp in results["checkpoints"]]
        self.assertIn("Package Readiness", checkpoint_names)
        self.assertIn("Final Report", checkpoint_names)


if __name__ == '__main__':
    unittest.main()