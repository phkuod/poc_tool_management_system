"""
Outsourcing QC check points with DataFrame integration and comprehensive vendor validation.
Extends existing checkpoint system to support enhanced vendor rules with detailed reporting.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from checkpoint_strategies import CheckpointRegistry


class OutsourcingQcCheckPoints:
    """QC check points with comprehensive validation and detailed reporting."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize enhanced QC check points.

        Args:
            df: DataFrame with tool validation data
        """
        self.df = df
        self.today = datetime.now()

        # Initialize enhanced checkpoint registry
        CheckpointRegistry.initialize_defaults()

    def get_failures(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns a dictionary of all failed rules using appropriate validation system.

        Returns:
            Dictionary mapping checkpoint names to lists of failure details
        """
        return self._get_failures()

    def get_results(self) -> Dict[str, Any]:
        """
        Get comprehensive enhanced validation results for all rows.

        Returns:
            Detailed results including statistics, validation steps, and pattern analysis
        """

        results = {
            "validation_timestamp": self.today.isoformat(),
            "total_tools": len(self.df),
            "enhanced_validation": True,
            "tool_results": [],
            "summary": {
                "total_failures": 0,
                "total_successes": 0,
                "tools_with_enhanced_validation": 0,
                "tools_with_legacy_fallback": 0,
                "vendor_statistics": {}
            }
        }

        for index, row in self.df.iterrows():
            tool_result = CheckpointRegistry.execute_all_checks(row, self.today)
            results["tool_results"].append(tool_result)

            # Update summary statistics
            if tool_result["overall_success"]:
                results["summary"]["total_successes"] += 1
            else:
                results["summary"]["total_failures"] += 1

            # Track vendor statistics
            vendor = row.get('Vendor', 'Unknown')
            if vendor not in results["summary"]["vendor_statistics"]:
                results["summary"]["vendor_statistics"][vendor] = {
                    "total_tools": 0,
                    "successes": 0,
                    "failures": 0,
                    "enhanced_validations": 0
                }

            vendor_stats = results["summary"]["vendor_statistics"][vendor]
            vendor_stats["total_tools"] += 1

            if tool_result["overall_success"]:
                vendor_stats["successes"] += 1
            else:
                vendor_stats["failures"] += 1

            # Check if any checkpoint used enhanced validation
            for checkpoint_result in tool_result["checkpoints"]:
                if checkpoint_result.get("detailed_result"):
                    vendor_stats["enhanced_validations"] += 1
                    results["summary"]["tools_with_enhanced_validation"] += 1
                    break
            else:
                results["summary"]["tools_with_legacy_fallback"] += 1

        return results

    def get_vendor_analysis(self) -> Dict[str, Any]:
        """
        Get detailed vendor-specific analysis with enhanced validation insights.

        Returns:
            Comprehensive vendor analysis including pattern validation statistics
        """

        vendor_analysis = {}

        for index, row in self.df.iterrows():
            vendor = row.get('Vendor', 'Unknown')
            tool_number = row['Tool_Number']

            if vendor not in vendor_analysis:
                vendor_analysis[vendor] = {
                    "total_tools": 0,
                    "enhanced_validation_available": False,
                    "tools": {},
                    "pattern_statistics": {
                        "total_patterns_checked": 0,
                        "total_patterns_passed": 0,
                        "total_patterns_failed": 0,
                        "total_patterns_bypassed": 0,
                        "average_passing_rate": 0.0
                    },
                    "common_failures": {}
                }

            vendor_data = vendor_analysis[vendor]
            vendor_data["total_tools"] += 1

            # Execute enhanced validation for this tool
            tool_result = CheckpointRegistry.execute_all_checks(row, self.today)
            vendor_data["tools"][tool_number] = tool_result

            # Analyze enhanced validation details
            for checkpoint_result in tool_result["checkpoints"]:
                detailed_result = checkpoint_result.get("detailed_result")
                if detailed_result:
                    vendor_data["enhanced_validation_available"] = True

                    # Aggregate pattern statistics
                    stats = detailed_result.get("statistics", {})
                    pattern_stats = vendor_data["pattern_statistics"]

                    pattern_stats["total_patterns_checked"] += stats.get("checked_patterns", 0)
                    pattern_stats["total_patterns_passed"] += stats.get("pass_count", 0)
                    pattern_stats["total_patterns_failed"] += stats.get("fail_count", 0)
                    pattern_stats["total_patterns_bypassed"] += stats.get("bypassed_count", 0)

                    # Track common failure patterns
                    for pattern_result in detailed_result.get("pattern_results", []):
                        if pattern_result.get("status") == "FAIL":
                            pattern = pattern_result["pattern"]
                            if pattern not in vendor_data["common_failures"]:
                                vendor_data["common_failures"][pattern] = 0
                            vendor_data["common_failures"][pattern] += 1

        # Calculate average passing rates
        for vendor_data in vendor_analysis.values():
            pattern_stats = vendor_data["pattern_statistics"]
            total_checked = pattern_stats["total_patterns_checked"]
            if total_checked > 0:
                pattern_stats["average_passing_rate"] = (
                    pattern_stats["total_patterns_passed"] / total_checked * 100
                )

        return vendor_analysis

    def _get_failures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get failures using enhanced validation system."""
        failures = {}

        for checkpoint in CheckpointRegistry.get_all_checkpoints():
            failures[checkpoint.name] = []

            for index, row in self.df.iterrows():
                if checkpoint.should_check(row, self.today):
                    checkpoint_failures = checkpoint.execute_check(row, self.today)
                    failures[checkpoint.name].extend(checkpoint_failures)

        return failures


    def add_checkpoint(self, checkpoint):
        """Add a new checkpoint to the enhanced registry."""
        CheckpointRegistry.register(checkpoint)

    def remove_checkpoint(self, checkpoint_name: str):
        """Remove a checkpoint by name from the enhanced registry."""
        CheckpointRegistry.unregister(checkpoint_name)

    def list_checkpoints(self) -> List[str]:
        """List all registered checkpoint names."""
        return [cp.name for cp in CheckpointRegistry.get_all_checkpoints()]

    def export_detailed_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export comprehensive validation report.

        Args:
            output_file: Optional file path to save JSON report

        Returns:
            Complete validation report
        """

        report = {
            "report_metadata": {
                "generation_timestamp": self.today.isoformat(),
                "total_tools_analyzed": len(self.df),
                "validation_type": "enhanced",
                "report_version": "1.0"
            },
            "results": self.get_results(),
            "vendor_analysis": self.get_vendor_analysis(),
            "failures": self._get_failures()
        }

        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for validation results.

        Returns:
            Summary statistics including success rates and failure analysis
        """
        results = self.get_results()
        summary = results["summary"]

        total_tools = summary["total_successes"] + summary["total_failures"]
        success_rate = (summary["total_successes"] / total_tools * 100) if total_tools > 0 else 0

        return {
            "validation_type": "enhanced",
            "total_tools": total_tools,
            "successful_tools": summary["total_successes"],
            "failed_tools": summary["total_failures"],
            "success_rate": success_rate,
            "enhanced_validation_usage": summary["tools_with_enhanced_validation"],
            "legacy_fallback_usage": summary["tools_with_legacy_fallback"],
            "vendor_count": len(summary["vendor_statistics"])
        }