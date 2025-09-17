"""
Enhanced checkpoint strategies with DataFrame integration and comprehensive vendor validation.
Extends existing checkpoint system to support enhanced vendor rules with detailed reporting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from vendor_rules import EnhancedVendorRuleRegistry


class EnhancedCheckpointStrategy(ABC):
    """Enhanced checkpoint strategy with detailed reporting and DataFrame integration."""

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority

    @abstractmethod
    def should_check(self, row: pd.Series, today: datetime) -> bool:
        """Determine if this checkpoint should be evaluated for the given row."""
        pass

    @abstractmethod
    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        """Execute the checkpoint logic and return list of failures."""
        pass

    def execute_enhanced_check(self, row: pd.Series, today: datetime) -> Dict[str, Any]:
        """
        Execute enhanced checkpoint with detailed reporting.

        Args:
            row: DataFrame row with validation data
            today: Current date for validation

        Returns:
            Detailed checkpoint result with comprehensive information
        """
        should_check = self.should_check(row, today)

        result = {
            "checkpoint_name": self.name,
            "tool_number": row['Tool_Number'],
            "tool_column": row['Tool Column'],
            "should_check": should_check,
            "executed": False,
            "success": False,
            "failures": [],
            "detailed_result": None,
            "execution_time": None
        }

        if should_check:
            import time
            start_time = time.time()

            try:
                failures = self.execute_check(row, today)
                result["executed"] = True
                result["success"] = len(failures) == 0
                result["failures"] = failures
                result["execution_time"] = time.time() - start_time

            except Exception as e:
                result["executed"] = True
                result["success"] = False
                result["failures"] = [{
                    'Tool_Number': row['Tool_Number'],
                    'Project': row['Tool Column'],
                    'Fail Reason': f'Checkpoint execution error: {str(e)}',
                    'Responsible User': row.get('Responsible User', 'Unknown')
                }]
                result["execution_time"] = time.time() - start_time

        return result


class EnhancedPackageReadinessCheckpoint(EnhancedCheckpointStrategy):
    """Enhanced package readiness checkpoint with detailed validation."""

    def __init__(self):
        super().__init__("Enhanced Package Readiness", priority=1)

    def should_check(self, row: pd.Series, today: datetime) -> bool:
        return today >= row['Project Start Date'] + pd.Timedelta(days=3)

    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']
        target_path = Path(f"Target/Path/{tool_column}")

        if not any(target_path.glob(f"*{tool_number}*")):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Fail Reason': 'Package not found',
                'Responsible User': row['Responsible User'],
                'Checkpoint': self.name
            }]
        return []


class EnhancedFinalReportCheckpoint(EnhancedCheckpointStrategy):
    """Enhanced final report checkpoint with comprehensive vendor validation."""

    def __init__(self):
        super().__init__("Enhanced Final Report", priority=2)

    def should_check(self, row: pd.Series, today: datetime) -> bool:
        return (row['Customer schedule'] - today).days <= 5

    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']

        # Get vendor key and validate it exists
        vendor_key = self._get_vendor_key(row)
        if vendor_key is None:
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Vendor': str(row.get('Vendor', 'MISSING')),
                'Fail Reason': 'Unsupported vendor or missing vendor information',
                'Responsible User': row['Responsible User'],
                'Checkpoint': self.name
            }]

        # Try enhanced vendor rule first
        enhanced_rule = EnhancedVendorRuleRegistry.get_enhanced_rule(vendor_key)
        if enhanced_rule:
            return self._execute_enhanced_vendor_check(enhanced_rule, row)
        else:
            # Fallback to legacy vendor rule
            return self._execute_legacy_vendor_check(vendor_key, row)

    def execute_enhanced_check(self, row: pd.Series, today: datetime) -> Dict[str, Any]:
        """
        Execute enhanced checkpoint with comprehensive vendor validation.

        Args:
            row: DataFrame row with validation data
            today: Current date for validation

        Returns:
            Detailed checkpoint result with vendor validation details
        """
        base_result = super().execute_enhanced_check(row, today)

        if base_result["should_check"] and base_result["executed"]:
            vendor_key = self._get_vendor_key(row)
            enhanced_rule = EnhancedVendorRuleRegistry.get_enhanced_rule(vendor_key)

            if enhanced_rule:
                # Add detailed vendor validation result
                try:
                    detailed_result = enhanced_rule.check_final_report_from_dataframe(row)
                    base_result["detailed_result"] = detailed_result
                    base_result["vendor_validation"] = {
                        "vendor": vendor_key,
                        "enhanced_validation": True,
                        "validation_steps": detailed_result.get("steps", {}),
                        "statistics": detailed_result.get("statistics", {}),
                        "pattern_results": detailed_result.get("pattern_results", [])
                    }
                except Exception as e:
                    base_result["vendor_validation"] = {
                        "vendor": vendor_key,
                        "enhanced_validation": False,
                        "error": str(e)
                    }

        return base_result

    def _execute_enhanced_vendor_check(self, enhanced_rule, row: pd.Series) -> List[Dict[str, Any]]:
        """Execute enhanced vendor rule validation."""
        try:
            result = enhanced_rule.check_final_report_from_dataframe(row)

            if not result["success"]:
                # Create failure entry with detailed information
                failure_details = {
                    'Tool_Number': row['Tool_Number'],
                    'Project': row['Tool Column'],
                    'Vendor': result["vendor"],
                    'Fail Reason': self._format_enhanced_fail_reason(result),
                    'Responsible User': row['Responsible User'],
                    'Checkpoint': self.name,
                    'Enhanced_Validation': True,
                    'Validation_Details': result
                }
                return [failure_details]

        except Exception as e:
            return [{
                'Tool_Number': row['Tool_Number'],
                'Project': row['Tool Column'],
                'Vendor': enhanced_rule.vendor_key,
                'Fail Reason': f'Enhanced validation error: {str(e)}',
                'Responsible User': row['Responsible User'],
                'Checkpoint': self.name,
                'Enhanced_Validation': False
            }]

        return []

    def _execute_legacy_vendor_check(self, vendor_key: str, row: pd.Series) -> List[Dict[str, Any]]:
        """Execute legacy vendor rule validation."""
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']

        target_path = Path(f"Target/Path/{tool_column}")
        rule = VendorRuleRegistry.get_rule(vendor_key)

        if not rule.check_final_report(tool_column, tool_number, target_path):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Vendor': vendor_key,
                'Fail Reason': rule.get_fail_reason(),
                'Responsible User': row['Responsible User'],
                'Checkpoint': self.name,
                'Enhanced_Validation': False
            }]
        return []

    def _format_enhanced_fail_reason(self, result: Dict[str, Any]) -> str:
        """Format detailed fail reason from enhanced validation result."""
        failed_steps = []
        steps = result.get("steps", {})

        for step_name, step_result in steps.items():
            if step_result.get("status") == "FAIL":
                failed_steps.append(f"{step_name}: {step_result.get('message', 'Failed')}")

        if failed_steps:
            base_reason = f"Enhanced validation failed - {', '.join(failed_steps)}"
        else:
            base_reason = "Enhanced validation failed"

        # Add statistics information
        stats = result.get("statistics", {})
        if stats.get("total_patterns", 0) > 0:
            passing_rate = stats.get("passing_rate", 0)
            base_reason += f" (Pass rate: {passing_rate:.1f}%)"

        return base_reason

    def _get_vendor_key(self, row: pd.Series) -> str:
        """Get vendor key from row, validate it exists in registry, return None if invalid"""
        if 'Vendor' not in row or pd.isna(row['Vendor']):
            return None

        vendor_key = str(row['Vendor']).lower()

        # Check if vendor exists in enhanced or legacy registry
        if vendor_key in EnhancedVendorRuleRegistry.list_enhanced_vendors():
            return vendor_key
        elif vendor_key in VendorRuleRegistry.list_vendors():
            return vendor_key
        else:
            return None


class EnhancedCheckpointRegistry:
    """Registry for enhanced checkpoint strategies."""

    _enhanced_checkpoints: List[EnhancedCheckpointStrategy] = []

    @classmethod
    def register(cls, checkpoint: EnhancedCheckpointStrategy):
        """Register an enhanced checkpoint strategy."""
        cls._enhanced_checkpoints.append(checkpoint)
        cls._enhanced_checkpoints.sort(key=lambda x: x.priority)

    @classmethod
    def unregister(cls, checkpoint_name: str):
        """Remove an enhanced checkpoint by name."""
        cls._enhanced_checkpoints = [cp for cp in cls._enhanced_checkpoints if cp.name != checkpoint_name]

    @classmethod
    def get_all_enhanced_checkpoints(cls) -> List[EnhancedCheckpointStrategy]:
        """Get all registered enhanced checkpoints sorted by priority."""
        return cls._enhanced_checkpoints.copy()

    @classmethod
    def clear(cls):
        """Clear all registered enhanced checkpoints."""
        cls._enhanced_checkpoints.clear()

    @classmethod
    def initialize_enhanced_defaults(cls):
        """Initialize with enhanced default checkpoints."""
        cls.clear()
        cls.register(EnhancedPackageReadinessCheckpoint())
        cls.register(EnhancedFinalReportCheckpoint())

    @classmethod
    def execute_all_enhanced_checks(cls, row: pd.Series, today: datetime) -> Dict[str, Any]:
        """
        Execute all enhanced checkpoints for a given row.

        Args:
            row: DataFrame row with validation data
            today: Current date for validation

        Returns:
            Comprehensive results from all checkpoints
        """
        results = {
            "tool_number": row['Tool_Number'],
            "tool_column": row['Tool Column'],
            "execution_timestamp": today.isoformat(),
            "checkpoints": [],
            "overall_success": True,
            "total_failures": 0,
            "executed_checkpoints": 0
        }

        for checkpoint in cls.get_all_enhanced_checkpoints():
            checkpoint_result = checkpoint.execute_enhanced_check(row, today)
            results["checkpoints"].append(checkpoint_result)

            if checkpoint_result["executed"]:
                results["executed_checkpoints"] += 1

            if not checkpoint_result["success"]:
                results["overall_success"] = False
                results["total_failures"] += len(checkpoint_result.get("failures", []))

        return results


# Initialize enhanced checkpoint registry with defaults
EnhancedCheckpointRegistry.initialize_enhanced_defaults()