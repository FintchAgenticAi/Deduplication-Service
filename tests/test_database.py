import unittest
from unittest.mock import patch

from database import get_rule_context


class GetRuleContextTests(unittest.TestCase):
    def test_uses_default_metadata_when_database_has_no_active_rule_row(self):
        class FakeCursor:
            def __init__(self):
                self.called = False

            def execute(self, *args, **kwargs):
                self.called = True

            def fetchone(self):
                return None

        class FakeConnection:
            def __init__(self):
                self.cursor_obj = FakeCursor()

            def cursor(self, dictionary=True):
                return self.cursor_obj

            def close(self):
                pass

        with patch("database.get_connection", return_value=FakeConnection()):
            result = get_rule_context("DR_002")

        self.assertEqual(result["rule_id"], 2)
        self.assertEqual(result["version_id"], 2)
        self.assertEqual(result["method_id"], 2)


if __name__ == "__main__":
    unittest.main()
