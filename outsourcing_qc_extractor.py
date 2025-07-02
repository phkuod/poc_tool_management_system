import pandas as pd

class OutsourcingQcExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.required_columns = [
            "Tool_Number",
            "Tool Column",
            "Customer schedule",
            "Responsible User",
        ]

    def get_raw_data(self) -> pd.DataFrame:
        """
        Loads and returns raw data from Excel.

        Returns:
            pd.DataFrame: The raw data from the Excel file.
        """
        df = pd.read_excel(self.file_path)
        self._validate_columns(df)
        df["Customer schedule"] = pd.to_datetime(
            df["Customer schedule"], errors="coerce"
        )
        return df

    def _validate_columns(self, df: pd.DataFrame):
        """
        Validates that the required columns exist in the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to validate.
        """
        missing_columns = [
            col for col in self.required_columns if col not in df.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

