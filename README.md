# Deduplication Service

Silver Zone Deduplication Service for the AI-Driven Financial Data Analysis & Market Impact Prediction Platform.

## Overview

Flask-based API that compares financial records pair by pair. It supports single-rule execution, multi-rule execution, validation-compatible routes, batch requests, and execution logs.

## Features

- Five deduplication rules: `DR_001` through `DR_005`
- Pair-wise comparison of two records
- Rule metadata from MySQL with a local registry fallback
- Single-rule and multi-rule execution
- Execution logging in `deduplication_logic_logs`
- Validation-compatible API routes

## Deduplication Rules

| Code | Rule Name | Category | Detects |
|---|---|---|---|
| `DR_001` | Exact Composite Key | Exact Match | Matching configured key fields |
| `DR_002` | Fuzzy Token Ratio | Fuzzy Match | Similar text values above a threshold |
| `DR_003` | Numerical Tolerance | Numeric Match | Numeric values within a tolerance |
| `DR_004` | Whitespace Normalized | Normalized Match | Values that differ only in formatting |
| `DR_005` | All Fields Exact | Exact Match | Records with matching fields |

## Requirements

- Python 3.10 or later
- MySQL 8 or compatible MySQL server
- A database created using `deduplication.sql`

## Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the supplied template and update the MySQL settings:

```powershell
copy .env.example .env
```

The service uses these environment variables:

| Variable | Default | Description |
|---|---|---|
| `MYSQL_HOST` | `127.0.0.1` | MySQL host |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | MySQL user |
| `MYSQL_PASSWORD` | `1234` | MySQL password |
| `MYSQL_DATABASE` | `deduplication_db` | Database name |
| `MYSQL_CONNECTION_TIMEOUT` | `5` | Connection timeout in seconds |

### 3. Initialize the Database

Run the schema and seed scripts from the project directory:

```powershell
mysql -u root -p1234 < deduplication.sql
mysql -u root -p1234 deduplication_db < seed_rules.sql
```

### 4. Run the Service

```powershell
uvicorn asgi:app --reload --port 8000
```

The service is available at `http://127.0.0.1:8000`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service and database health check |
| `GET` | `/health/db` | Database health check |
| `POST` | `/api/v1/deduplicate/execute` | Execute deduplication |
| `GET` | `/api/v1/validation/rules` | List available validation rules |
| `GET` | `/api/v1/validation/rules/{rule_id}` | Get validation rule metadata |
| `POST` | `/api/v1/validation/execute` | Execute one validation request |
| `POST` | `/api/v1/validation/batch` | Execute multiple validation requests |
| `GET` | `/api/v1/validation/logs` | List recent validation executions |

## Validation API Examples

All POST requests require the header:

```text
Content-Type: application/json
```

### Health

```http
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/health/db
```

### List Rules

```http
GET http://127.0.0.1:8000/api/v1/validation/rules
GET http://127.0.0.1:8000/api/v1/validation/rules/DR_001
```

### Execute One Rule

```http
POST http://127.0.0.1:8000/api/v1/validation/execute
```

```json
{
  "request_id": "VAL-001",
  "rule_id": "DR_001",
  "config": {
    "key_fields": ["Year", "Revenue ($B)"]
  },
  "record1": {
    "Year": 2004,
    "Revenue ($B)": 19.06
  },
  "record2": {
    "Year": 2004,
    "Revenue ($B)": 19.06
  }
}
```

### Execute Multiple Rules

```http
POST http://127.0.0.1:8000/api/v1/validation/execute
```

```json
{
  "request_id": "VAL-002",
  "rule_ids": ["DR_001", "DR_004", "DR_005"],
  "records": [
    {
      "Year": 2004,
      "Revenue ($B)": 19.06,
      "Earnings ($B)": 3.2
    },
    {
      "Year": 2004,
      "Revenue ($B)": 19.06,
      "Earnings ($B)": 3.2
    }
  ],
  "config": {
    "DR_001": {
      "key_fields": ["Year", "Revenue ($B)"]
    },
    "DR_004": {
      "key_fields": ["Year", "Revenue ($B)"]
    },
    "DR_005": {
      "exclude_fields": []
    }
  }
}
```

### Batch Validation

The batch endpoint accepts a `requests` array. Each item uses the same format as the execute endpoint.

```http
POST http://127.0.0.1:8000/api/v1/validation/batch
```

```json
{
  "requests": [
    {
      "request_id": "VAL-BATCH-001",
      "rule_id": "DR_001",
      "config": {
        "key_fields": ["Year"]
      },
      "record1": {"Year": 2024},
      "record2": {"Year": 2024}
    },
    {
      "request_id": "VAL-BATCH-002",
      "rule_id": "DR_003",
      "config": {
        "field": "Revenue ($B)",
        "tolerance": 0.01
      },
      "record1": {"Revenue ($B)": 19.06},
      "record2": {"Revenue ($B)": 19.065}
    }
  ]
}
```

### Execution Logs

```http
GET http://127.0.0.1:8000/api/v1/validation/logs
GET http://127.0.0.1:8000/api/v1/validation/logs?limit=20
GET http://127.0.0.1:8000/api/v1/validation/logs?request_id=VAL-001
```

## Deduplication API Example

The original deduplication endpoint remains available:

```http
POST http://127.0.0.1:8000/api/v1/deduplicate/execute
```

```json
{
  "request_id": "DEDUP-001",
  "rule_id": "DR_001",
  "config": {
    "key_fields": ["Year", "Revenue ($B)"]
  },
  "record1": {
    "Year": 2004,
    "Revenue ($B)": 19.06
  },
  "record2": {
    "Year": 2004,
    "Revenue ($B)": 19.06
  }
}
```

## Response Format

Successful execution responses have this shape:

```json
{
  "success": true,
  "request_id": "VAL-001",
  "records_count": 2,
  "rule_ids": ["DR_001"],
  "results": [
    {
      "rule_id": "DR_001",
      "is_duplicate": true
    }
  ],
  "overall_is_duplicate": true,
  "matched_rules": ["DR_001"]
}
```

## Project Structure

```text
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
    ├── base/
    │   └── base_dedup_rule.py
    ├── resolutions/
    │   ├── keep_first.py
    │   └── merge_coalesce.py
    └── rules/
        ├── DR_001_exact_composite_key.py
        ├── DR_002_fuzzy_token_ratio.py
        ├── DR_003_numerical_tolerance.py
        ├── DR_004_whitespace_normalized.py
        └── DR_005_all_fields_exact.py
```

## Testing

Run the test suite with:

```powershell
python -m pytest -q
```

## License

Academic Project - University of Colombo School of Computing
