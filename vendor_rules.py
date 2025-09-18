from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Set
import pandas as pd
import re


class ValidationRule(ABC):
    """Base class for individual validation rules."""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Return the name of this validation rule."""
        pass

    @abstractmethod
    def validate(self, row: pd.Series) -> Dict[str, Any]:
        """
        Execute the validation rule.

        Args:
            row: DataFrame row containing tool data

        Returns:
            {
                "success": bool,
                "fail_reason": str | None,
                "details": Dict[str, Any]  # Rule-specific details
            }
        """
        pass


class ArchiveValidationRule(ValidationRule):
    """Validation rule for checking archive files."""

    @property
    def rule_name(self) -> str:
        return "Archive Validation"

    def __init__(self, source_pattern: str, target_pattern: str,
                 source_path_template: str, target_path_template: str,
                 vendor_name: str = ""):
        self.source_pattern = source_pattern
        self.target_pattern = target_pattern
        self.source_path_template = source_path_template
        self.target_path_template = target_path_template
        self.vendor_name = vendor_name

    def validate(self, row: pd.Series) -> Dict[str, Any]:
        base_paths = {'source_root': 'Sources', 'target_root': 'Targets'}

        # Build search paths
        source_path = Path(self._build_path_from_template(self.source_path_template, row, base_paths))
        target_path = Path(self._build_path_from_template(self.target_path_template, row, base_paths))

        # Find archives
        source_archive = self._find_archive_by_pattern(source_path, self.source_pattern.format(tool_number=row['Tool_Number']))
        target_archive = self._find_archive_by_pattern(target_path, self.target_pattern.format(tool_number=row['Tool_Number']))

        success = source_archive is not None and target_archive is not None
        fail_reason = None
        if not success:
            missing = []
            if not source_archive:
                missing.append(f"source archive (pattern: {self.source_pattern.format(tool_number=row['Tool_Number'])})")
            if not target_archive:
                missing.append(f"target archive (pattern: {self.target_pattern.format(tool_number=row['Tool_Number'])})")
            prefix = f"{self.vendor_name}: " if self.vendor_name else ""
            fail_reason = f"{prefix}Missing {' and '.join(missing)}"

        return {
            "success": success,
            "fail_reason": fail_reason,
            "details": {
                "source_archive": source_archive,
                "target_archive": target_archive,
                "source_pattern": self.source_pattern.format(tool_number=row['Tool_Number']),
                "target_pattern": self.target_pattern.format(tool_number=row['Tool_Number']),
                "source_archive_found": source_archive is not None,
                "target_archive_found": target_archive is not None,
                "source_archive_path": source_archive,
                "target_archive_path": target_archive
            }
        }

    def _find_archive_by_pattern(self, search_path: Path, pattern: str) -> str:
        """Find archive file matching regex pattern."""
        if not search_path.exists():
            return None

        for file_path in search_path.rglob("*.tar.gz"):
            if re.match(pattern, file_path.name):
                return str(file_path)
        return None

    def _build_path_from_template(self, template: str, row: pd.Series, base_paths: Dict[str, str]) -> str:
        """Build file path from template using DataFrame row data."""
        path = template.format(
            source_root=base_paths.get('source_root', 'Sources'),
            target_root=base_paths.get('target_root', 'Targets'),
            tool_column=row['Tool Column'],
            tool_number=row['Tool_Number'],
            vendor=row.get('Vendor', 'default')
        )
        return path


class VendorRuleStrategy(ABC):
    """Base class for vendor-specific validation strategies."""

    def __init__(self):
        self._rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule):
        """Add a validation rule to this vendor strategy."""
        self._rules.append(rule)

    def remove_rule(self, rule_name: str):
        """Remove a validation rule by name."""
        self._rules = [rule for rule in self._rules if rule.rule_name != rule_name]

    def get_rule_names(self) -> Set[str]:
        """Get names of all validation rules."""
        return {rule.rule_name for rule in self._rules}


    def execute_all_validations(self, row: pd.Series) -> Dict[str, Dict[str, Any]]:
        """
        Execute all validation rules for this vendor.

        Returns:
            Dict mapping rule names to their validation results
        """
        results = {}
        for rule in self._rules:
            results[rule.rule_name] = rule.validate(row)
        return results


class DefaultVendorRule(VendorRuleStrategy):
    def __init__(self):
        super().__init__()
        # Default vendor includes archive validation
        self.add_rule(ArchiveValidationRule(
            source_pattern=r"source_{tool_number}_.*\.tar\.gz$",
            target_pattern=r"target_{tool_number}_.*\.tar\.gz$",
            source_path_template="{source_root}/{tool_column}",
            target_path_template="{target_root}/{tool_column}",
            vendor_name="Default"
        ))


class VendorARule(VendorRuleStrategy):
    def __init__(self):
        super().__init__()
        # Vendor A includes archive validation
        self.add_rule(ArchiveValidationRule(
            source_pattern=r"source_{tool_number}_v\d+\.tar\.gz$",
            target_pattern=r"target_{tool_number}_final\.tar\.gz$",
            source_path_template="{source_root}/{tool_column}",
            target_path_template="{target_root}/{tool_column}",
            vendor_name="Vendor A"
        ))

        # Additional Vendor A validation rules
        self.add_rule(ArchiveValidationRule(
            source_pattern=r"backup_{tool_number}_\d{{8}}\.tar\.gz$",
            target_pattern=r"deployment_{tool_number}_ready\.tar\.gz$",
            source_path_template="{source_root}/{tool_column}/backups",
            target_path_template="{target_root}/{tool_column}/deploy",
            vendor_name="Vendor A - Backup"
        ))

        # Database validation for Vendor A
        self.add_rule(DatabaseValidationRule("vendor_a_tools", "Vendor A"))


class VendorBRule(VendorRuleStrategy):
    def __init__(self):
        super().__init__()
        # Vendor B includes archive validation with different paths
        self.add_rule(ArchiveValidationRule(
            source_pattern=r"pkg_{tool_number}_\d+\.tar\.gz$",
            target_pattern=r"final_{tool_number}_\w+\.tar\.gz$",
            source_path_template="{source_root}/packages",
            target_path_template="{target_root}/deliveries/{tool_column}",
            vendor_name="Vendor B"
        ))


class VendorCRule(VendorRuleStrategy):
    def __init__(self):
        super().__init__()
        # Vendor C includes archive validation with staging/completed paths
        self.add_rule(ArchiveValidationRule(
            source_pattern=r"src_{tool_number}_\d{{8}}\.tar\.gz$",
            target_pattern=r"release_{tool_number}_final\.tar\.gz$",
            source_path_template="{source_root}/{tool_column}/staging",
            target_path_template="{target_root}/{tool_column}/completed",
            vendor_name="Vendor C"
        ))


class VendorDRule(VendorRuleStrategy):
    """Example vendor that only needs database validation, no archive checks."""
    def __init__(self):
        super().__init__()
        # Vendor D doesn't need any validation rules - or could have custom ones
        # No archive validation needed for this vendor
        pass


class DatabaseValidationRule(ValidationRule):
    """Example validation rule for database checks."""

    @property
    def rule_name(self) -> str:
        return "Database Validation"

    def __init__(self, table_name: str, vendor_name: str = ""):
        self.table_name = table_name
        self.vendor_name = vendor_name

    def validate(self, row: pd.Series) -> Dict[str, Any]:
        # This is a mock implementation - replace with actual database logic
        tool_number = row['Tool_Number']

        # Mock database check
        # In reality, you'd check if the tool exists in the specified table
        mock_exists = tool_number.startswith('T00')  # Mock logic

        success = mock_exists
        fail_reason = None if success else f"{self.vendor_name}: Tool {tool_number} not found in {self.table_name}"

        return {
            "success": success,
            "fail_reason": fail_reason,
            "details": {
                "table_name": self.table_name,
                "tool_number": tool_number,
                "exists_in_database": mock_exists
            }
        }


class VendorRuleRegistry:
    _rules = {
        'default': DefaultVendorRule(),
        'vendor_a': VendorARule(),
        'vendor_b': VendorBRule(),
        'vendor_c': VendorCRule(),
        'vendor_d': VendorDRule(),
    }

    @classmethod
    def get_rule(cls, vendor_key: str) -> VendorRuleStrategy:
        return cls._rules.get(vendor_key.lower(), cls._rules['default'])

    @classmethod
    def register_rule(cls, vendor_key: str, rule: VendorRuleStrategy):
        cls._rules[vendor_key.lower()] = rule

    @classmethod
    def list_vendors(cls) -> List[str]:
        return list(cls._rules.keys())