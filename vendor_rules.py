"""
Enhanced vendor rules with DataFrame integration and comprehensive validation.
Supports regex-based archive discovery, configurable file extensions, and detailed reporting.
"""

import re
import pandas as pd
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

from vendor_config_loader import vendor_config_loader
from tar_file_reader import TarFileReader
from tar_compare import TarFileComparer


class EnhancedVendorRuleStrategy(ABC):
    """Enhanced vendor rule strategy with DataFrame integration and comprehensive validation."""

    def __init__(self, vendor_key: str, config_loader=None):
        """
        Initialize the enhanced vendor rule.

        Args:
            vendor_key: Vendor identifier (e.g., 'vendor_a')
            config_loader: Optional config loader instance (for testing)
        """
        self.vendor_key = vendor_key
        self.config_loader = config_loader or vendor_config_loader
        self.config = self.config_loader.get_vendor_config(vendor_key)
        self.global_paths = self.config_loader.get_global_paths()

        if not self.config:
            raise ValueError(f"No configuration found for vendor '{vendor_key}'")

        # Validate configuration
        is_valid, error_msg = self.config_loader.validate_vendor_config(vendor_key)
        if not is_valid:
            raise ValueError(f"Invalid configuration for vendor '{vendor_key}': {error_msg}")

    @abstractmethod
    def get_fail_reason(self) -> str:
        """Return vendor-specific failure reason."""
        pass

    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        """
        Legacy method for backward compatibility.

        Args:
            tool_column: Tool column identifier
            tool_number: Tool number identifier
            target_path: Target path for validation

        Returns:
            Boolean indicating validation success
        """
        # Create a minimal DataFrame row for compatibility
        row_data = {
            'Tool_Number': tool_number,
            'Tool Column': tool_column,
            'technology': 0  # Default technology value
        }

        result = self.check_final_report_from_dataframe(pd.Series(row_data))
        return result["success"]

    def check_final_report_from_dataframe(self, row: pd.Series, technology: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete validation using DataFrame row data with 5-step validation process.

        Args:
            row: DataFrame row with Tool_Number, Tool Column, technology, etc.
            technology: Technology value (can override row value)

        Returns:
            Comprehensive validation results dictionary
        """
        tool_number = row['Tool_Number']
        tool_column = row['Tool Column']
        tech_value = technology if technology is not None else row.get('technology', 0)

        validation_results = {
            "success": False,
            "vendor": self.vendor_key,
            "tool_number": tool_number,
            "tool_column": tool_column,
            "technology_value": tech_value,
            "paths": {
                "source_archive": None,
                "target_archive": None
            },
            "steps": {
                "archive_discovery": {"status": "PENDING", "message": ""},
                "target_exists": {"status": "PENDING", "message": ""},
                "file_consistency": {"status": "PENDING", "message": ""},
                "pattern_validation": {"status": "PENDING", "message": ""},
                "bypass_applied": {"status": "PENDING", "message": ""}
            },
            "statistics": {
                "pass_count": 0,
                "fail_count": 0,
                "bypassed_count": 0,
                "passing_rate": 0.0,
                "total_patterns": len(self.config["required_patterns"]),
                "checked_patterns": 0
            },
            "pattern_results": []
        }

        try:
            # Step 1: Archive Discovery using regex
            source_archive, target_archive = self._find_archives_from_dataframe(row)

            validation_results["paths"]["source_archive"] = str(source_archive) if source_archive else None
            validation_results["paths"]["target_archive"] = str(target_archive) if target_archive else None

            if not source_archive or not target_archive:
                validation_results["steps"]["archive_discovery"] = {
                    "status": "FAIL",
                    "message": f"Archives not found - Source: {source_archive}, Target: {target_archive}"
                }
                return validation_results

            validation_results["steps"]["archive_discovery"] = {
                "status": "PASS",
                "message": f"Archives found - Source: {source_archive.name}, Target: {target_archive.name}"
            }

            # Step 2: Target existence (already confirmed in discovery)
            validation_results["steps"]["target_exists"] = {
                "status": "PASS",
                "message": f"Target archive exists: {target_archive}"
            }

            # Step 3: File consistency check
            consistency_result = self._check_file_consistency(source_archive, target_archive, tool_number)
            validation_results["steps"]["file_consistency"] = consistency_result

            if consistency_result["status"] == "FAIL":
                return validation_results

            # Step 4 & 5: Pattern validation with bypass
            patterns_to_check, bypassed_patterns = self._apply_bypass_rules(tech_value)
            pass_count, fail_count, pattern_results = self._validate_patterns(target_archive, patterns_to_check, tool_number)

            # Add bypassed patterns to results
            for pattern in bypassed_patterns:
                pattern_results.append({
                    "pattern": pattern,
                    "status": "BYPASSED",
                    "bypass_reason": f"Technology {tech_value} > {self.config['bypass_rules']['technology_threshold']}",
                    "files": []
                })

            validation_results["pattern_results"] = pattern_results
            validation_results["steps"]["bypass_applied"] = {
                "status": "INFO",
                "message": f"Bypassed {len(bypassed_patterns)} patterns based on technology value {tech_value}"
            }

            validation_results["steps"]["pattern_validation"] = {
                "status": "PASS" if fail_count == 0 else "FAIL",
                "message": f"Pattern validation: {pass_count}/{len(patterns_to_check)} patterns passed"
            }

            # Final statistics
            total_checked = len(patterns_to_check)
            validation_results["statistics"].update({
                "pass_count": pass_count,
                "fail_count": fail_count,
                "bypassed_count": len(bypassed_patterns),
                "passing_rate": (pass_count / total_checked * 100) if total_checked > 0 else 100.0,
                "checked_patterns": total_checked
            })

            # Overall success
            validation_results["success"] = (
                validation_results["steps"]["archive_discovery"]["status"] == "PASS" and
                validation_results["steps"]["target_exists"]["status"] == "PASS" and
                validation_results["steps"]["file_consistency"]["status"] in ["PASS", "SKIPPED"] and
                validation_results["steps"]["pattern_validation"]["status"] == "PASS"
            )

        except Exception as e:
            validation_results["steps"]["archive_discovery"]["status"] = "ERROR"
            validation_results["steps"]["archive_discovery"]["message"] = f"Validation error: {str(e)}"

        return validation_results

    def _find_archives_from_dataframe(self, row: pd.Series) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Find source and target archives using DataFrame data and regex patterns.

        Args:
            row: DataFrame row containing tool_number, tool_column, etc.

        Returns:
            Tuple of (source_archive_path, target_archive_path) or (None, None) if not found
        """
        tool_number = row['Tool_Number']
        tool_column = row['Tool Column']

        # Get regex patterns from config
        archive_config = self.config["archive_config"]
        source_regex = archive_config["source_archive_regex"]
        target_regex = archive_config["target_archive_regex"]

        # Substitute variables in regex patterns
        substitutions = {
            "source_root": self.global_paths["source_root"],
            "target_root": self.global_paths["target_root"],
            "tool_number": tool_number,
            "tool_column": tool_column
        }

        try:
            source_pattern = self.config_loader.compile_regex_pattern(source_regex, **substitutions)
            target_pattern = self.config_loader.compile_regex_pattern(target_regex, **substitutions)
        except ValueError as e:
            raise ValueError(f"Failed to compile regex patterns for vendor {self.vendor_key}: {e}")

        # Find source archive
        source_archive = None
        source_search_path = Path(self.global_paths["source_root"])
        if source_search_path.exists():
            for file_path in source_search_path.rglob("*.tar.gz"):
                # Normalize file path for regex matching (convert backslashes to forward slashes)
                normalized_path = str(file_path).replace('\\', '/')
                if source_pattern.match(normalized_path):
                    source_archive = file_path
                    break

        # Find target archive
        target_archive = None
        target_search_path = Path(self.global_paths["target_root"])
        if target_search_path.exists():
            for file_path in target_search_path.rglob("*.tar.gz"):
                # Normalize file path for regex matching (convert backslashes to forward slashes)
                normalized_path = str(file_path).replace('\\', '/')
                if target_pattern.match(normalized_path):
                    target_archive = file_path
                    break

        return source_archive, target_archive

    def _check_file_consistency(self, source_archive: Path, target_archive: Path, tool_number: str) -> Dict[str, str]:
        """
        Check file consistency between source and target archives.

        Args:
            source_archive: Path to source archive
            target_archive: Path to target archive
            tool_number: Tool number for logging

        Returns:
            Dictionary with status and message
        """
        consistency_config = self.config["archive_config"]["consistency_check"]

        if not consistency_config.get("enabled", False):
            return {
                "status": "SKIPPED",
                "message": "File consistency check disabled",
                "checked_extension": None
            }

        file_extension = consistency_config["file_extension"]

        try:
            comparer = TarFileComparer(str(source_archive), str(target_archive))
            result = comparer.compare_files(file_extension)

            if result.success:
                return {
                    "status": "PASS",
                    "message": f".{file_extension} files are identical between source and target",
                    "checked_extension": file_extension
                }
            else:
                return {
                    "status": "FAIL",
                    "message": f".{file_extension} file consistency check failed: {result.message}",
                    "checked_extension": file_extension
                }

        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Error during consistency check: {str(e)}",
                "checked_extension": file_extension
            }

    def _apply_bypass_rules(self, technology: int) -> Tuple[List[str], List[str]]:
        """
        Apply bypass rules based on technology value.

        Args:
            technology: Technology value

        Returns:
            Tuple of (patterns_to_check, bypassed_patterns)
        """
        bypass_rules = self.config["bypass_rules"]
        threshold = bypass_rules["technology_threshold"]
        bypass_patterns = bypass_rules["bypass_patterns"]

        patterns_to_check = []
        bypassed_patterns = []

        for pattern in self.config["required_patterns"]:
            should_bypass = False

            # Check if pattern matches any bypass pattern
            for bypass_pattern in bypass_patterns:
                if pattern.endswith(bypass_pattern) and technology > threshold:
                    should_bypass = True
                    break

            if should_bypass:
                bypassed_patterns.append(pattern)
            else:
                patterns_to_check.append(pattern)

        return patterns_to_check, bypassed_patterns

    def _validate_patterns(self, target_archive: Path, patterns_to_check: List[str], tool_number: str) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Validate required patterns in target archive.

        Args:
            target_archive: Path to target archive
            patterns_to_check: List of patterns to validate
            tool_number: Tool number for pattern substitution

        Returns:
            Tuple of (pass_count, fail_count, pattern_results)
        """
        pass_count = 0
        fail_count = 0
        pattern_results = []

        try:
            target_reader = TarFileReader(str(target_archive))

            for pattern in patterns_to_check:
                formatted_pattern = pattern.format(tool_number=tool_number)
                matches = list(target_reader.search_files_by_pattern(formatted_pattern))

                # Filter files with size > 0
                valid_files = [match for match in matches if match[2] > 0]

                if valid_files:
                    pass_count += 1
                    pattern_results.append({
                        "pattern": pattern,
                        "formatted_pattern": formatted_pattern,
                        "status": "PASS",
                        "files": valid_files,
                        "file_count": len(valid_files)
                    })
                else:
                    fail_count += 1
                    pattern_results.append({
                        "pattern": pattern,
                        "formatted_pattern": formatted_pattern,
                        "status": "FAIL",
                        "files": [],
                        "file_count": 0
                    })

        except Exception as e:
            # If we can't read the archive, mark all patterns as failed
            fail_count = len(patterns_to_check)
            for pattern in patterns_to_check:
                pattern_results.append({
                    "pattern": pattern,
                    "status": "FAIL",
                    "files": [],
                    "file_count": 0,
                    "error": str(e)
                })

        return pass_count, fail_count, pattern_results


class EnhancedVendorARule(EnhancedVendorRuleStrategy):
    """Enhanced Vendor A rule with tar.gz support and configurable patterns."""

    def __init__(self, config_loader=None):
        super().__init__("vendor_a", config_loader)

    def get_fail_reason(self) -> str:
        return "Vendor A validation failed - check pattern validation details"


class EnhancedVendorBRule(EnhancedVendorRuleStrategy):
    """Enhanced Vendor B rule with tar.gz support and configurable patterns."""

    def __init__(self, config_loader=None):
        super().__init__("vendor_b", config_loader)

    def get_fail_reason(self) -> str:
        return "Vendor B validation failed - check pattern validation details"


class EnhancedVendorCRule(EnhancedVendorRuleStrategy):
    """Enhanced Vendor C rule with tar.gz support and configurable patterns."""

    def __init__(self, config_loader=None):
        super().__init__("vendor_c", config_loader)

    def get_fail_reason(self) -> str:
        return "Vendor C validation failed - check pattern validation details"


class EnhancedVendorRuleRegistry:
    """Registry for enhanced vendor rules with automatic configuration loading."""

    _enhanced_rules = {}

    @classmethod
    def get_enhanced_rule(cls, vendor_key: str) -> Optional[EnhancedVendorRuleStrategy]:
        """
        Get enhanced vendor rule by key.

        Args:
            vendor_key: Vendor identifier

        Returns:
            Enhanced vendor rule instance or None if not found
        """
        vendor_key = vendor_key.lower()

        if vendor_key not in cls._enhanced_rules:
            # Try to create rule dynamically if config exists
            if vendor_config_loader.get_vendor_config(vendor_key):
                try:
                    # For now, use a generic enhanced rule
                    cls._enhanced_rules[vendor_key] = EnhancedVendorRuleStrategy(vendor_key)
                except ValueError:
                    return None
            else:
                return None

        return cls._enhanced_rules.get(vendor_key)

    @classmethod
    def register_enhanced_rule(cls, vendor_key: str, rule: EnhancedVendorRuleStrategy):
        """
        Register an enhanced vendor rule.

        Args:
            vendor_key: Vendor identifier
            rule: Enhanced vendor rule instance
        """
        cls._enhanced_rules[vendor_key.lower()] = rule

    @classmethod
    def list_enhanced_vendors(cls) -> List[str]:
        """
        Get list of all available enhanced vendors.

        Returns:
            List of enhanced vendor keys
        """
        # Return both registered and configured vendors
        registered = list(cls._enhanced_rules.keys())
        configured = vendor_config_loader.list_vendors()
        return list(set(registered + configured))

    @classmethod
    def clear_cache(cls):
        """Clear cached rules and reload configurations."""
        cls._enhanced_rules.clear()
        vendor_config_loader.clear_cache()


# Create a generic enhanced vendor rule class
class GenericEnhancedVendorRule(EnhancedVendorRuleStrategy):
    """Generic enhanced vendor rule that works with any configured vendor."""

    def __init__(self, vendor_key: str, config_loader=None):
        super().__init__(vendor_key, config_loader)

    def get_fail_reason(self) -> str:
        return f"{self.vendor_key} validation failed - check pattern validation details"


# Override the get_enhanced_rule method to use generic class
def _get_enhanced_rule_generic(cls, vendor_key: str) -> Optional[EnhancedVendorRuleStrategy]:
    """Get enhanced vendor rule with generic fallback."""
    vendor_key = vendor_key.lower()

    if vendor_key not in cls._enhanced_rules:
        if vendor_config_loader.get_vendor_config(vendor_key):
            try:
                cls._enhanced_rules[vendor_key] = GenericEnhancedVendorRule(vendor_key)
            except ValueError:
                return None
        else:
            return None

    return cls._enhanced_rules.get(vendor_key)

# Replace the method
EnhancedVendorRuleRegistry.get_enhanced_rule = classmethod(_get_enhanced_rule_generic)