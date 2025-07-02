import pandas as pd
from datetime import datetime, timedelta

class OutsourcingQcTrans:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_transformed_data(self) -> pd.DataFrame:
        """
        Filters and enriches the data.

        Returns:
            pd.DataFrame: The transformed data.
        """
        today = datetime.now()
        three_weeks_from_now = today + timedelta(weeks=3)

        filtered_df = self.df[
            (self.df["Customer schedule"] >= today)
            & (self.df["Customer schedule"] <= three_weeks_from_now)
        ].copy()

        filtered_df["Project Start Date"] = (
            filtered_df["Customer schedule"] - pd.DateOffset(weeks=3)
        )
        return filtered_df
