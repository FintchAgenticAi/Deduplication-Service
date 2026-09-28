from ..base.base_dedup_rule import BaseDedupRule


class NumericalToleranceRule(BaseDedupRule):

    rule_id = "DR_003"

    def __init__(self, field, tolerance=0.01):
        self.field = field
        self.tolerance = tolerance

    def apply(self, record1, record2):
        try:
            value1 = float(record1.get(self.field))
            value2 = float(record2.get(self.field))

            return abs(value1 - value2) <= self.tolerance

        except (TypeError, ValueError):
            return False