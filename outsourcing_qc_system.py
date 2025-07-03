import argparse
import json
from outsourcing_qc_extractor import OutsourcingQcExtractor
from outsourcing_qc_trans import OutsourcingQcTrans
from outsourcing_qc_check_points import OutsourcingQcCheckPoints
from outsourcing_qc_system_logger import SystemLogger

def main():
    logger = SystemLogger().get_logger()
    logger.info("Starting Outsourcing QC System")

    parser = argparse.ArgumentParser(description='Outsourcing QC System')
    parser.add_argument('input_path', help='Path to the input Excel file')
    args = parser.parse_args()

    try:
        logger.info(f"Loading data from {args.input_path}")
        extractor = OutsourcingQcExtractor(args.input_path)
        raw_df = extractor.get_raw_data()
        logger.info(f"Successfully loaded {len(raw_df)} rows of raw data.")

        logger.info("Transforming data.")
        transformer = OutsourcingQcTrans(raw_df)
        trans_df = transformer.get_transformed_data()
        logger.info(f"Successfully transformed data. {len(trans_df)} rows remaining after filtering.")

        logger.info("Checking for failures.")
        checker = OutsourcingQcCheckPoints(trans_df)
        failures = checker.get_failures()
        logger.info("Successfully checked for failures.")

        print(json.dumps(failures, indent=4))
        logger.info("System run completed successfully.")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
