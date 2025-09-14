# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
python outsourcing_qc_system.py <input_path>
```
The system processes Excel files containing tool management data with required columns: Tool_Number, Tool Column, Customer schedule, Responsible User.

### Testing
```bash
python -m unittest discover tests/
```
Tests use Python's built-in unittest framework. Each test file follows the `test_*.py` naming convention.

### Running Individual Tests
```bash
python -m unittest tests.test_extractor
python -m unittest tests.test_trans
python -m unittest tests.test_checkpoints
```

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```
Core dependencies: pandas, openpyxl, requests

### Taiwan Holiday Support
The system automatically excludes Taiwan public holidays when calculating business days:
- **Primary source**: Taiwan calendar API (api.pin-yi.me/taiwan-calendar)
- **Fallback**: Local holiday configuration (`config/taiwan_holidays_fallback.json`)
- **Cache**: Downloaded holidays cached locally for offline use
- **Disable**: Set `enable_taiwan_holidays=False` to use weekends-only calculation

## Architecture

### Core Processing Pipeline
The system implements a three-stage data processing pipeline:

1. **Extraction** (`OutsourcingQcExtractor`): Loads Excel data and validates required columns
2. **Transformation** (`OutsourcingQcTrans`): Filters data for next 15 working days (excluding Taiwan holidays) and enriches with calculated dates
3. **Check Points** (`OutsourcingQcCheckPoints`): Validates business rules and identifies failures

### Business Rules Engine
Two main validation rules:
- **Package Readiness**: Checks if tool packages exist 3+ days after project start
- **Final Report**: Checks if final reports exist within 7 days of customer deadline

Both rules check file existence in target paths using glob patterns.

### Configuration
- `config.json`: Contains target path configuration
- Singleton logger (`SystemLogger`) with rotating file handler
- Email notifications via environment variables (SENDER_EMAIL, SMTP_SERVER, SMTP_PORT)

### Module Structure
- Root level: Main processing modules (`outsourcing_qc_*.py`)
- `tool_management/`: Package structure with notifier and utilities
- `tests/`: Unit tests with conftest.py for path setup
- `logs/`: Runtime logs with rotation

### Data Flow
Excel Input → Raw DataFrame → Filtered & Enriched Data → Rule Validation → JSON Failures Output → Optional Email Notifications

The system is designed for automated quality control of outsourcing tool management with file-based validation and email alerting.