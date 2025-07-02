import argparse
import json
from outsourcing_qc_extractor import OutsourcingQcExtractor
from outsourcing_qc_trans import OutsourcingQcTrans
from outsourcing_qc_check_points import OutsourcingQcCheckPoints
from tool_management.notifier import email_notifier

def main():
    """
    Main function to run the outsourcing QC system.
    """
    parser = argparse.ArgumentParser(description="Outsourcing QC System")
    parser.add_argument("input_path", help="Path to the input Excel file")
    args = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)
    
    target_path = config.get("target_path")

    extractor = OutsourcingQcExtractor(args.input_path)
    raw_df = extractor.get_raw_data()

    transformer = OutsourcingQcTrans(raw_df)
    trans_df = transformer.get_transformed_data()

    checker = OutsourcingQcCheckPoints(trans_df, target_path)
    failures = checker.get_failures()

    if failures:
        email_notifier.send_notifications(failures)
    else:
        print("All checks passed successfully.")

if __name__ == "__main__":
    main()