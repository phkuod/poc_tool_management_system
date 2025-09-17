"""
Checkpoint strategies with DataFrame integration and comprehensive vendor validation.
Provides checkpoint system with vendor rules and detailed reporting.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time

from vendor_rules import VendorRuleRegistry


class VendorValidator:
    """Simple vendor validation logic extracted for reusability."""

    def validate(self, row: pd.Series) -> List[str]:
        """Validate vendor rules for a tool row."""
        vendor_key = self._get_vendor_key(row)
        if vendor_key is None:
            return ['Unsupported vendor or missing vendor information']

        vendor_rule = VendorRuleRegistry.get_rule(vendor_key)
        if vendor_rule:
            return self._execute_vendor_check(vendor_rule, row)
        else:
            return self._execute_fallback_vendor_check(vendor_key, row)

    def _get_vendor_key(self, row: pd.Series) -> Optional[str]:
        """Get vendor key from row, validate it exists in registry."""
        if 'Vendor' not in row or pd.isna(row['Vendor']):
            return None

        vendor_key = str(row['Vendor']).lower()
        if vendor_key in VendorRuleRegistry.list_vendors():
            return vendor_key
        return None

    def _execute_vendor_check(self, vendor_rule, row: pd.Series) -> List[str]:
        """Execute vendor rule validation."""
        try:
            result = vendor_rule.check_final_report_from_dataframe(row)
            if not result["success"]:
                return [self._format_fail_reason(result)]
        except Exception as e:
            return [f'Vendor validation error: {str(e)}']
        return []

    def _execute_fallback_vendor_check(self, vendor_key: str, row: pd.Series) -> List[str]:
        """Execute fallback vendor rule validation."""
        # This would need config injection for target_path
        return [f'No validation rule found for vendor: {vendor_key}']

    def _format_fail_reason(self, result: dict) -> str:
        """Format detailed fail reason from vendor validation result."""
        failed_steps = []
        steps = result.get("steps", {})

        for step_name, step_result in steps.items():
            if step_result.get("status") == "FAIL":
                failed_steps.append(f"{step_name}: {step_result.get('message', 'Failed')}")

        if failed_steps:
            base_reason = f"Validation failed - {', '.join(failed_steps)}"
        else:
            base_reason = "Validation failed"

        stats = result.get("statistics", {})
        if stats.get("total_patterns", 0) > 0:
            passing_rate = stats.get("passing_rate", 0)
            base_reason += f" (Pass rate: {passing_rate:.1f}%)"

        return base_reason


@dataclass
class CheckpointResult:
    """Simple, extensible result object for checkpoint validation."""
    name: str
    tool_number: str
    tool_column: str
    success: bool
    failures: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    executed: bool = False

    def add_failure(self, reason: str):
        """Add a failure reason and mark as unsuccessful."""
        self.failures.append(reason)
        self.success = False


@dataclass
class CheckpointConfig:
    """Simple configuration for checkpoint strategies."""
    target_path_template: str = "Target/Path/{tool_column}"

    def target_path_for(self, tool_column: str) -> Path:
        """Get target path for a given tool column."""
        return Path(self.target_path_template.format(tool_column=tool_column))


class CheckpointStrategy(ABC):
    """Checkpoint strategy with detailed reporting and DataFrame integration."""

    def __init__(self, name: str, config: Optional[CheckpointConfig] = None, priority: int = 0):
        self.name = name
        self.config = config or CheckpointConfig()
        self.priority = priority

    @abstractmethod
    def should_validate(self, row: pd.Series, today: datetime) -> bool:
        """Determine if this checkpoint should be evaluated for the given row."""
        pass

    @abstractmethod
    def validate_business_rules(self, row: pd.Series) -> List[str]:
        """
        Execute the core business logic validation.

        Args:
            row: DataFrame row with validation data

        Returns:
            List of failure reasons (empty list if validation passes)
        """
        pass

    def execute_check(self, row: pd.Series, today: datetime) -> CheckpointResult:
        """
        Template method that handles infrastructure and delegates to business logic.

        Args:
            row: DataFrame row with validation data
            today: Current date for validation

        Returns:
            Clean checkpoint result object
        """
        should_check = self.should_validate(row, today)
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']

        result = CheckpointResult(
            name=self.name,
            tool_number=tool_number,
            tool_column=tool_column,
            success=True
        )

        if should_check:
            start_time = time.time()

            try:
                failures = self.validate_business_rules(row)
                result.failures = failures
                result.success = len(failures) == 0
                result.executed = True
                result.execution_time = time.time() - start_time

            except Exception as e:
                result.executed = True
                result.add_failure(f'{self.name} execution error: {str(e)}')
                result.execution_time = time.time() - start_time

        return result



class PackageReadinessCheckpoint(CheckpointStrategy):
    """Package readiness checkpoint with detailed validation."""

    def __init__(self, config: Optional[CheckpointConfig] = None):
        super().__init__("Package Readiness", config, priority=1)

    def should_validate(self, row: pd.Series, today: datetime) -> bool:
        return today >= row['Project Start Date'] + pd.Timedelta(days=3)

    def validate_business_rules(self, row: pd.Series) -> List[str]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']

        target_path = self.config.target_path_for(tool_column)

        if not any(target_path.glob(f"*{tool_number}*")):
            return ['Package not found']

        return []


class FinalReportCheckpoint(CheckpointStrategy):
    """Final report checkpoint with clean vendor validation."""

    def __init__(self, config: Optional[CheckpointConfig] = None, vendor_validator: Optional[VendorValidator] = None):
        super().__init__("Final Report", config, priority=2)
        self.vendor_validator = vendor_validator or VendorValidator()

    def should_validate(self, row: pd.Series, today: datetime) -> bool:
        return (row['Customer schedule'] - today).days <= 5

    def validate_business_rules(self, row: pd.Series) -> List[str]:
        """Simple delegation to vendor validator."""
        return self.vendor_validator.validate(row)







class CheckpointRegistry:
    """Simple registry for checkpoint strategies."""

    def __init__(self):
        """Initialize empty registry."""
        self._checkpoints: List[CheckpointStrategy] = []

    def add(self, checkpoint: CheckpointStrategy):
        """Register a checkpoint strategy."""
        self._checkpoints.append(checkpoint)
        self._checkpoints.sort(key=lambda x: x.priority)

    def remove(self, checkpoint_name: str):
        """Remove a checkpoint by name."""
        self._checkpoints = [cp for cp in self._checkpoints if cp.name != checkpoint_name]

    def list(self) -> List[CheckpointStrategy]:
        """Get all registered checkpoints sorted by priority."""
        return self._checkpoints.copy()

    def clear(self):
        """Clear all registered checkpoints."""
        self._checkpoints.clear()

    def run_all_checks(self, row: pd.Series, today: datetime) -> Dict[str, Any]:
        """Execute all checkpoints for a given row."""
        results = {
            "tool_number": row['Tool_Number'],
            "tool_column": row['Tool Column'],
            "execution_timestamp": today.isoformat(),
            "checkpoints": [],
            "overall_success": True,
            "total_failures": 0,
            "executed_checkpoints": 0
        }

        for checkpoint in self.list():
            checkpoint_result = checkpoint.execute_check(row, today)
            results["checkpoints"].append(checkpoint_result)

            if checkpoint_result.executed:
                results["executed_checkpoints"] += 1

            if not checkpoint_result.success:
                results["overall_success"] = False
                results["total_failures"] += len(checkpoint_result.failures)

        return results

    @staticmethod
    def create_default(config: Optional[CheckpointConfig] = None) -> 'CheckpointRegistry':
        """Factory method to create registry with default checkpoints."""
        registry = CheckpointRegistry()
        registry.add(PackageReadinessCheckpoint(config))
        registry.add(FinalReportCheckpoint(config))
        return registry

