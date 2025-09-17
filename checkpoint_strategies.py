from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from vendor_rules import VendorRuleRegistry
from enhanced_vendor_rules import EnhancedVendorRuleRegistry


class CheckpointStrategy(ABC):
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


class PackageReadinessCheckpoint(CheckpointStrategy):
    def __init__(self):
        super().__init__("Package Readiness", priority=1)
    
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
                'Responsible User': row['Responsible User']
            }]
        return []


class FinalReportCheckpoint(CheckpointStrategy):
    def __init__(self):
        super().__init__("Final Report", priority=2)
    
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
                'Responsible User': row['Responsible User']
            }]
        
        # Execute vendor-specific check
        target_path = Path(f"Target/Path/{tool_column}")
        rule = VendorRuleRegistry.get_rule(vendor_key)
        
        if not rule.check_final_report(tool_column, tool_number, target_path):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Vendor': vendor_key,
                'Fail Reason': rule.get_fail_reason(),
                'Responsible User': row['Responsible User']
            }]
        return []
    
    def _get_vendor_key(self, row) -> str:
        """Get vendor key from row, validate it exists in registry, return None if invalid"""
        if 'Vendor' not in row or pd.isna(row['Vendor']):
            return None
        
        vendor_key = str(row['Vendor']).lower()
        
        # Check if vendor exists in registry
        if vendor_key not in VendorRuleRegistry.list_vendors():
            return None
            
        return vendor_key


class QualityAssuranceCheckpoint(CheckpointStrategy):
    def __init__(self):
        super().__init__("Quality Assurance", priority=3)
    
    def should_check(self, row: pd.Series, today: datetime) -> bool:
        return (row['Customer schedule'] - today).days <= 10
    
    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']
        qa_path = Path(f"Target/Path/{tool_column}/QA")
        
        if not any(qa_path.glob(f"QA_Report_{tool_number}.pdf")):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Fail Reason': 'QA report missing',
                'Responsible User': row['Responsible User']
            }]
        return []


class CustomerApprovalCheckpoint(CheckpointStrategy):
    def __init__(self):
        super().__init__("Customer Approval", priority=4)
    
    def should_check(self, row: pd.Series, today: datetime) -> bool:
        return (row['Customer schedule'] - today).days <= 3
    
    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']
        approval_path = Path(f"Target/Path/{tool_column}/Approvals")
        
        if not any(approval_path.glob(f"Customer_Approval_{tool_number}.*")):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Fail Reason': 'Customer approval missing',
                'Responsible User': row['Responsible User']
            }]
        return []


class DeliveryCheckpoint(CheckpointStrategy):
    def __init__(self):
        super().__init__("Delivery Confirmation", priority=5)
    
    def should_check(self, row: pd.Series, today: datetime) -> bool:
        return today >= row['Customer schedule']
    
    def execute_check(self, row: pd.Series, today: datetime) -> List[Dict[str, Any]]:
        tool_column = row['Tool Column']
        tool_number = row['Tool_Number']
        delivery_path = Path(f"Target/Path/{tool_column}/Delivered")
        
        if not any(delivery_path.glob(f"Delivery_Confirmation_{tool_number}.*")):
            return [{
                'Tool_Number': tool_number,
                'Project': tool_column,
                'Fail Reason': 'Delivery confirmation missing',
                'Responsible User': row['Responsible User']
            }]
        return []


class CheckpointRegistry:
    _checkpoints: List[CheckpointStrategy] = []
    
    @classmethod
    def register(cls, checkpoint: CheckpointStrategy):
        """Register a checkpoint strategy."""
        cls._checkpoints.append(checkpoint)
        cls._checkpoints.sort(key=lambda x: x.priority)
    
    @classmethod
    def unregister(cls, checkpoint_name: str):
        """Remove a checkpoint by name."""
        cls._checkpoints = [cp for cp in cls._checkpoints if cp.name != checkpoint_name]
    
    @classmethod
    def get_all_checkpoints(cls) -> List[CheckpointStrategy]:
        """Get all registered checkpoints sorted by priority."""
        return cls._checkpoints.copy()
    
    @classmethod
    def clear(cls):
        """Clear all registered checkpoints."""
        cls._checkpoints.clear()
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize with default checkpoints."""
        cls.clear()
        cls.register(PackageReadinessCheckpoint())
        cls.register(FinalReportCheckpoint())
        # Future checkpoints can be added here
        # cls.register(QualityAssuranceCheckpoint())
        # cls.register(CustomerApprovalCheckpoint())
        # cls.register(DeliveryCheckpoint())