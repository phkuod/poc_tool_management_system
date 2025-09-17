#!/usr/bin/env python3
"""
Comprehensive demo script for enhanced vendor rules with DataFrame integration.
Shows the complete 5-step validation process with detailed reporting.
"""

import tempfile
import tarfile
import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from vendor_rules import VendorRuleRegistry, GenericVendorRule
from outsourcing_qc_check_points import OutsourcingQcCheckPoints
from vendor_config_loader import VendorConfigLoader


def create_demo_environment():
    """Create a complete demo environment with configuration and test data."""
    temp_dir = tempfile.mkdtemp()
    print(f"Creating demo environment in: {temp_dir}")

    # Create configuration
    config = {
        "target_path": temp_dir,
        "paths": {
            "source_root": os.path.join(temp_dir, "source_deliveries"),
            "target_root": os.path.join(temp_dir, "target_archives")
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
                    "Summary_{tool_number}_.*\\.pdf$",
                    "Config_{tool_number}_.*\\.aaa$"
                ],
                "bypass_rules": {
                    "technology_threshold": 5,
                    "bypass_patterns": [".aaa$"]
                }
            },
            "vendor_b": {
                "archive_config": {
                    "source_archive_regex": "{source_root}/packages/pkg_{tool_number}_v\\d+\\.tar\\.gz$",
                    "target_archive_regex": "{target_root}/deliveries/{tool_column}/final_{tool_number}_.*\\.tar\\.gz$",
                    "consistency_check": {
                        "enabled": True,
                        "file_extension": "config"
                    }
                },
                "required_patterns": [
                    "Final_{tool_number}_.*\\.pdf$",
                    "Specs_{tool_number}_.*\\.docx$"
                ],
                "bypass_rules": {
                    "technology_threshold": 3,
                    "bypass_patterns": [".docx$"]
                }
            }
        }
    }

    # Write configuration
    config_path = os.path.join(temp_dir, "demo_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Create directory structure
    os.makedirs(os.path.join(temp_dir, "source_deliveries", "ProjectA"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "source_deliveries", "ProjectB"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "source_deliveries", "packages"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "target_archives", "ProjectA"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "target_archives", "ProjectB"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "target_archives", "deliveries", "ProjectB"), exist_ok=True)

    return temp_dir, config_path


def create_demo_archives(temp_dir):
    """Create demo tar.gz archives with various scenarios."""
    print("Creating demo archives...")

    # Scenario 1: vendor_a with successful validation (low technology)
    source_files_1 = {"config.rctl": "tool T001 configuration v1.0"}
    target_files_1 = {
        "config.rctl": "tool T001 configuration v1.0",  # Same content
        "Report_T001_final.xlsx": b"Excel report content for T001",
        "Summary_T001_overview.pdf": b"PDF summary content for T001",
        "Config_T001_settings.aaa": b"AAA config content for T001"
    }

    create_archive(
        os.path.join(temp_dir, "source_deliveries", "ProjectA", "source_T001_v1.tar.gz"),
        source_files_1
    )
    create_archive(
        os.path.join(temp_dir, "target_archives", "ProjectA", "target_T001_release.tar.gz"),
        target_files_1
    )

    # Scenario 2: vendor_a with bypass (high technology)
    source_files_2 = {"config.rctl": "tool T002 configuration v2.0"}
    target_files_2 = {
        "config.rctl": "tool T002 configuration v2.0",
        "Report_T002_final.xlsx": b"Excel report content for T002",
        "Summary_T002_overview.pdf": b"PDF summary content for T002"
        # Missing .aaa file, but should be bypassed due to high technology
    }

    create_archive(
        os.path.join(temp_dir, "source_deliveries", "ProjectA", "source_T002_v1.tar.gz"),
        source_files_2
    )
    create_archive(
        os.path.join(temp_dir, "target_archives", "ProjectA", "target_T002_release.tar.gz"),
        target_files_2
    )

    # Scenario 3: vendor_a with consistency failure
    source_files_3 = {"config.rctl": "tool T003 configuration v1.0"}
    target_files_3 = {
        "config.rctl": "tool T003 configuration v2.0",  # Different content!
        "Report_T003_final.xlsx": b"Excel report content for T003",
        "Summary_T003_overview.pdf": b"PDF summary content for T003",
        "Config_T003_settings.aaa": b"AAA config content for T003"
    }

    create_archive(
        os.path.join(temp_dir, "source_deliveries", "ProjectA", "source_T003_v1.tar.gz"),
        source_files_3
    )
    create_archive(
        os.path.join(temp_dir, "target_archives", "ProjectA", "target_T003_release.tar.gz"),
        target_files_3
    )

    # Scenario 4: vendor_b with successful validation
    source_files_4 = {"settings.config": "vendor B configuration"}
    target_files_4 = {
        "settings.config": "vendor B configuration",
        "Final_T004_report.pdf": b"Final report for T004",
        "Specs_T004_documentation.docx": b"Specifications document for T004"
    }

    create_archive(
        os.path.join(temp_dir, "source_deliveries", "packages", "pkg_T004_v3.tar.gz"),
        source_files_4
    )
    create_archive(
        os.path.join(temp_dir, "target_archives", "deliveries", "ProjectB", "final_T004_delivery.tar.gz"),
        target_files_4
    )

    print("Demo archives created successfully!")


def create_archive(archive_path, files):
    """Create a tar.gz archive with specified files."""
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


def demo_enhanced_vendor_validation():
    """Demonstrate enhanced vendor validation with various scenarios."""
    print("=== ENHANCED VENDOR VALIDATION DEMO ===")
    print()

    # Create demo environment
    temp_dir, config_path = create_demo_environment()
    create_demo_archives(temp_dir)

    try:
        # Initialize config loader with demo config
        config_loader = VendorConfigLoader(config_path)

        # Create test DataFrame
        today = datetime.now()
        test_data = {
            'Tool_Number': ['T001', 'T002', 'T003', 'T004'],
            'Tool Column': ['ProjectA', 'ProjectA', 'ProjectA', 'ProjectB'],
            'Customer schedule': [
                today + timedelta(days=3),
                today + timedelta(days=5),
                today + timedelta(days=2),
                today + timedelta(days=4)
            ],
            'Project Start Date': [
                today - timedelta(weeks=3),
                today - timedelta(weeks=3),
                today - timedelta(weeks=3),
                today - timedelta(weeks=3)
            ],
            'Responsible User': ['alice@company.com', 'bob@company.com', 'charlie@company.com', 'diana@company.com'],
            'Vendor': ['vendor_a', 'vendor_a', 'vendor_a', 'vendor_b'],
            'technology': [3, 7, 3, 5]  # T002 has high tech for bypass testing
        }
        df = pd.DataFrame(test_data)

        print("Test DataFrame:")
        print(df[['Tool_Number', 'Tool Column', 'Vendor', 'technology']].to_string(index=False))
        print()

        # Demo individual vendor rule validation
        print("=== INDIVIDUAL VENDOR RULE VALIDATION ===")
        print()

        for index, row in df.iterrows():
            tool_number = row['Tool_Number']
            vendor = row['Vendor']
            technology = row['technology']

            print(f">> Tool {tool_number} (Vendor: {vendor}, Technology: {technology}):")

            # Get enhanced vendor rule with demo config
            from enhanced_vendor_rules import GenericVendorRule
            try:
                rule = GenericVendorRule(vendor, config_loader)
            except ValueError:
                rule = None

            if rule:

                # Execute validation
                result = rule.check_final_report_from_dataframe(row)

                # Display results
                print(f"   Success: {'YES' if result['success'] else 'NO'}")
                print(f"   Archives Found: {bool(result['paths']['source_archive'] and result['paths']['target_archive'])}")

                # Show validation steps
                for step_name, step_result in result['steps'].items():
                    status = step_result['status']
                    print(f"   {step_name.title()}: {status}")

                # Show statistics
                stats = result['statistics']
                print(f"   Patterns: {stats['pass_count']}/{stats['checked_patterns']} passed, {stats['bypassed_count']} bypassed")
                print(f"   Passing Rate: {stats['passing_rate']:.1f}%")

                # Show pattern details for interesting cases
                if not result['success'] or stats['bypassed_count'] > 0:
                    print("   Pattern Details:")
                    for pattern_result in result['pattern_results']:
                        status = pattern_result['status']
                        pattern = pattern_result['pattern']
                        if status == "FAIL":
                            print(f"     ❌ {pattern} - {status}")
                        elif status == "BYPASSED":
                            reason = pattern_result.get('bypass_reason', '')
                            print(f"     ⏭️  {pattern} - {status} ({reason})")
                        else:
                            file_count = pattern_result.get('file_count', 0)
                            print(f"     ✅ {pattern} - {status} ({file_count} files)")

            else:
                print(f"   No enhanced rule found for vendor: {vendor}")

            print()

        # Demo comprehensive checkpoint validation
        print("=== COMPREHENSIVE CHECKPOINT VALIDATION ===")
        print()

        enhanced_checker = OutsourcingQcCheckPoints(df, use_enhanced=True)
        # Note: For demo purposes, the enhanced checker would need custom configuration injection

        # Get enhanced results
        enhanced_results = enhanced_checker.get_enhanced_results()

        print("Overall Results:")
        summary = enhanced_results['summary']
        print(f"  Total Tools: {enhanced_results['total_tools']}")
        print(f"  Successful: {summary['total_successes']}")
        print(f"  Failed: {summary['total_failures']}")
        print(f"  Enhanced Validation Used: {summary['tools_with_enhanced_validation']}")
        print(f"  Legacy Fallback Used: {summary['tools_with_legacy_fallback']}")
        print()

        # Vendor analysis
        print("=== VENDOR ANALYSIS ===")
        print()

        vendor_analysis = enhanced_checker.get_vendor_analysis()

        for vendor, vendor_data in vendor_analysis.items():
            print(f">> Vendor: {vendor}")
            print(f"   Total Tools: {vendor_data['total_tools']}")
            print(f"   Enhanced Validation Available: {vendor_data['enhanced_validation_available']}")

            if vendor_data['enhanced_validation_available']:
                pattern_stats = vendor_data['pattern_statistics']
                print(f"   Pattern Statistics:")
                print(f"     Total Checked: {pattern_stats['total_patterns_checked']}")
                print(f"     Passed: {pattern_stats['total_patterns_passed']}")
                print(f"     Failed: {pattern_stats['total_patterns_failed']}")
                print(f"     Bypassed: {pattern_stats['total_patterns_bypassed']}")
                print(f"     Average Pass Rate: {pattern_stats['average_passing_rate']:.1f}%")

                # Show common failures
                if vendor_data['common_failures']:
                    print(f"   Common Failure Patterns:")
                    for pattern, count in vendor_data['common_failures'].items():
                        print(f"     {pattern}: {count} failures")

            print()

        # Summary statistics
        print("=== SUMMARY STATISTICS ===")
        print()

        summary_stats = enhanced_checker.get_summary_statistics()
        print(f"Validation Type: {summary_stats['validation_type']}")
        print(f"Total Tools: {summary_stats['total_tools']}")
        print(f"Success Rate: {summary_stats['success_rate']:.1f}%")
        print(f"Enhanced Validation Usage: {summary_stats['enhanced_validation_usage']} tools")
        print(f"Vendor Count: {summary_stats['vendor_count']}")
        print()

        print("=== DEMO SCENARIOS EXPLAINED ===")
        print()
        print("T001 (vendor_a, tech=3): ✅ All patterns found, low tech = no bypass")
        print("T002 (vendor_a, tech=7): ✅ High tech bypasses .aaa pattern, others found")
        print("T003 (vendor_a, tech=3): ❌ Consistency check fails (different .rctl content)")
        print("T004 (vendor_b, tech=5): ✅ All patterns found (vendor_b has different rules)")
        print()

    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"Cleaned up demo environment: {temp_dir}")


def demo_configuration_flexibility():
    """Demonstrate configuration flexibility and vendor extensibility."""
    print("=== CONFIGURATION FLEXIBILITY DEMO ===")
    print()

    temp_dir, config_path = create_demo_environment()

    try:
        config_loader = VendorConfigLoader(config_path)

        # Show available vendors
        vendors = config_loader.list_vendors()
        print(f"Configured Vendors: {vendors}")
        print()

        # Show vendor-specific configurations
        for vendor in vendors:
            print(f">> Vendor: {vendor}")
            vendor_config = config_loader.get_vendor_config(vendor)

            archive_config = vendor_config['archive_config']
            print(f"   Source Pattern: {archive_config['source_archive_regex']}")
            print(f"   Target Pattern: {archive_config['target_archive_regex']}")
            print(f"   Consistency Extension: {archive_config['consistency_check']['file_extension']}")

            print(f"   Required Patterns:")
            for pattern in vendor_config['required_patterns']:
                print(f"     - {pattern}")

            bypass_rules = vendor_config['bypass_rules']
            print(f"   Bypass Rules:")
            print(f"     Technology Threshold: {bypass_rules['technology_threshold']}")
            print(f"     Bypass Patterns: {bypass_rules['bypass_patterns']}")

            # Validate configuration
            is_valid, message = config_loader.validate_vendor_config(vendor)
            print(f"   Configuration Valid: {'YES' if is_valid else 'NO'}")
            if not is_valid:
                print(f"   Validation Error: {message}")

            print()

    finally:
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Run comprehensive enhanced vendor rules demonstration."""
    print("Enhanced Vendor Rules - Comprehensive Demo")
    print("=" * 60)
    print()

    demo_configuration_flexibility()
    print()

    demo_enhanced_vendor_validation()
    print()

    print("Demo complete! Key features demonstrated:")
    print("- Configurable regex-based archive discovery")
    print("- 5-step validation process with detailed reporting")
    print("- Technology-based bypass rules")
    print("- File consistency checking with configurable extensions")
    print("- Pattern validation with size checking")
    print("- Comprehensive statistical reporting")
    print("- DataFrame integration for batch processing")
    print("- Vendor analysis and failure tracking")
    print("=" * 60)


if __name__ == "__main__":
    main()