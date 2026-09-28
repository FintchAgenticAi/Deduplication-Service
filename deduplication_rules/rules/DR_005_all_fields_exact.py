# deduplication_rules/rules/DR_005_all_fields_exact.py
from ..base.base_dedup_rule import BaseDedupRule


class AllFieldsExactRule(BaseDedupRule):
    """
    Detects exact duplicates by comparing all fields.
    
    Detects: Year 2004 → exact duplicate
    
    Params:
        exclude_fields (list): fields to skip (e.g., internal IDs)
    """

    rule_id = "DR_005"

    def __init__(self, exclude_fields=None):
        self.exclude_fields = exclude_fields or []

    def apply(self, record1, record2):
        if not isinstance(record1, dict) or not isinstance(record2, dict):
            return False

        # Get all unique keys
        all_keys = set(record1.keys()) | set(record2.keys())
        all_keys -= set(self.exclude_fields)

        for key in all_keys:
            v1 = record1.get(key)
            v2 = record2.get(key)

            # Handle numeric tolerance for float comparison
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                if abs(float(v1) - float(v2)) > 0.0001:
                    return False
            # String comparison (exact)
            elif str(v1).strip() != str(v2).strip():
                return False

        return True