#!/usr/bin/env python3
"""
Basic test to verify vendor rule functionality.
"""

import pandas as pd
from datetime import datetime, timedelta
from vendor_rules import GenericVendorRule, VendorRuleRegistry

def test_basic_functionality():
    """Test basic vendor rule functionality."""
    print("=== BASIC VENDOR RULE TEST ===")

    # Test with the configured vendors
    vendors = ["vendor_a", "vendor_b", "vendor_c"]

    for vendor in vendors:
        print(f"\n>> Testing {vendor}:")

        try:
            # Create enhanced vendor rule
            rule = GenericVendorRule(vendor)
            print(f"   PASS: Rule created successfully")
            print(f"   Config loaded: {len(rule.config.get('required_patterns', []))} patterns")
            print(f"   Bypass threshold: {rule.config['bypass_rules']['technology_threshold']}")

            # Test DataFrame row (without actual archives)
            today = datetime.now()
            row_data = {
                'Tool_Number': 'T001',
                'Tool Column': 'TestProject',
                'technology': 3
            }
            row = pd.Series(row_data)

            # Execute validation (will fail due to missing archives, but should not crash)
            result = rule.check_final_report_from_dataframe(row)
            print(f"   Validation executed: {'SUCCESS' if result['success'] else 'FAILED (expected - no archives)'}")
            print(f"   Steps completed: {len([s for s in result['steps'].values() if s['status'] != 'PENDING'])}")

        except Exception as e:
            print(f"   FAIL: Error: {e}")

def test_registry():
    """Test vendor registry."""
    print(f"\n=== VENDOR REGISTRY TEST ===")

    # Test listing vendors
    available = VendorRuleRegistry.list_vendors()
    print(f"Available vendors: {available}")

    # Test getting rules
    for vendor in available[:2]:  # Test first 2
        rule = VendorRuleRegistry.get_rule(vendor)
        if rule:
            print(f"PASS {vendor}: Rule retrieved successfully")
        else:
            print(f"FAIL {vendor}: Failed to retrieve rule")

def test_configuration_validation():
    """Test configuration validation."""
    print(f"\n=== CONFIGURATION VALIDATION TEST ===")

    from vendor_config_loader import vendor_config_loader

    vendors = vendor_config_loader.list_vendors()
    print(f"Configured vendors: {vendors}")

    for vendor in vendors:
        is_valid, message = vendor_config_loader.validate_vendor_config(vendor)
        status = "PASS" if is_valid else "FAIL"
        print(f"{status} {vendor}: {message}")

if __name__ == "__main__":
    test_configuration_validation()
    test_basic_functionality()
    test_registry()
    print(f"\n=== TEST COMPLETE ===")