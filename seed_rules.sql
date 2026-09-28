USE deduplication_db;

INSERT INTO deduplication_categories (category_name, description)
SELECT 'Record Matching', 'Rules used to identify duplicate records'
WHERE NOT EXISTS (
    SELECT 1 FROM deduplication_categories WHERE category_name = 'Record Matching'
);

SET @category_id = (
    SELECT category_id FROM deduplication_categories
    WHERE category_name = 'Record Matching' LIMIT 1
);

INSERT INTO deduplication_rules
    (rule_code, rule_name, description, category_id, status, is_system_rule)
VALUES
    ('DR_001', 'Exact Composite Key', 'Exact comparison across configured fields', @category_id, 'active', 'Y'),
    ('DR_002', 'Fuzzy Token Ratio', 'Fuzzy comparison of a configured text field', @category_id, 'active', 'Y'),
    ('DR_003', 'Numerical Tolerance', 'Numeric comparison within a configured tolerance', @category_id, 'active', 'Y')
ON DUPLICATE KEY UPDATE
    rule_name = VALUES(rule_name), description = VALUES(description),
    category_id = VALUES(category_id), status = 'active';

INSERT INTO deduplication_rule_versions (rule_id, version_no, status, change_log)
SELECT rule_id, '1.0', 'active', 'Initial system rule version'
FROM deduplication_rules r
WHERE NOT EXISTS (
    SELECT 1 FROM deduplication_rule_versions v
    WHERE v.rule_id = r.rule_id AND v.version_no = '1.0'
);

INSERT INTO deduplication_rule_methods
    (version_id, method_name, method_path, entry_point, description)
SELECT v.version_id,
       CASE r.rule_code
           WHEN 'DR_001' THEN 'ExactCompositeKeyRule'
           WHEN 'DR_002' THEN 'FuzzyTokenRatioRule'
           WHEN 'DR_003' THEN 'NumericalToleranceRule'
       END,
       CASE r.rule_code
           WHEN 'DR_001' THEN 'deduplication_rules.rules.DR_001_exact_composite_key'
           WHEN 'DR_002' THEN 'deduplication_rules.rules.DR_002_fuzzy_token_ratio'
           WHEN 'DR_003' THEN 'deduplication_rules.rules.DR_003_numerical_tolerance'
       END,
       'apply', 'Python implementation of the rule'
FROM deduplication_rules r
JOIN deduplication_rule_versions v ON v.rule_id = r.rule_id
WHERE v.version_no = '1.0'
  AND NOT EXISTS (
      SELECT 1 FROM deduplication_rule_methods m WHERE m.version_id = v.version_id
  );


  ////////////
  USE deduplication_db;

-- ============================================
-- 1. CATEGORIES
-- ============================================
INSERT IGNORE INTO deduplication_categories (category_name, description) VALUES
('Exact Match', 'Exact duplicate detection'),
('Fuzzy Match', 'Near-duplicate using similarity'),
('Numeric Match', 'Numeric tolerance detection'),
('Normalized Match', 'Whitespace/case-normalized detection'),
('Hash Match', 'Full record hash-based detection');

-- ============================================
-- 2. RULES
-- ============================================
INSERT INTO deduplication_rules 
(rule_code, rule_name, description, category_id, status, created_by)
VALUES
('DR_001', 'Exact Composite Key', 
 'Exact match on specified key fields',
 (SELECT category_id FROM deduplication_categories WHERE category_name='Exact Match'),
 'active', 'SYSTEM'),

('DR_002', 'Fuzzy Token Ratio', 
 'Fuzzy string similarity on a field',
 (SELECT category_id FROM deduplication_categories WHERE category_name='Fuzzy Match'),
 'active', 'SYSTEM'),

('DR_003', 'Numerical Tolerance', 
 'Numeric values within tolerance',
 (SELECT category_id FROM deduplication_categories WHERE category_name='Numeric Match'),
 'active', 'SYSTEM'),

('DR_004', 'Whitespace Normalized', 
 'Detects near-duplicates differing only in whitespace/formatting',
 (SELECT category_id FROM deduplication_categories WHERE category_name='Normalized Match'),
 'active', 'SYSTEM'),

('DR_005', 'Full Record Hash', 
 'Detects exact duplicates using full record hash',
 (SELECT category_id FROM deduplication_categories WHERE category_name='Hash Match'),
 'active', 'SYSTEM');

-- ============================================
-- 3. VERSIONS
-- ============================================
INSERT INTO deduplication_rule_versions 
(rule_id, version_no, status, created_by)
SELECT rule_id, 'v1.0', 'active', 'SYSTEM'
FROM deduplication_rules
WHERE rule_code IN ('DR_001','DR_002','DR_003','DR_004','DR_005');

-- ============================================
-- 4. METHODS
-- ============================================
INSERT INTO deduplication_rule_methods 
(version_id, method_name, method_path, entry_point)
SELECT v.version_id,
  CASE r.rule_code
    WHEN 'DR_001' THEN 'ExactCompositeKeyRule'
    WHEN 'DR_002' THEN 'FuzzyTokenRatioRule'
    WHEN 'DR_003' THEN 'NumericalToleranceRule'
    WHEN 'DR_004' THEN 'WhitespaceNormalizedRule'
    WHEN 'DR_005' THEN 'FullRecordHashRule'
  END,
  CONCAT('deduplication_rules.rules.',
    CASE r.rule_code
      WHEN 'DR_001' THEN 'DR_001_exact_composite_key.ExactCompositeKeyRule'
      WHEN 'DR_002' THEN 'DR_002_fuzzy_token_ratio.FuzzyTokenRatioRule'
      WHEN 'DR_003' THEN 'DR_003_numerical_tolerance.NumericalToleranceRule'
      WHEN 'DR_004' THEN 'DR_004_whitespace_normalized.WhitespaceNormalizedRule'
      WHEN 'DR_005' THEN 'DR_005_full_record_hash.FullRecordHashRule'
    END),
  'apply'
FROM deduplication_rules r
JOIN deduplication_rule_versions v ON v.rule_id = r.rule_id
WHERE r.rule_code IN ('DR_001','DR_002','DR_003','DR_004','DR_005');

-- ============================================
-- 5. PARAMETERS (dataset-specific)
-- ============================================

-- DR_001: Exact Composite Key
INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'key_fields', 'json', 'Y',
  '["Year","Market cap ($B)","Revenue ($B)","Earnings ($B)"]'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_001';

-- DR_002: Fuzzy Token Ratio
INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'field', 'string', 'Y', 'Revenue ($B)'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_002';

INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'threshold', 'float', 'N', '0.85'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_002';

-- DR_003: Numerical Tolerance
INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'field', 'string', 'Y', 'Revenue ($B)'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_003';

INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'tolerance', 'float', 'N', '0.01'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_003';

-- DR_004: Whitespace Normalized
INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'key_fields', 'json', 'Y',
  '["Year","Revenue ($B)","Earnings ($B)"]'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_004';

-- DR_005: Full Record Hash
INSERT INTO deduplication_rule_parameters 
(method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'exclude_fields', 'json', 'N', '[]'
FROM deduplication_rule_methods m
JOIN deduplication_rule_versions v ON v.version_id = m.version_id
JOIN deduplication_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'DR_005';

SELECT 'Deduplication rules seeded' AS status;
SELECT rule_id, rule_code, rule_name FROM deduplication_rules;