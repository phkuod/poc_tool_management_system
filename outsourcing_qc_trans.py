import pandas as pd
from datetime import datetime, timedelta
from taiwan_holidays import TaiwanBusinessDay

class OutsourcingQcTrans:
    def __init__(self, df, enable_taiwan_holidays: bool = True):
        self.df = df
        self.taiwan_bday = TaiwanBusinessDay(enable_holiday_checking=enable_taiwan_holidays)

    def get_transformed_data(self):
        """
        Filters and enriches the data for next 15 working days (excluding Taiwan holidays).
        """
        today = datetime.now()
        fifteen_bdays_later = self.taiwan_bday.add_business_days(today, 15)

        self.df['Customer schedule'] = pd.to_datetime(self.df['Customer schedule'])

        filtered_df = self.df[
            (self.df['Customer schedule'] >= today) &
            (self.df['Customer schedule'] <= fifteen_bdays_later)
        ].copy()

        # Calculate project start dates using Taiwan business days
        filtered_df = filtered_df.copy()
        filtered_df['Project Start Date'] = filtered_df['Customer schedule'].apply(
            lambda date: self.taiwan_bday.add_business_days(date, -15)
        )

        return filtered_df