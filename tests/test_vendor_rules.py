import unittest
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from vendor_rules import VendorRuleRegistry, VendorARule, VendorBRule
from outsourcing_qc_check_points import OutsourcingQcCheckPoints


class TestVendorRules(unittest.TestCase):

    def test_default_vendor_rule(self):
        rule = VendorRuleRegistry.get_rule('default')
        self.assertEqual(rule.get_fail_reason(), "Final report not found")

    def test_vendor_a_rule(self):
        rule = VendorRuleRegistry.get_rule('vendor_a')
        self.assertEqual(rule.get_fail_reason(), "Vendor A report not found (Excel format required)")

    def test_vendor_b_rule(self):
        rule = VendorRuleRegistry.get_rule('vendor_b')
        self.assertEqual(rule.get_fail_reason(), "Vendor B final report not found in VendorB subfolder")

    def test_registry_unknown_vendor_returns_default(self):
        rule = VendorRuleRegistry.get_rule('unknown_vendor')
        self.assertEqual(rule.get_fail_reason(), "Final report not found")

    def test_registry_register_new_rule(self):
        class CustomRule(VendorARule):
            def get_fail_reason(self):
                return "Custom vendor rule failed"
        
        VendorRuleRegistry.register_rule('custom', CustomRule())
        rule = VendorRuleRegistry.get_rule('custom')
        self.assertEqual(rule.get_fail_reason(), "Custom vendor rule failed")

    def test_check_points_with_vendor_column(self):
        today = datetime.now()
        data = {
            'Tool_Number': ['T001', 'T002'],
            'Tool Column': ['ProjectA', 'ProjectB'],
            'Customer schedule': [
                today + timedelta(days=5),
                today + timedelta(days=3)
            ],
            'Project Start Date': [
                today - timedelta(weeks=3),
                today - timedelta(weeks=3)
            ],
            'Responsible User': ['user1@test.com', 'user2@test.com'],
            'Vendor': ['vendor_a', 'vendor_b']  # Vendor info now directly in data
        }
        df = pd.DataFrame(data)
        
        checker = OutsourcingQcCheckPoints(df)
        failures = checker.get_failures()
        
        self.assertIn('Final Report', failures)
        if failures['Final Report']:
            self.assertIn('Vendor', failures['Final Report'][0])


if __name__ == '__main__':
    unittest.main()