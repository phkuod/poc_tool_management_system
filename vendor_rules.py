from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class VendorRuleStrategy(ABC):
    @abstractmethod
    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        """Check if final report exists according to vendor-specific rules."""
        pass

    @abstractmethod
    def get_fail_reason(self) -> str:
        """Return vendor-specific failure reason."""
        pass


class DefaultVendorRule(VendorRuleStrategy):
    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        return any(target_path.glob(f"Final_Report_*{tool_number}*.pdf"))
    
    def get_fail_reason(self) -> str:
        return "Final report not found"


class VendorARule(VendorRuleStrategy):
    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        return any(target_path.glob(f"Report_{tool_number}_*.xlsx"))
    
    def get_fail_reason(self) -> str:
        return "Vendor A report not found (Excel format required)"


class VendorBRule(VendorRuleStrategy):
    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        vendor_path = target_path / "VendorB"
        return any(vendor_path.glob(f"Final_*{tool_number}*.pdf"))
    
    def get_fail_reason(self) -> str:
        return "Vendor B final report not found in VendorB subfolder"


class VendorCRule(VendorRuleStrategy):
    def check_final_report(self, tool_column: str, tool_number: str, target_path: Path) -> bool:
        completed_path = target_path / "completed"
        summary_exists = any(completed_path.glob(f"Summary_{tool_number}.pdf"))
        details_exists = any(completed_path.glob(f"Details_{tool_number}.xlsx"))
        return summary_exists and details_exists
    
    def get_fail_reason(self) -> str:
        return "Vendor C requires both Summary.pdf and Details.xlsx in completed folder"


class VendorRuleRegistry:
    _rules = {
        'default': DefaultVendorRule(),
        'vendor_a': VendorARule(),
        'vendor_b': VendorBRule(),
        'vendor_c': VendorCRule(),
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