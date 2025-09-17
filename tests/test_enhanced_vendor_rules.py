#!/usr/bin/env python3
"""
Unit tests for enhanced vendor rules with DataFrame integration.
"""

import unittest
import tempfile
import tarfile
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vendor_rules import (
    EnhancedVendorRuleStrategy,
    EnhancedVendorRuleRegistry,
    GenericEnhancedVendorRule
)
from vendor_config_loader import VendorConfigLoader


class TestEnhancedVendorRules(unittest.TestCase):
    """Test cases for enhanced vendor rules."""

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
                "test_vendor": {
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
                        "Summary_{tool_number}_.*\\.pdf$",
                        "Config_{tool_number}_.*\\.aaa$"
                    ],
                    "bypass_rules": {
                        "technology_threshold": 5,
                        "bypass_patterns": [".aaa$"]
                    }
                }
            }
        }

        # Write test configuration
        with open(self.test_config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)

        # Create directory structure
        os.makedirs(os.path.join(self.temp_dir, "source", "ProjectA"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "target", "ProjectA"), exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

        # Clear vendor registry cache
        EnhancedVendorRuleRegistry.clear_cache()

    def _create_test_archive(self, archive_path: str, files: dict):
        """Create a test tar.gz archive with specified files."""
        with tempfile.TemporaryDirectory() as temp_content_dir:
            # Create files in temporary directory
            for file_path, content in files.items():
                full_path = Path(temp_content_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                if isinstance(content, str):
                    full_path.write_text(content, encoding='utf-8')
                else:
                    full_path.write_bytes(content)

            # Create tar.gz archive
            with tarfile.open(archive_path, 'w:gz') as tar:
                for file_path in files.keys():
                    full_path = Path(temp_content_dir) / file_path
                    tar.add(full_path, arcname=file_path)

    def test_vendor_config_loader(self):
        """Test vendor configuration loading."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Test loading configuration
        config = config_loader.load_config()
        self.assertIn("vendors", config)
        self.assertIn("test_vendor", config["vendors"])

        # Test vendor-specific config
        vendor_config = config_loader.get_vendor_config("test_vendor")
        self.assertIsNotNone(vendor_config)
        self.assertIn("archive_config", vendor_config)

        # Test validation
        is_valid, message = config_loader.validate_vendor_config("test_vendor")
        self.assertTrue(is_valid, f"Validation failed: {message}")

    def test_enhanced_vendor_rule_creation(self):
        """Test creation of enhanced vendor rule."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        self.assertEqual(rule.vendor_key, "test_vendor")
        self.assertIsNotNone(rule.config)

    def test_archive_discovery_regex(self):
        """Test regex-based archive discovery."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        # Create archives with test content
        source_files = {"config.rctl": "source config content"}
        target_files = {
            "config.rctl": "source config content",  # Same content for consistency
            "Report_T001_final.xlsx": b"xlsx content",
            "Summary_T001_report.pdf": b"pdf content"
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Test archive discovery
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3
        }
        row = pd.Series(row_data)

        # Find archives
        source_found, target_found = rule._find_archives_from_dataframe(row)

        self.assertIsNotNone(source_found)
        self.assertIsNotNone(target_found)
        self.assertEqual(source_found.name, "source_T001_v1.tar.gz")
        self.assertEqual(target_found.name, "target_T001_final.tar.gz")

    def test_dataframe_validation_success(self):
        """Test successful DataFrame-based validation."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives with all required files
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        source_files = {"config.rctl": "test config content"}
        target_files = {
            "config.rctl": "test config content",  # Same for consistency
            "Report_T001_final.xlsx": b"xlsx content",
            "Summary_T001_report.pdf": b"pdf content",
            "Config_T001_settings.aaa": b"aaa content"
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3  # Below threshold, all patterns checked
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["statistics"]["pass_count"], 3)
        self.assertEqual(result["statistics"]["fail_count"], 0)
        self.assertEqual(result["statistics"]["bypassed_count"], 0)
        self.assertEqual(result["statistics"]["passing_rate"], 100.0)

    def test_dataframe_validation_with_bypass(self):
        """Test DataFrame validation with technology-based bypass."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        source_files = {"config.rctl": "test config content"}
        target_files = {
            "config.rctl": "test config content",
            "Report_T001_final.xlsx": b"xlsx content",
            "Summary_T001_report.pdf": b"pdf content"
            # Missing .aaa file, but should be bypassed
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row with high technology value
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 7  # Above threshold, .aaa pattern bypassed
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["statistics"]["pass_count"], 2)  # xlsx, pdf
        self.assertEqual(result["statistics"]["fail_count"], 0)
        self.assertEqual(result["statistics"]["bypassed_count"], 1)  # .aaa bypassed
        self.assertEqual(result["statistics"]["passing_rate"], 100.0)

    def test_dataframe_validation_failure(self):
        """Test DataFrame validation with missing required files."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives with missing files
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        source_files = {"config.rctl": "test config content"}
        target_files = {
            "config.rctl": "test config content",
            "Report_T001_final.xlsx": b"xlsx content"
            # Missing Summary pdf and Config aaa files
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3  # Below threshold, all patterns checked
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results
        self.assertFalse(result["success"])
        self.assertEqual(result["statistics"]["pass_count"], 1)  # Only xlsx
        self.assertEqual(result["statistics"]["fail_count"], 2)  # Missing pdf, aaa
        self.assertEqual(result["statistics"]["bypassed_count"], 0)
        self.assertAlmostEqual(result["statistics"]["passing_rate"], 33.33, places=1)  # 1/3 * 100

    def test_consistency_check_failure(self):
        """Test consistency check failure between source and target."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives with different .rctl content
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        source_files = {"config.rctl": "source config content"}
        target_files = {
            "config.rctl": "different config content",  # Different content
            "Report_T001_final.xlsx": b"xlsx content",
            "Summary_T001_report.pdf": b"pdf content"
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results - should fail due to consistency check
        self.assertFalse(result["success"])
        self.assertEqual(result["steps"]["file_consistency"]["status"], "FAIL")

    def test_enhanced_vendor_registry(self):
        """Test enhanced vendor registry functionality."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Register test vendor manually for this test
        test_rule = GenericEnhancedVendorRule("test_vendor", config_loader)
        EnhancedVendorRuleRegistry.register_enhanced_rule("test_vendor", test_rule)

        # Test registry functionality
        vendors = EnhancedVendorRuleRegistry.list_enhanced_vendors()
        self.assertIn("test_vendor", vendors)

        # Test getting enhanced rule
        rule = EnhancedVendorRuleRegistry.get_enhanced_rule("test_vendor")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.vendor_key, "test_vendor")

        # Test non-existent vendor
        no_rule = EnhancedVendorRuleRegistry.get_enhanced_rule("nonexistent_vendor")
        self.assertIsNone(no_rule)

    def test_missing_archives(self):
        """Test behavior when archives are missing."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row (no archives created)
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results - should fail due to missing archives
        self.assertFalse(result["success"])
        self.assertEqual(result["steps"]["archive_discovery"]["status"], "FAIL")

    def test_empty_files_rejected(self):
        """Test that empty files (size = 0) are rejected."""
        config_loader = VendorConfigLoader(self.test_config_path)

        # Create test archives with empty files
        source_archive_path = os.path.join(self.temp_dir, "source", "ProjectA", "source_T001_v1.tar.gz")
        target_archive_path = os.path.join(self.temp_dir, "target", "ProjectA", "target_T001_final.tar.gz")

        source_files = {"config.rctl": "test config content"}
        target_files = {
            "config.rctl": "test config content",
            "Report_T001_final.xlsx": "",  # Empty file
            "Summary_T001_report.pdf": b"pdf content"
        }

        self._create_test_archive(source_archive_path, source_files)
        self._create_test_archive(target_archive_path, target_files)

        # Create enhanced vendor rule
        rule = GenericEnhancedVendorRule("test_vendor", config_loader)

        # Create test DataFrame row
        row_data = {
            'Tool_Number': 'T001',
            'Tool Column': 'ProjectA',
            'technology': 3
        }
        row = pd.Series(row_data)

        # Execute validation
        result = rule.check_final_report_from_dataframe(row)

        # Verify results - should fail because xlsx file is empty
        self.assertFalse(result["success"])
        self.assertEqual(result["statistics"]["fail_count"], 2)  # xlsx (empty) and aaa (missing)


if __name__ == '__main__':
    unittest.main()