# Deduplication Service

Silver Zone Deduplication Service for the AI-Driven Financial Data Analysis & Market Impact Prediction Platform.

## Overview

Flask-based API that executes deduplication rules on financial records using **pair-wise comparison**. Supports both single-rule and multi-rule payloads.

## Features

- **5 Deduplication Rules** (DR_001 to DR_005)
- **Pair-Wise Comparison** — two records at a time
- **Dynamic Rule Loading** from MySQL
- **Multi-Rule Support** — run multiple rules on the same pair
- **Execution Logging** to `deduplication_logic_logs`
- **Quarantine Support** — stores duplicate metadata

## Deduplication Rules

| Code | Rule Name | Category | Detects |
|---|---|---|---|
| DR_001 | Exact Composite Key | Exact Match | Same key fields |
| DR_002 | Fuzzy Token Ratio | Fuzzy Match | Similar strings (>= threshold) |
| DR_003 | Numerical Tolerance | Numeric Match | Values within tolerance |
| DR_004 | Whitespace Normalized | Normalized Match | Formatting differences |
| DR_005 | All Fields Exact | Exact Match | Every field matches |

## Setup

### 1. Install Dependencies
\\\ash
pip install -r requirements.txt
\\\

### 2. Configure Environment
\\\ash
copy .env.example .env
# Edit .env with your MySQL credentials
\\\

### 3. Initialize Database
\\\ash
mysql -u root -p1234 < deduplication.sql
mysql -u root -p1234 deduplication_db < seed_rules.sql
\\\

### 4. Run the Service
\\\ash
uvicorn asgi:app --reload --port 8000
\\\

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health/db` | Database health check |
| POST | `/api/v1/deduplicate/execute` | Execute deduplication |

## Usage Examples

### Single Rule (Legacy)

\\\json
POST http://127.0.0.1:8000/api/v1/deduplicate/execute

{
  "request_id": "DEDUP-001",
  "rule_id": "DR_001",
  "config": {
    "key_fields": ["Year", "Revenue (\)"]
  },
  "record1": {"Year": 2004, "Revenue (\)": 19.06},
  "record2": {"Year": 2004, "Revenue (\)": 19.06}
}
\\\

### Multiple Rules

\\\json
POST http://127.0.0.1:8000/api/v1/deduplicate/execute

{
  "request_id": "DEDUP-002",
  "rule_ids": ["DR_001", "DR_004", "DR_005"],
  "records": [
    {"Year": 2004, "Revenue (\)": 19.06, "Earnings (\)": 3.2},
    {"Year": 2004, "Revenue (\)": 19.06, "Earnings (\)": 3.2}
  ],
  "config": {
    "DR_001": {"key_fields": ["Year", "Revenue (\)"]},
    "DR_004": {"key_fields": ["Year", "Revenue (\)"]},
    "DR_005": {"exclude_fields": []}
  }
}
\\\

## Response Format

\\\json
{
  "success": true,
  "request_id": "DEDUP-002",
  "records_count": 2,
  "rule_ids": ["DR_001", "DR_004", "DR_005"],
  "results": [
    {"rule_id": "DR_001", "is_duplicate": true},
    {"rule_id": "DR_004", "is_duplicate": true},
    {"rule_id": "DR_005", "is_duplicate": true}
  ],
  "overall_is_duplicate": true,
  "matched_rules": ["DR_001", "DR_004", "DR_005"]
}
\\\

## Project Structure

\\\
Deduplication-Service/
├── app.py
├── asgi.py
├── database.py
├── deduplication.sql
├── seed_rules.sql
├── requirements.txt
├── .env.example
├── .gitignore
└── deduplication_rules/
    ├── registry.py
    ├── base/base_dedup_rule.py
    ├── resolutions/
    │   ├── keep_first.py
    │   └── merge_coalesce.py
    └── rules/
        ├── DR_001_exact_composite_key.py
        ├── DR_002_fuzzy_token_ratio.py
        ├── DR_003_numerical_tolerance.py
        ├── DR_004_whitespace_normalized.py
        └── DR_005_all_fields_exact.py
\\\

## License

Academic Project — University of Colombo School of Computing
