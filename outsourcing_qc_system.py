import argparse
import json
from outsourcing_qc_extractor import OutsourcingQcExtractor
from outsourcing_qc_trans import OutsourcingQcTrans
from outsourcing_qc_check_points import OutsourcingQcCheckPoints

def main():
    parser = argparse.ArgumentParser(description='Outsourcing QC System')
    parser.add_argument('input_path', help='Path to the input Excel file')
    args = parser.parse_args()

    try:
        extractor = OutsourcingQcExtractor(args.input_path)
        raw_df = extractor.get_raw_data()

        transformer = OutsourcingQcTrans(raw_df)
        trans_df = transformer.get_transformed_data()

        checker = OutsourcingQcCheckPoints(trans_df)
        failures = checker.get_failures()

        print(json.dumps(failures, indent=4))

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
