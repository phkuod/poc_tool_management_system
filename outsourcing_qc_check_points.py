import pandas as pd
from datetime import datetime
import glob
import os
from typing import List, Dict, Any

class OutsourcingQcCheckPoints:
    def __init__(self, df: pd.DataFrame, target_path: str):
        self.df = df
        self.target_path = target_path
        self.failures = []

    def get_failures(self) -> List[Dict[str, Any]]:
        """
        Runs all checkpoint rules and returns a list of failures.

        Returns:
            List[Dict[str, Any]]: A list of all failed rules.
        """
        self._check_package_readiness()
        self._check_final_report()
        return self.failures

    def _check_package_readiness(self):
        """
        Rule 1: Package Readiness
        - Trigger: Today >= Project Start Date + 3 days
        - Check path: /Target/Path/{Tool Column}/*Tool_Number*
        """
        today = datetime.now()
        for _, row in self.df.iterrows():
            if today >= row["Project Start Date"] + pd.Timedelta(days=3):
                tool_number = row["Tool_Number"]
                tool_column = row["Tool Column"]
                expected_path = os.path.join(
                    self.target_path, tool_column, f"*{tool_number}*"
                )
                if not glob.glob(expected_path):
                    self.failures.append(
                        {
                            "Tool_Number": tool_number,
                            "Project": tool_column,
                            "Fail Reason": "Package Readiness Check Failed",
                            "Responsible User": row["Responsible User"],
                        }
                    )

    def _check_final_report(self):
        """
        Rule 2: Final Report
        - Trigger: Customer schedule - Today <= 7 days
        - Check path: /Target/Path/{Tool Column}/Final_Report_*{Tool_Number}*.pdf
        """
        today = datetime.now()
        for _, row in self.df.iterrows():
            if (row["Customer schedule"] - today).days <= 7:
                tool_number = row["Tool_Number"]
                tool_column = row["Tool Column"]
                expected_path = os.path.join(
                    self.target_path,
                    tool_column,
                    f"Final_Report_*{tool_number}*.pdf",
                )
                if not glob.glob(expected_path):
                    self.failures.append(
                        {
                            "Tool_Number": tool_number,
                            "Project": tool_column,
                            "Fail Reason": "Final Report Check Failed",
                            "Responsible User": row["Responsible User"],
                        }
                    )
