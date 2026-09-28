from ..base.base_dedup_rule import BaseDedupRule


class ExactCompositeKeyRule(BaseDedupRule):

    rule_id = "DR_001"

    def __init__(self, key_fields):
        self.key_fields = key_fields

    def apply(self, record1, record2):
        return all(
            record1.get(field) == record2.get(field)
            for field in self.key_fields
        )