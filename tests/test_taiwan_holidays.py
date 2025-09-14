import unittest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open
from taiwan_holidays import TaiwanHolidayFetcher, TaiwanBusinessDay


class TestTaiwanHolidayFetcher(unittest.TestCase):
    
    def setUp(self):
        self.fetcher = TaiwanHolidayFetcher(cache_dir="test_cache")
    
    def test_fallback_holidays_load(self):
        """Test loading holidays from fallback configuration."""
        mock_data = {
            "2025": [
                "2025-01-01",
                "2025-02-28",
                "2025-04-04"
            ]
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
            holidays = self.fetcher._get_from_fallback(2025)
            
        self.assertIsNotNone(holidays)
        self.assertEqual(len(holidays), 3)
        self.assertIn(datetime(2025, 1, 1), holidays)
        self.assertIn(datetime(2025, 2, 28), holidays)
        self.assertIn(datetime(2025, 4, 4), holidays)
    
    @patch('requests.get')
    def test_api_fetch_success(self, mock_get):
        """Test successful API fetch."""
        mock_response_data = [
            {"date": "2025-01-01", "isHoliday": True},
            {"date": "2025-01-02", "isHoliday": False},
            {"date": "2025-02-28", "isHoliday": True}
        ]
        mock_get.return_value.json.return_value = mock_response_data
        mock_get.return_value.raise_for_status.return_value = None
        
        holidays = self.fetcher._fetch_from_api(2025)
        
        self.assertIsNotNone(holidays)
        self.assertEqual(len(holidays), 2)  # Only holidays
        self.assertIn(datetime(2025, 1, 1), holidays)
        self.assertIn(datetime(2025, 2, 28), holidays)
    
    @patch('requests.get')
    def test_api_fetch_failure(self, mock_get):
        """Test API fetch failure handling."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        holidays = self.fetcher._fetch_from_api(2025)
        
        self.assertIsNone(holidays)


class TestTaiwanBusinessDay(unittest.TestCase):
    
    def setUp(self):
        self.taiwan_bday = TaiwanBusinessDay(enable_holiday_checking=False)
        self.taiwan_bday_with_holidays = TaiwanBusinessDay(enable_holiday_checking=True)
    
    def test_add_business_days_weekends_only(self):
        """Test adding business days excluding only weekends."""
        # Start on a Monday (2025-01-13)
        start_date = datetime(2025, 1, 13)  # Monday
        
        # Add 5 business days should give us next Monday (2025-01-20)
        result = self.taiwan_bday.add_business_days(start_date, 5)
        expected = datetime(2025, 1, 20)  # Next Monday
        
        self.assertEqual(result.date(), expected.date())
    
    def test_add_business_days_across_weekend(self):
        """Test adding business days that cross weekends."""
        # Start on a Friday (2025-01-10)
        start_date = datetime(2025, 1, 10)  # Friday
        
        # Add 3 business days should give us Wednesday (2025-01-15)
        result = self.taiwan_bday.add_business_days(start_date, 3)
        expected = datetime(2025, 1, 15)  # Wednesday
        
        self.assertEqual(result.date(), expected.date())
    
    def test_subtract_business_days(self):
        """Test subtracting business days."""
        # Start on a Friday (2025-01-17)
        start_date = datetime(2025, 1, 17)  # Friday
        
        # Subtract 5 business days should give us previous Friday (2025-01-10)
        result = self.taiwan_bday.add_business_days(start_date, -5)
        expected = datetime(2025, 1, 10)  # Previous Friday
        
        self.assertEqual(result.date(), expected.date())
    
    def test_get_business_days_between(self):
        """Test calculating business days between dates."""
        start_date = datetime(2025, 1, 13)  # Monday
        end_date = datetime(2025, 1, 20)    # Next Monday
        
        # Should be 5 business days between
        result = self.taiwan_bday.get_business_days_between(start_date, end_date)
        expected = 5
        
        self.assertEqual(result, expected)
    
    @patch.object(TaiwanBusinessDay, '_is_taiwan_holiday')
    def test_holiday_exclusion(self, mock_is_holiday):
        """Test that Taiwan holidays are properly excluded."""
        # Mock Tuesday (2025-01-14) as a holiday
        def mock_holiday_check(date):
            return date.date() == datetime(2025, 1, 14).date()
        
        mock_is_holiday.side_effect = mock_holiday_check
        
        # Start on Monday (2025-01-13)
        start_date = datetime(2025, 1, 13)
        
        # Add 2 business days, but Tuesday is holiday, so should get Thursday
        result = self.taiwan_bday_with_holidays.add_business_days(start_date, 2)
        expected = datetime(2025, 1, 16)  # Thursday (skipping holiday Tuesday)
        
        self.assertEqual(result.date(), expected.date())
    
    def test_edge_case_start_on_weekend(self):
        """Test starting calculation on a weekend."""
        # Start on Saturday (2025-01-11)
        start_date = datetime(2025, 1, 11)  # Saturday
        
        # Add 1 business day should give us Monday
        result = self.taiwan_bday.add_business_days(start_date, 1)
        expected = datetime(2025, 1, 13)  # Monday
        
        self.assertEqual(result.date(), expected.date())
    
    def test_fifteen_business_days(self):
        """Test the specific 15 business days calculation used in the system."""
        # Start on Monday (2025-01-13)
        start_date = datetime(2025, 1, 13)
        
        # Add 15 business days
        result = self.taiwan_bday.add_business_days(start_date, 15)
        
        # Manually count: 15 business days from Jan 13 should be Feb 3
        # Week 1: Jan 13-17 (5 days)
        # Week 2: Jan 20-24 (5 days) 
        # Week 3: Jan 27-31 (5 days)
        # Total: 15 days = Jan 31
        expected = datetime(2025, 2, 3)  # Monday
        
        self.assertEqual(result.date(), expected.date())


if __name__ == '__main__':
    unittest.main()