import pandas as pd
from datetime import datetime
from pathlib import Path

class OutsourcingQcCheckPoints:
    def __init__(self, df):
        self.df = df
        self.today = datetime.now()
        self.failures = {}

    def get_failures(self):
        """
        Returns a dictionary of all failed rules.
        """
        self._check_package_readiness()
        self._check_final_report()
        return self.failures

    def _check_package_readiness(self):
        """
        Rule 1: Package Readiness
        Trigger: Today >= Project Start Date + 3 days
        Check path: /Target/Path/{Tool Column}/*Tool_Number*
        """
        rule_name = "Package Readiness"
        self.failures[rule_name] = []

        for index, row in self.df.iterrows():
            if self.today >= row['Project Start Date'] + pd.Timedelta(days=3):
                tool_column = row['Tool Column']
                tool_number = row['Tool_Number']
                target_path = Path(f"Target/Path/{tool_column}")
                
                if not any(target_path.glob(f"*{tool_number}*")):
                    self.failures[rule_name].append({
                        'Tool_Number': tool_number,
                        'Project': tool_column,
                        'Fail Reason': 'Package not found',
                        'Responsible User': row['Responsible User']
                    })

    def _check_final_report(self):
        """
        Rule 2: Final Report
        Trigger: Customer schedule - Today <= 7 days
        Check path: /Target/Path/{Tool Column}/Final_Report_*{Tool_Number}*.pdf
        """
        rule_name = "Final Report"
        self.failures[rule_name] = []

        for index, row in self.df.iterrows():
            if (row['Customer schedule'] - self.today).days <= 7:
                tool_column = row['Tool Column']
                tool_number = row['Tool_Number']
                target_path = Path(f"Target/Path/{tool_column}")

                if not any(target_path.glob(f"Final_Report_*{tool_number}*.pdf")):
                    self.failures[rule_name].append({
                        'Tool_Number': tool_number,
                        'Project': tool_column,
                        'Fail Reason': 'Final report not found',
                        'Responsible User': row['Responsible User']
                    })