"""
Demonstration of project start date differences with and without Taiwan holiday exclusion.
"""

import pandas as pd
from datetime import datetime, timedelta
from outsourcing_qc_trans import OutsourcingQcTrans

def compare_holiday_impact():
    """Compare project start dates with and without Taiwan holiday exclusion."""

    print("=== Taiwan Holiday Impact on Project Start Dates ===\n")

    # Test cases with customer schedules that will show holiday impact
    test_cases = [
        {
            'Tool_Number': 'T001',
            'Project': 'Lunar_New_Year_Project',
            'Customer_Deadline': datetime(2025, 2, 10),
            'Description': 'After Lunar New Year holidays'
        },
        {
            'Tool_Number': 'T002',
            'Project': 'Labor_Day_Project',
            'Customer_Deadline': datetime(2025, 5, 15),
            'Description': 'After Labor Day'
        },
        {
            'Tool_Number': 'T003',
            'Project': 'National_Day_Project',
            'Customer_Deadline': datetime(2025, 10, 20),
            'Description': 'After National Day'
        }
    ]
    
    # Create business day calculators
    from taiwan_holidays import TaiwanBusinessDay
    bday_weekends_only = TaiwanBusinessDay(enable_holiday_checking=False)
    bday_with_holidays = TaiwanBusinessDay(enable_holiday_checking=True)

    print(">> WITHOUT Taiwan Holiday Exclusion (weekends only):")
    results_no_holidays = []

    for case in test_cases:
        customer_date = case['Customer_Deadline']
        start_date = bday_weekends_only.add_business_days(customer_date, -15)
        days_diff = (customer_date - start_date).days
        results_no_holidays.append({'case': case, 'start_date': start_date})
        print(f"  Tool {case['Tool_Number']}: Customer {customer_date.strftime('%Y-%m-%d')} -> Start {start_date.strftime('%Y-%m-%d')} ({days_diff} calendar days)")

    print("\n>> WITH Taiwan Holiday Exclusion:")
    results_with_holidays = []

    for case in test_cases:
        customer_date = case['Customer_Deadline']
        start_date = bday_with_holidays.add_business_days(customer_date, -15)
        days_diff = (customer_date - start_date).days
        results_with_holidays.append({'case': case, 'start_date': start_date})
        print(f"  Tool {case['Tool_Number']}: Customer {customer_date.strftime('%Y-%m-%d')} -> Start {start_date.strftime('%Y-%m-%d')} ({days_diff} calendar days)")
    
    print("\n=== Comparison Analysis ===")

    for i in range(len(test_cases)):
        case = test_cases[i]
        tool_num = case['Tool_Number']
        customer_date = case['Customer_Deadline']

        start_no_holidays = results_no_holidays[i]['start_date']
        start_with_holidays = results_with_holidays[i]['start_date']

        calendar_days_diff = (start_no_holidays - start_with_holidays).days

        print(f"\n>> Tool {tool_num} ({case['Description']} - Customer: {customer_date.strftime('%Y-%m-%d')}):")
        print(f"   - Without holidays: Start {start_no_holidays.strftime('%Y-%m-%d')}")
        print(f"   - With holidays:    Start {start_with_holidays.strftime('%Y-%m-%d')}")

        if calendar_days_diff > 0:
            print(f"   - Impact: Start date is {calendar_days_diff} days EARLIER with Taiwan holiday exclusion")
            print(f"   - Reason: Taiwan holidays require going back further to get 15 working days")
        elif calendar_days_diff < 0:
            print(f"   - Impact: Start date is {abs(calendar_days_diff)} days LATER with Taiwan holiday exclusion")
        else:
            print(f"   - Impact: No difference (no Taiwan holidays affecting this period)")

def show_specific_holiday_example():
    """Show a specific example during Lunar New Year period."""
    print("\n\n=== Specific Example: Lunar New Year Period ===")

    # Customer deadline during Lunar New Year period
    customer_deadline = datetime(2025, 2, 5)  # Right after LNY holidays

    print(f"Customer Deadline: {customer_deadline.strftime('%Y-%m-%d')} ({customer_deadline.strftime('%A')})")
    print("Lunar New Year 2025: Jan 28 - Feb 2 (estimated holiday period)")

    # Direct business day calculation
    from taiwan_holidays import TaiwanBusinessDay
    bday_weekends_only = TaiwanBusinessDay(enable_holiday_checking=False)
    bday_with_holidays = TaiwanBusinessDay(enable_holiday_checking=True)

    # Calculate 15 business days before deadline
    start_no_holidays = bday_weekends_only.add_business_days(customer_deadline, -15)
    start_with_holidays = bday_with_holidays.add_business_days(customer_deadline, -15)
    
    print(f"\n>> Project Start Dates:")
    print(f"   - Weekends only:     {start_no_holidays.strftime('%Y-%m-%d')} ({start_no_holidays.strftime('%A')})")
    print(f"   - Taiwan holidays:   {start_with_holidays.strftime('%Y-%m-%d')} ({start_with_holidays.strftime('%A')})")
    
    calendar_diff = (start_no_holidays - start_with_holidays).days
    if calendar_diff != 0:
        print(f"\n>> Impact: {abs(calendar_diff)} days difference!")
        print(f"   Taiwan holidays make project start {'earlier' if calendar_diff > 0 else 'later'}")
        print(f"   This gives teams {'more' if calendar_diff > 0 else 'less'} calendar time to complete work")

if __name__ == "__main__":
    try:
        compare_holiday_impact()
        show_specific_holiday_example()
        
        print("\n\n>> Key Takeaways:")
        print("   1. Taiwan holidays require EARLIER project start dates")
        print("   2. This ensures teams get exactly 15 working days despite holidays")
        print("   3. Critical for realistic project scheduling in Taiwan business environment")
        print("   4. Prevents missed deadlines due to holiday periods")
        
    except Exception as e:
        print(f"Demo error: {e}")
        print("Note: This demo requires network access for Taiwan holiday data.")
        print("Run with enable_taiwan_holidays=False if API is unavailable.")