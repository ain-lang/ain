import unittest
from fact_core import FactCore

class TestFactCore(unittest.TestCase):
    def setUp(self):
        self.fc = FactCore(fact_path="test_fact_core.json")

    def test_get_fact_with_default(self):
        # 존재하는 키
        version = self.fc.get_fact("identity", "version")
        self.assertIsNotNone(version)
        
        # 존재하지 않는 키 + 기본값
        val = self.fc.get_fact("non_existent", default="fallback")
        self.assertEqual(val, "fallback")
        
        # 깊은 계층 키 + 기본값
        val = self.fc.get_fact("identity", "invalid", default=123)
        self.assertEqual(val, 123)

    def test_add_fact_and_update(self):
        self.fc.add_fact("test_key", "test_value")
        self.assertEqual(self.fc.get_fact("test_key"), "test_value")
        
        self.fc.update_fact("test_key", "updated_value")
        self.assertEqual(self.fc.get_fact("test_key"), "updated_value")

    def test_export_as_arrow(self):
        try:
            import pyarrow as pa
            table = self.fc.export_as_arrow()
            self.assertIsInstance(table, pa.Table)
        except ImportError:
            self.skipTest("pyarrow not installed")

    def tearDown(self):
        import os
        if os.path.exists("test_fact_core.json"):
            os.remove("test_fact_core.json")

if __name__ == "__main__":
    unittest.main()
