# deduplication_rules/registry.py
from .rules.DR_001_exact_composite_key import ExactCompositeKeyRule
from .rules.DR_002_fuzzy_token_ratio import FuzzyTokenRatioRule
from .rules.DR_003_numerical_tolerance import NumericalToleranceRule
from .rules.DR_004_whitespace_normalized import WhitespaceNormalizedRule
from .rules.DR_005_all_fields_exact import AllFieldsExactRule


RULE_REGISTRY = {
    "DR_001": ExactCompositeKeyRule,
    "DR_002": FuzzyTokenRatioRule,
    "DR_003": NumericalToleranceRule,
    "DR_004": WhitespaceNormalizedRule,
    "DR_005": AllFieldsExactRule,
}


def get_rule(rule_id):
    rule = RULE_REGISTRY.get(rule_id)
    if rule is None:
        raise ValueError(f"Unknown rule ID: {rule_id}")
    return rule