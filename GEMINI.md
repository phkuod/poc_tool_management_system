# GEMINI.md — Python Outsourcing QC System

This file provides context and architectural guidance for the Gemini CLI assistant working on this project.

---

## 📌 Project Overview

- **Project Name:** outsourcing_qc_system  
- **Description:** A modular Python project to monitor outsourcing task schedules via Excel, validate checkpoints, and send email alerts if criteria are not met.  
- **Python Version:** 3.8+  
- **Core Technologies:**  
  - `pandas` for data handling  
  - `openpyxl` for Excel I/O  
  - `argparse` for CLI parsing  
  - `smtplib` or external mail API for notifications (configurable)

---

## 🧩 System Requirements

### 0. High-Level Monitoring & Alerting
- The system monitors project tasks scheduled in an Excel file.
- It applies multiple **checkpoint rules** to validate task readiness.
- If a checkpoint fails, the system generates a **grouped email notification** to remind responsible users.

---

### 1. Input Configuration
- **Input Format:** Excel `.xlsx` with columns:  
  - `Tool_Number`  
  - `Tool Column`  
  - `Customer schedule`  
  - `Responsible User`  
- **Input Path:** Passed as a CLI argument.  

---

### 2. Data Processing Pipeline

The source code must contain 3 modular components, each encapsulated in a class for scalability and testability.

---

#### 2.1 📥 Data Extraction
- **File:** `outsourcing_qc_extractor.py`  
- **Class:** `OutsourcingQcExtractor`  
- **Methods:**
  - `get_raw_data()` — loads and returns raw data from Excel.
- **Details:**  
  - Validates required columns exist.
  - Handles date parsing and basic cleanup.

---

#### 2.2 🔄 Data Transformation
- **File:** `outsourcing_qc_trans.py`  
- **Class:** `OutsourcingQcTrans`  
- **Methods:**
  - `get_transformed_data()` — filters and enriches data.
- **Processing Logic:**
  - Keep rows where:  
    `Today ≤ Customer schedule ≤ Today + 3 weeks`  
  - Add new column:  
    `Project Start Date = Customer schedule – 3 weeks`

---

#### 2.3 ✅ Checkpoint Rule Executor
- **File:** `outsourcing_qc_check_points.py`  
- **Class:** `OutsourcingQcCheckPoints`  
- **Methods:**
  - `get_failures()` — returns a dictionary or DataFrame of all failed rules.
- **Rules:**
  - **Rule 1: Package Readiness**
    - Trigger: `Today ≥ Project Start Date + 3 days`
    - Check path: `/Target/Path/{Tool Column}/*Tool_Number*`
  - **Rule 2: Final Report**
    - Trigger: `Customer schedule - Today ≤ 7 days`
    - Check path: `/Target/Path/{Tool Column}/Final_Report_*{Tool_Number}*.pdf`

---

### 3. Orchestration and Main Entry

- **File:** `outsourcing_qc_system.py`
- **Functionality:**  
  - Uses `argparse` to receive input path.
  - Runs the pipeline:
    ```python
    extractor = OutsourcingQcExtractor(input_path)
    raw_df = extractor.get_raw_data()

    transformer = OutsourcingQcTrans(raw_df)
    trans_df = transformer.get_transformed_data()

    checker = OutsourcingQcCheckPoints(trans_df)
    failures = checker.get_failures()
    ```
  - Outputs final results (e.g., logs, prints, or JSON output for email pipeline)

---

### 4. Notification

- **Grouping:** Failed items are grouped by checkpoint.
- **Method:** Output used by notifier class or CLI script to send emails.
- **Structure:**  
  - `Tool_Number`, `Project`, `Fail Reason`, `Responsible User`
- **Configurable:** SMTP server and sender address loaded via `.env` or `config.json`.

---

## 🛠 Architectural Goals

- **Modular**: Individual files for extractor, transformer, checkpoint logic, and main system controller.
- **Scalable**: Easily extend with new checkpoints or input types.
- **Testable**: Each class has unit test coverage.
- **Safe**: Use pathlib, assert column existence, and validate paths before filesystem operations.

---

## 🧪 Testing Strategy

- Each core module has a corresponding test file in `tests/`
- Test classes:
  - `TestOutsourcingQcExtractor`
  - `TestOutsourcingQcTrans`
  - `TestOutsourcingQcCheckPoints`
- Coverage goal: ≥ 90% using `pytest` + `coverage`
- Optional mocking of filesystem checks and SMTP sending

---

## 🔧 Project Layout

```
.
├── outsourcing_qc_extractor.py       # Raw Excel loader
├── outsourcing_qc_trans.py           # Data transformation logic
├── outsourcing_qc_check_points.py    # Checkpoint execution logic
├── outsourcing_qc_system.py          # Main orchestrator
├── notifier/                         # (optional) Email handler module
├── tests/                            # Unit tests for each module
│   ├── test_extractor.py
│   ├── test_trans.py
│   ├── test_checkpoints.py
├── config.json
├── .env.example
├── requirements.txt
└── GEMINI.md
```

---

## ⚙️ Commands

```bash
# Run system
python outsourcing_qc_system.py path/to/schedule.xlsx

# Test
pytest tests/

# Format & lint
ruff format .
ruff check .
```

---

## 🧠 Memory & Conventions

- Date columns must be parsed with `pd.to_datetime()`, raise if invalid.
- Always perform **sanity checks** after loading raw data:
  - Required columns exist
  - Dates are valid and logical
- Use pathlib, not raw string joins for paths.
- External paths should be relative or loaded from `config.json`.
