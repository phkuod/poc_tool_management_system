"""
Simple demonstration of Taiwan business day calculation differences.
"""

from datetime import datetime
from taiwan_holidays import TaiwanBusinessDay

def demo_business_day_calculation():
    """Demonstrate the difference between weekends-only and Taiwan holiday exclusion."""

    print("=== Business Day Calculation Demo ===\n")

    # Test customer deadlines around known Taiwan holidays
    test_cases = [
        {
            'name': 'Lunar New Year Period',
            'customer_deadline': datetime(2025, 2, 5),  # After LNY
            'description': 'Customer deadline right after Lunar New Year holidays'
        },
        {
            'name': 'Labor Day Period',
            'customer_deadline': datetime(2025, 5, 5),  # After Labor Day
            'description': 'Customer deadline after Labor Day'
        },
        {
            'name': 'National Day Period',
            'customer_deadline': datetime(2025, 10, 13),  # After National Day
            'description': 'Customer deadline after National Day'
        }
    ]

    for case in test_cases:
        print(f">> {case['name']}:")
        print(f"   {case['description']}")
        print(f"   Customer Deadline: {case['customer_deadline'].strftime('%Y-%m-%d (%A)')}")

        # Calculate project start date (15 business days before customer deadline)

        # Without Taiwan holidays (weekends only)
        bday_weekends_only = TaiwanBusinessDay(enable_holiday_checking=False)
        start_weekends_only = bday_weekends_only.add_business_days(case['customer_deadline'], -15)

        # With Taiwan holidays
        bday_with_holidays = TaiwanBusinessDay(enable_holiday_checking=True)
        start_with_holidays = bday_with_holidays.add_business_days(case['customer_deadline'], -15)

        print(f"   Project Start (weekends only): {start_weekends_only.strftime('%Y-%m-%d (%A)')}")
        print(f"   Project Start (with holidays): {start_with_holidays.strftime('%Y-%m-%d (%A)')}")

        # Calculate the difference
        calendar_diff = (start_weekends_only - start_with_holidays).days

        if calendar_diff > 0:
            print(f"   Impact: Start date is {calendar_diff} days EARLIER with holiday exclusion")
            print(f"   Reason: Taiwan holidays require going back further in time")
        elif calendar_diff < 0:
            print(f"   Impact: Start date is {abs(calendar_diff)} days LATER with holiday exclusion")
        else:
            print(f"   Impact: No difference (no Taiwan holidays affecting this period)")

        print()

if __name__ == "__main__":
    try:
        demo_business_day_calculation()

        print(">> Key Insights:")
        print("   1. With Taiwan holidays excluded, project starts need to be earlier")
        print("   2. This gives teams the same number of working days despite holidays")
        print("   3. Critical for accurate project planning in Taiwan business environment")

    except Exception as e:
        print(f"Demo error: {e}")
        print("Note: This demo requires the taiwan_holidays module to be working.")