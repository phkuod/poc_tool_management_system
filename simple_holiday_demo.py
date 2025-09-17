"""
Simple demonstration of project start date differences with/without Taiwan holidays.
"""

import pandas as pd
from datetime import datetime
from outsourcing_qc_trans import OutsourcingQcTrans

def simple_comparison():
    """Compare project start dates with and without Taiwan holiday exclusion."""
    
    # Sample data with customer schedule after Lunar New Year 2025
    sample_data = pd.DataFrame({
        'Tool_Number': ['T001'],
        'Tool Column': ['Project_A'],
        'Customer schedule': [datetime(2025, 2, 10)],  # After LNY holidays
        'Responsible User': ['Alice']
    })
    
    print("Taiwan Holiday Impact Comparison")
    print("=" * 40)
    print(f"Customer Deadline: 2025-02-10 (Monday)")
    print(f"Lunar New Year: 2025-01-27 to 2025-01-31 (5 holidays)")
    print()
    
    # Without Taiwan holidays (weekends only)
    print("WITHOUT Taiwan Holidays (weekends only):")
    transformer_no = OutsourcingQcTrans(sample_data.copy(), enable_taiwan_holidays=False)
    result_no = transformer_no.get_transformed_data()
    start_no = result_no.iloc[0]['Project Start Date']
    calendar_days_no = (result_no.iloc[0]['Customer schedule'] - start_no).days
    print(f"  Project Start: {start_no.strftime('%Y-%m-%d')} ({start_no.strftime('%A')})")
    print(f"  Calendar days: {calendar_days_no} days")
    print()
    
    # With Taiwan holidays
    print("WITH Taiwan Holidays:")
    transformer_yes = OutsourcingQcTrans(sample_data.copy(), enable_taiwan_holidays=True)
    result_yes = transformer_yes.get_transformed_data()
    start_yes = result_yes.iloc[0]['Project Start Date']
    calendar_days_yes = (result_yes.iloc[0]['Customer schedule'] - start_yes).days
    print(f"  Project Start: {start_yes.strftime('%Y-%m-%d')} ({start_yes.strftime('%A')})")
    print(f"  Calendar days: {calendar_days_yes} days")
    print()
    
    # Show difference
    calendar_diff = calendar_days_yes - calendar_days_no
    date_diff = (start_no - start_yes).days
    
    print("IMPACT ANALYSIS:")
    print(f"  Difference: {calendar_diff} more calendar days when holidays excluded")
    print(f"  Start date: {abs(date_diff)} days {'earlier' if date_diff > 0 else 'later'} with holidays")
    print()
    print("WHY THIS MATTERS:")
    print("  - More accurate business day calculations")
    print("  - Better project planning in Taiwan environment")  
    print("  - Teams get proper calendar time including holidays")

if __name__ == "__main__":
    try:
        simple_comparison()
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This demo may require network access for Taiwan holiday data.")
        print("The system will fall back to local holiday configuration if API fails.")