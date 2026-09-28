from difflib import SequenceMatcher
from ..base.base_dedup_rule import BaseDedupRule


class FuzzyTokenRatioRule(BaseDedupRule):

    rule_id = "DR_002"

    def __init__(self, field, threshold=0.85):
        self.field = field
        self.threshold = threshold

    def apply(self, record1, record2):
        value1 = str(record1.get(self.field, "")).lower().strip()
        value2 = str(record2.get(self.field, "")).lower().strip()

        if not value1 or not value2:
            return False

        ratio = SequenceMatcher(None, value1, value2).ratio()

        return ratio >= self.threshold