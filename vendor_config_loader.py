"""
Configuration loader utility for vendor-specific validation rules.
Handles loading and validation of vendor configurations from config.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class VendorConfigLoader:
    """Utility class for loading and managing vendor configurations."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the config loader.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self._config_cache = None
        self._compiled_patterns = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load the complete configuration from file.

        Returns:
            Dictionary containing the full configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if self._config_cache is None:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self._config_cache = json.load(f)

            self._validate_config_structure(self._config_cache)

        return self._config_cache

    def get_vendor_config(self, vendor_key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific vendor.

        Args:
            vendor_key: Vendor identifier (e.g., 'vendor_a')

        Returns:
            Vendor configuration dictionary or None if not found
        """
        config = self.load_config()
        return config.get("vendors", {}).get(vendor_key.lower())

    def get_global_paths(self) -> Dict[str, str]:
        """
        Get global path configuration.

        Returns:
            Dictionary containing source_root and target_root paths
        """
        config = self.load_config()
        return config.get("paths", {})

    def list_vendors(self) -> list:
        """
        Get list of all configured vendors.

        Returns:
            List of vendor keys
        """
        config = self.load_config()
        return list(config.get("vendors", {}).keys())

    def validate_vendor_config(self, vendor_key: str) -> Tuple[bool, str]:
        """
        Validate a specific vendor's configuration.

        Args:
            vendor_key: Vendor identifier to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        vendor_config = self.get_vendor_config(vendor_key)
        if not vendor_config:
            return False, f"Vendor '{vendor_key}' not found in configuration"

        # Check required sections
        required_sections = ["archive_config", "required_patterns", "bypass_rules"]
        for section in required_sections:
            if section not in vendor_config:
                return False, f"Missing required section '{section}' for vendor '{vendor_key}'"

        # Validate archive config
        archive_config = vendor_config["archive_config"]
        required_archive_fields = ["source_archive_regex", "target_archive_regex", "consistency_check"]
        for field in required_archive_fields:
            if field not in archive_config:
                return False, f"Missing required field '{field}' in archive_config for vendor '{vendor_key}'"

        # Validate consistency check config
        consistency_config = archive_config["consistency_check"]
        if "enabled" not in consistency_config or "file_extension" not in consistency_config:
            return False, f"Invalid consistency_check configuration for vendor '{vendor_key}'"

        # Validate regex patterns
        try:
            self._validate_regex_pattern(archive_config["source_archive_regex"])
            self._validate_regex_pattern(archive_config["target_archive_regex"])
        except re.error as e:
            return False, f"Invalid regex pattern for vendor '{vendor_key}': {e}"

        # Validate required patterns
        if not isinstance(vendor_config["required_patterns"], list) or not vendor_config["required_patterns"]:
            return False, f"required_patterns must be a non-empty list for vendor '{vendor_key}'"

        # Validate bypass rules
        bypass_rules = vendor_config["bypass_rules"]
        if "technology_threshold" not in bypass_rules or "bypass_patterns" not in bypass_rules:
            return False, f"Invalid bypass_rules configuration for vendor '{vendor_key}'"

        return True, "Configuration is valid"

    def compile_regex_pattern(self, pattern: str, **kwargs) -> re.Pattern:
        """
        Compile and cache regex patterns with variable substitution.

        Args:
            pattern: Regex pattern string with format placeholders
            **kwargs: Variables to substitute in the pattern

        Returns:
            Compiled regex pattern
        """
        # Create cache key from pattern and substitutions
        cache_key = (pattern, tuple(sorted(kwargs.items())))

        if cache_key not in self._compiled_patterns:
            try:
                formatted_pattern = pattern.format(**kwargs)
                compiled_pattern = re.compile(formatted_pattern)
                self._compiled_patterns[cache_key] = compiled_pattern
            except (KeyError, re.error) as e:
                raise ValueError(f"Failed to compile regex pattern '{pattern}' with variables {kwargs}: {e}")

        return self._compiled_patterns[cache_key]

    def clear_cache(self):
        """Clear cached configuration and compiled patterns."""
        self._config_cache = None
        self._compiled_patterns.clear()

    def _validate_config_structure(self, config: Dict[str, Any]):
        """
        Validate the basic structure of the configuration.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration structure is invalid
        """
        # Check for required top-level sections
        if "paths" not in config:
            raise ValueError("Configuration missing required 'paths' section")

        if "vendors" not in config:
            raise ValueError("Configuration missing required 'vendors' section")

        # Validate paths section
        paths = config["paths"]
        required_paths = ["source_root", "target_root"]
        for path_key in required_paths:
            if path_key not in paths:
                raise ValueError(f"Missing required path '{path_key}' in paths configuration")

            path_value = paths[path_key]
            if not isinstance(path_value, str) or not path_value:
                raise ValueError(f"Path '{path_key}' must be a non-empty string")

        # Validate vendors section
        vendors = config["vendors"]
        if not isinstance(vendors, dict) or not vendors:
            raise ValueError("Vendors section must be a non-empty dictionary")

    def _validate_regex_pattern(self, pattern: str):
        """
        Validate that a regex pattern can be compiled.

        Args:
            pattern: Regex pattern string to validate

        Raises:
            re.error: If pattern is invalid
        """
        # Test pattern with dummy substitutions
        test_pattern = pattern.format(
            source_root="test_source",
            target_root="test_target",
            tool_number="T001",
            tool_column="TestProject"
        )
        re.compile(test_pattern)


# Global instance for easy access
vendor_config_loader = VendorConfigLoader()