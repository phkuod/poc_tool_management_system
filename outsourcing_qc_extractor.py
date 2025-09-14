import pandas as pd

class OutsourcingQcExtractor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.required_columns = [
            'Tool_Number',
            'Tool Column', 
            'Customer schedule',
            'Responsible User',
            'Vendor'
        ]

    def get_raw_data(self):
        """
        Loads and returns raw data from Excel.
        """
        try:
            df = pd.read_excel(self.input_path)
            self._validate_columns(df)
            return df
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise Exception(f"An error occurred while reading the Excel file: {e}")

    def _validate_columns(self, df):
        """
        Validates that the required columns exist in the DataFrame.
        """
        missing_columns = [
            col for col in self.required_columns if col not in df.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")