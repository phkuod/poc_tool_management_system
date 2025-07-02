import pandas as pd
from datetime import datetime, timedelta

class OutsourcingQcTrans:
    def __init__(self, df):
        self.df = df

    def get_transformed_data(self):
        """
        Filters and enriches the data.
        """
        today = datetime.now()
        three_weeks_later = today + timedelta(weeks=3)

        self.df['Customer schedule'] = pd.to_datetime(self.df['Customer schedule'])

        filtered_df = self.df[
            (self.df['Customer schedule'] >= today) &
            (self.df['Customer schedule'] <= three_weeks_later)
        ].copy()

        filtered_df['Project Start Date'] = filtered_df['Customer schedule'] - timedelta(weeks=3)

        return filtered_df