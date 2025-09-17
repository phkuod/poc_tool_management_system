"""
Clean demonstration of Taiwan holiday impact on project scheduling.
"""

import pandas as pd
from datetime import datetime, timedelta
from taiwan_holidays import TaiwanBusinessDay

def demo_taiwan_holiday_impact():
    """Demonstrate Taiwan holiday impact with clear examples."""

    print("=== Taiwan Holiday Impact on Project Scheduling ===\n")

    # Create business day calculators
    bday_weekends_only = TaiwanBusinessDay(enable_holiday_checking=False)
    bday_with_holidays = TaiwanBusinessDay(enable_holiday_checking=True)

    # Test cases with known Taiwan holidays
    test_cases = [
        {
            'name': 'Lunar New Year Impact',
            'customer_deadline': datetime(2025, 2, 10),
            'description': 'Project due after Lunar New Year holidays'
        },
        {
            'name': 'Labor Day Impact',
            'customer_deadline': datetime(2025, 5, 15),
            'description': 'Project due after Labor Day'
        },
        {
            'name': 'National Day Impact',
            'customer_deadline': datetime(2025, 10, 20),
            'description': 'Project due after National Day'
        }
    ]

    print("Calculating project start dates (15 business days before deadline):\n")

    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Description: {case['description']}")
        print(f"   Customer Deadline: {case['customer_deadline'].strftime('%Y-%m-%d (%A)')}")

        try:
            # Calculate start dates
            start_weekends = bday_weekends_only.add_business_days(case['customer_deadline'], -15)
            start_holidays = bday_with_holidays.add_business_days(case['customer_deadline'], -15)

            print(f"   Start (weekends only):  {start_weekends.strftime('%Y-%m-%d (%A)')}")
            print(f"   Start (with holidays):  {start_holidays.strftime('%Y-%m-%d (%A)')}")

            # Calculate difference
            diff_days = (start_weekends - start_holidays).days

            if diff_days > 0:
                print(f"   >> Impact: {diff_days} days EARLIER start with Taiwan holidays")
                print(f"   >> Reason: Need extra time to account for holiday non-working days")
            elif diff_days < 0:
                print(f"   >> Impact: {abs(diff_days)} days LATER start with Taiwan holidays")
            else:
                print(f"   >> Impact: No difference (no holidays in this period)")

        except Exception as e:
            print(f"   Error calculating dates: {e}")

        print()

    # Summary
    print(">> Key Takeaways:")
    print("   1. Taiwan holidays require EARLIER project start dates")
    print("   2. This ensures teams have 15 actual working days")
    print("   3. Critical for realistic project planning in Taiwan")
    print("   4. Helps avoid missed deadlines due to holiday periods")

def demo_simple_calculation():
    """Simple calculation demo without complex data structures."""

    print("\n\n=== Simple Business Day Calculation ===\n")

    # Pick a specific date after Lunar New Year
    deadline = datetime(2025, 2, 5)  # Wednesday after LNY

    print(f"Customer Deadline: {deadline.strftime('%Y-%m-%d (%A)')}")
    print("Need to start 15 business days before deadline\n")

    # Method 1: Weekends only
    bday_simple = TaiwanBusinessDay(enable_holiday_checking=False)
    start_simple = bday_simple.add_business_days(deadline, -15)

    # Method 2: Taiwan holidays included
    bday_taiwan = TaiwanBusinessDay(enable_holiday_checking=True)
    start_taiwan = bday_taiwan.add_business_days(deadline, -15)

    print(f"Method 1 (weekends only): Start {start_simple.strftime('%Y-%m-%d (%A)')}")
    print(f"Method 2 (Taiwan holidays): Start {start_taiwan.strftime('%Y-%m-%d (%A)')}")

    diff = (start_simple - start_taiwan).days
    print(f"\nDifference: {diff} days")

    if diff > 0:
        print(f"Taiwan holiday method starts {diff} days EARLIER")
        print("This accounts for Lunar New Year holidays in the calculation period")

if __name__ == "__main__":
    try:
        demo_taiwan_holiday_impact()
        demo_simple_calculation()

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure taiwan_holidays.py is available")
    except Exception as e:
        print(f"Demo error: {e}")
        print("Check that the Taiwan holiday API is accessible")