# deduplication_rules/rules/DR_004_whitespace_normalized.py
from ..base.base_dedup_rule import BaseDedupRule


class WhitespaceNormalizedRule(BaseDedupRule):
    """
    Detects near-duplicates that differ only in whitespace/formatting.
    
    Detects: Year 2010 → Revenue = "  24.07  " vs "24.07"
    
    Params:
        key_fields (list): fields to compare after normalization
    """

    rule_id = "DR_004"

    def __init__(self, key_fields=None):
        self.key_fields = key_fields or []

    def _normalize(self, value):
        """Normalize: strip, lowercase, remove symbols."""
        if value is None:
            return ""
        normalized = str(value).strip().lower()
        # Remove currency symbols, commas, percent signs
        for char in ["$", ",", "%", " "]:
            normalized = normalized.replace(char, "")
        return normalized

    def apply(self, record1, record2):
        if not self.key_fields:
            return False

        for field in self.key_fields:
            v1 = self._normalize(record1.get(field))
            v2 = self._normalize(record2.get(field))

            # Skip empty values
            if not v1 or not v2:
                continue

            if v1 != v2:
                return False

        return True