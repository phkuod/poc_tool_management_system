import pandas as pd
from datetime import datetime
from pathlib import Path
from vendor_rules import VendorRuleRegistry

class OutsourcingQcCheckPoints:
    def __init__(self, df):
        self.df = df
        self.today = datetime.now()

    def get_enhanced_results(self) -> pd.DataFrame:
        """
        Return original DataFrame with appended vendor validation results.

        Returns:
            DataFrame with added columns for all validation results
        """
        result_df = self.df.copy()

        # Add base validation result columns
        result_df['validation_status'] = 'PENDING'
        result_df['fail_reasons'] = None
        result_df['validation_details'] = None

        # Execute validation for each row
        for index, row in result_df.iterrows():
            vendor_key = self._get_vendor_key(row)

            if vendor_key is None:
                result_df.at[index, 'validation_status'] = 'FAILED'
                result_df.at[index, 'fail_reasons'] = ['Unsupported vendor or missing vendor information']
                continue

            # Get vendor rule and execute all validations
            vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
            all_validation_results = vendor_rule.execute_all_validations(row)

            # Collect all failures and details
            failed_rules = []
            all_details = {}
            overall_success = True

            for rule_name, result in all_validation_results.items():
                if not result['success']:
                    failed_rules.append(result['fail_reason'])
                    overall_success = False

                # Store rule-specific details
                if 'details' in result:
                    all_details[rule_name] = result['details']

            # Set results
            result_df.at[index, 'validation_status'] = 'PASSED' if overall_success else 'FAILED'
            result_df.at[index, 'fail_reasons'] = failed_rules if failed_rules else None
            result_df.at[index, 'validation_details'] = all_details if all_details else None

        return result_df

    def get_failures(self):
        """
        Returns dictionary of failures organized by validation rule type.
        """
        enhanced_df = self.get_enhanced_results()
        failed_rows = enhanced_df[enhanced_df['validation_status'] == 'FAILED']

        failures = {}

        for _, row in failed_rows.iterrows():
            vendor_key = self._get_vendor_key(row)

            if vendor_key is None:
                # Handle unsupported vendor case
                if 'Vendor Issues' not in failures:
                    failures['Vendor Issues'] = []
                failures['Vendor Issues'].append({
                    'Tool_Number': row['Tool_Number'],
                    'Project': row['Tool Column'],
                    'Vendor': row.get('Vendor', 'MISSING'),
                    'Fail Reason': 'Unsupported vendor or missing vendor information',
                    'Responsible User': row['Responsible User']
                })
                continue

            # Get validation results for this vendor
            vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
            all_validation_results = vendor_rule.execute_all_validations(row)

            for rule_name, result in all_validation_results.items():
                if not result['success']:
                    if rule_name not in failures:
                        failures[rule_name] = []

                    failures[rule_name].append({
                        'Tool_Number': row['Tool_Number'],
                        'Project': row['Tool Column'],
                        'Vendor': row.get('Vendor', 'MISSING'),
                        'Fail Reason': result['fail_reason'],
                        'Responsible User': row['Responsible User']
                    })

        return failures

    def _get_vendor_key(self, row: pd.Series) -> str:
        """Get vendor key from row, validate it exists in registry."""
        if 'Vendor' not in row or pd.isna(row['Vendor']):
            return None

        vendor_key = str(row['Vendor']).lower()

        # Check if vendor exists in registry
        if vendor_key not in VendorRuleRegistry.list_vendors():
            return None

        return vendor_key

    def add_vendor_rule(self, vendor_key: str, rule):
        """Add a validation rule to a specific vendor."""
        vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
        vendor_rule.add_rule(rule)

    def remove_vendor_rule(self, vendor_key: str, rule_name: str):
        """Remove a validation rule from a specific vendor."""
        vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
        vendor_rule.remove_rule(rule_name)

    def list_vendor_rules(self, vendor_key: str):
        """List all validation rules for a specific vendor."""
        vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
        return list(vendor_rule.get_rule_names())

    def list_vendors(self):
        """List all available vendors."""
        return VendorRuleRegistry.list_vendors()