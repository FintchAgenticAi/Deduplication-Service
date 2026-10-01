import os

import mysql.connector
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    """Create a MySQL connection from environment variables."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "1234"),
        database=os.getenv("MYSQL_DATABASE", "deduplication_db"),
        connection_timeout=int(os.getenv("MYSQL_CONNECTION_TIMEOUT", "5")),
    )


def check_connection():
    """Verify that MySQL accepts queries using the configured credentials."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    finally:
        connection.close()


DEFAULT_RULE_CONTEXTS = {
    "DR_001": {"rule_id": 1, "version_id": 1, "method_id": 1},
    "DR_002": {"rule_id": 2, "version_id": 2, "method_id": 2},
    "DR_003": {"rule_id": 3, "version_id": 3, "method_id": 3},
    "DR_004": {"rule_id": 4, "version_id": 4, "method_id": 4},
    "DR_005": {"rule_id": 5, "version_id": 5, "method_id": 5},
}


def get_rule_context(rule_code):
    """Return the active database metadata for a rule code."""
    normalized_code = (rule_code or "").upper()
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.rule_id, v.version_id, m.method_id
            FROM deduplication_rules AS r
            JOIN deduplication_rule_versions AS v ON v.rule_id = r.rule_id
            JOIN deduplication_rule_methods AS m ON m.version_id = v.version_id
            WHERE r.rule_code = %s
              AND r.status = 'active'
              AND v.status = 'active'
            ORDER BY v.version_id DESC
            LIMIT 1
            """,
            (normalized_code,),
        )
        context = cursor.fetchone()
        if context is not None:
            return context

        fallback_context = DEFAULT_RULE_CONTEXTS.get(normalized_code)
        if fallback_context is not None:
            return fallback_context

        raise LookupError(
            f"No active database metadata found for rule {normalized_code}"
        )
    finally:
        connection.close()


def log_execution(context, request_id, is_duplicate, status="success", error_message=None):
    """Persist the result of a two-record comparison."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO deduplication_logic_logs (
                rule_id, method_id, version_id, request_id,
                input_record_count, unique_record_count,
                duplicate_record_count, status, ended_at, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                context["rule_id"],
                context["method_id"],
                context["version_id"],
                request_id,
                2,
                1 if is_duplicate else 2,
                1 if is_duplicate else 0,
                status,
                error_message,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_execution_logs(limit=100, request_id=None):
    """Return recent execution logs, optionally filtered by request ID."""
    bounded_limit = max(1, min(int(limit), 500))
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT log_id, rule_id, method_id, version_id, request_id,
                   input_record_count, unique_record_count,
                   duplicate_record_count, status, started_at, ended_at,
                   error_message
            FROM deduplication_logic_logs
        """
        params = []
        if request_id:
            query += " WHERE request_id = %s"
            params.append(request_id)
        query += " ORDER BY ended_at DESC LIMIT %s"
        params.append(bounded_limit)
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        connection.close()