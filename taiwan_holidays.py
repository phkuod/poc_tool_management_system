"""
Taiwan Holiday Management Module

Provides functionality to fetch Taiwan public holidays from various sources
with fallback mechanisms for reliable business day calculations.
"""

import json
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class TaiwanHolidayFetcher:
    """Fetches Taiwan holidays from multiple sources with fallback support."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.api_url = "https://api.pin-yi.me/taiwan-calendar"
        self.cache_file = self.cache_dir / "taiwan_holidays.json"
        self.fallback_file = Path("config") / "taiwan_holidays_fallback.json"
        
    def get_holidays(self, year: int) -> Set[datetime]:
        """
        Get Taiwan holidays for a specific year.
        
        Args:
            year: The year to get holidays for
            
        Returns:
            Set of datetime objects representing holidays
        """
        try:
            # Try to get from cache first
            holidays = self._get_from_cache(year)
            if holidays:
                logger.info(f"Loaded Taiwan holidays for {year} from cache")
                return holidays
                
            # Try to fetch from API
            holidays = self._fetch_from_api(year)
            if holidays:
                self._save_to_cache(year, holidays)
                logger.info(f"Fetched Taiwan holidays for {year} from API")
                return holidays
                
            # Fall back to local configuration
            holidays = self._get_from_fallback(year)
            if holidays:
                logger.warning(f"Using fallback Taiwan holidays for {year}")
                return holidays
                
            logger.error(f"No holiday data available for {year}")
            return set()
            
        except Exception as e:
            logger.error(f"Error getting Taiwan holidays for {year}: {e}")
            return self._get_from_fallback(year) or set()
    
    def _fetch_from_api(self, year: int) -> Optional[Set[datetime]]:
        """Fetch holidays from Taiwan calendar API."""
        try:
            url = f"{self.api_url}/{year}/?isHoliday=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            holidays = set()
            
            for item in data:
                if item.get('isHoliday', False):
                    date_str = item.get('date')
                    if date_str:
                        holiday_date = datetime.strptime(date_str, '%Y-%m-%d')
                        holidays.add(holiday_date)
            
            return holidays
            
        except requests.RequestException as e:
            logger.warning(f"API request failed: {e}")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"API response parsing failed: {e}")
            return None
    
    def _get_from_cache(self, year: int) -> Optional[Set[datetime]]:
        """Get holidays from local cache."""
        try:
            if not self.cache_file.exists():
                return None
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is recent (within 30 days)
            cache_timestamp = cache_data.get('timestamp')
            if cache_timestamp:
                cache_date = datetime.fromisoformat(cache_timestamp)
                if (datetime.now() - cache_date).days > 30:
                    logger.info("Cache is older than 30 days, will refresh")
                    return None
            
            year_data = cache_data.get('holidays', {}).get(str(year), [])
            holidays = set()
            for date_str in year_data:
                holidays.add(datetime.strptime(date_str, '%Y-%m-%d'))
            
            return holidays if holidays else None
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Cache read failed: {e}")
            return None
    
    def _save_to_cache(self, year: int, holidays: Set[datetime]):
        """Save holidays to local cache."""
        try:
            cache_data = {'timestamp': datetime.now().isoformat(), 'holidays': {}}
            
            # Load existing cache if available
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        cache_data['holidays'] = existing_data.get('holidays', {})
                except:
                    pass  # Use empty cache on read error
            
            # Add new year data
            cache_data['holidays'][str(year)] = [
                holiday.strftime('%Y-%m-%d') for holiday in holidays
            ]
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def _get_from_fallback(self, year: int) -> Optional[Set[datetime]]:
        """Get holidays from fallback configuration file."""
        try:
            if not self.fallback_file.exists():
                return None
                
            with open(self.fallback_file, 'r', encoding='utf-8') as f:
                fallback_data = json.load(f)
            
            year_data = fallback_data.get(str(year), [])
            holidays = set()
            for date_str in year_data:
                holidays.add(datetime.strptime(date_str, '%Y-%m-%d'))
            
            return holidays if holidays else None
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Fallback read failed: {e}")
            return None


class TaiwanBusinessDay:
    """Taiwan-aware business day calculator."""
    
    def __init__(self, enable_holiday_checking: bool = True):
        self.enable_holiday_checking = enable_holiday_checking
        self.holiday_fetcher = TaiwanHolidayFetcher() if enable_holiday_checking else None
        self._holiday_cache = {}
        
    def add_business_days(self, start_date: datetime, num_days: int) -> datetime:
        """
        Add business days to a date, excluding weekends and Taiwan holidays.
        
        Args:
            start_date: Starting date
            num_days: Number of business days to add
            
        Returns:
            Date after adding business days
        """
        if not self.enable_holiday_checking:
            # Fall back to pandas BDay if holiday checking disabled
            return start_date + pd.tseries.offsets.BDay(num_days)
        
        current_date = start_date
        days_added = 0
        
        while days_added < num_days:
            current_date += timedelta(days=1)
            
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
                
            # Skip Taiwan holidays
            if self._is_taiwan_holiday(current_date):
                continue
                
            days_added += 1
        
        return current_date
    
    def get_business_days_between(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calculate number of business days between two dates.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of business days
        """
        if not self.enable_holiday_checking:
            # Fall back to pandas BDay if holiday checking disabled
            return len(pd.bdate_range(start_date, end_date)) - 1
        
        business_days = 0
        current_date = start_date
        
        while current_date < end_date:
            current_date += timedelta(days=1)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
                
            # Skip Taiwan holidays
            if self._is_taiwan_holiday(current_date):
                continue
                
            business_days += 1
        
        return business_days
    
    def _is_taiwan_holiday(self, date: datetime) -> bool:
        """Check if a date is a Taiwan holiday."""
        if not self.holiday_fetcher:
            return False
            
        year = date.year
        
        # Get holidays for this year (cached)
        if year not in self._holiday_cache:
            self._holiday_cache[year] = self.holiday_fetcher.get_holidays(year)
        
        holidays = self._holiday_cache[year]
        
        # Check if date (ignoring time) is in holidays
        date_only = datetime(date.year, date.month, date.day)
        return date_only in holidays