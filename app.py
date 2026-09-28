"""
Deduplication Service — API Entry Point

Flask app that exposes the deduplication rule engine over HTTP.
Supports both single-rule and multi-rule payloads for two-record comparison.
"""
from uuid import uuid4

from flask import Flask, request, jsonify

from deduplication_rules.registry import get_rule
from database import check_connection, get_rule_context, log_execution


app = Flask(__name__)


# ============================================
# HEALTH CHECK
# ============================================
@app.route("/health/db", methods=["GET"])
def database_health():
    """Verify the API can reach MySQL."""
    try:
        check_connection()
        return jsonify({"success": True, "database": "connected"})
    except Exception as e:
        return jsonify({
            "success": False,
            "database": "unavailable",
            "error": str(e),
        }), 503


# ============================================
# DEDUPLICATION ENDPOINT
# ============================================
@app.route("/deduplicate", methods=["POST"])
@app.route("/api/v1/deduplicate/execute", methods=["POST"])
def deduplicate():
    """
    Compare two records against one or more deduplication rules.

    Payload Format A — single rule (legacy):
        {
          "request_id": "...",
          "rule_id": "DR_001",
          "record1": {...},
          "record2": {...},
          "config": {...}
        }

    Payload Format B — multiple rules:
        {
          "request_id": "...",
          "rule_ids": ["DR_001", "DR_004"],
          "records": [{...}, {...}],
          "config": {
            "DR_001": {...},
            "DR_004": {...}
          }
        }
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A JSON request body is required",
        }), 400

    request_id = data.get("request_id", str(uuid4()))

    # ----------------------------------------
    # 1. Parse payload (support both formats)
    # ----------------------------------------
    if "rule_id" in data:
        # Format A — single rule
        rule_id = data["rule_id"]
        rule_ids = [rule_id]
        record1 = data.get("record1")
        record2 = data.get("record2")
        records = [record1, record2] if record1 is not None and record2 is not None else None
        config = {rule_id: data.get("config", {})}

    elif "rule_ids" in data:
        # Format B — multiple rules
        rule_ids = data.get("rule_ids", [])
        records = data.get("records")
        config = data.get("config", {})

    else:
        return jsonify({
            "success": False,
            "error": "Either 'rule_id' or 'rule_ids' is required",
        }), 400

    # ----------------------------------------
    # 2. Validate
    # ----------------------------------------
    if not rule_ids:
        return jsonify({
            "success": False,
            "error": "No rules specified",
        }), 400

    if not isinstance(records, (list, tuple)) or len(records) != 2:
        return jsonify({
            "success": False,
            "error": "Exactly 2 records are required for comparison",
        }), 400

    record1, record2 = records
    results = []
    matched_rules = []

    # ----------------------------------------
    # 3. Execute each rule
    # ----------------------------------------
    try:
        for rule_id in rule_ids:
            RuleClass = get_rule(rule_id)
            context = get_rule_context(rule_id)
            rule_config = config.get(rule_id, {}) if isinstance(config, dict) else {}

            # Instantiate the rule with appropriate parameters
            if rule_id == "DR_001":
                rule = RuleClass(key_fields=rule_config.get("key_fields", []))

            elif rule_id == "DR_002":
                rule = RuleClass(
                    field=rule_config.get("field"),
                    threshold=rule_config.get("threshold", 0.85),
                )

            elif rule_id == "DR_003":
                rule = RuleClass(
                    field=rule_config.get("field"),
                    tolerance=rule_config.get("tolerance", 0.01),
                )

            elif rule_id == "DR_004":
                rule = RuleClass(key_fields=rule_config.get("key_fields", []))

            elif rule_id == "DR_005":
                rule = RuleClass(exclude_fields=rule_config.get("exclude_fields", []))

            else:
                results.append({
                    "rule_id": rule_id,
                    "success": False,
                    "error": f"Unsupported rule: {rule_id}",
                })
                continue

            # Apply the rule
            is_duplicate = rule.apply(record1, record2)

            # Persist to DB
            log_execution(context, request_id, is_duplicate)

            # Collect result
            results.append({
                "rule_id": rule_id,
                "is_duplicate": is_duplicate,
            })

            if is_duplicate:
                matched_rules.append(rule_id)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400

    # ----------------------------------------
    # 4. Build response
    # ----------------------------------------
    return jsonify({
        "success": True,
        "request_id": request_id,
        "records_count": 2,
        "rule_ids": rule_ids,
        "results": results,
        "overall_is_duplicate": len(matched_rules) > 0,
        "matched_rules": matched_rules,
    })


# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    app.run(debug=True, port=8000)