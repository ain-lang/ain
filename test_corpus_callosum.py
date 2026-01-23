import unittest
from corpus_callosum import CorpusCallosum
from fact_core import FactCore

class MockNexus:
    def get_evolution_summary(self):
        return "Mock History"

class TestCorpusCallosum(unittest.TestCase):
    def setUp(self):
        self.fc = FactCore(fact_path="test_cc_fact.json")
        self.nexus = MockNexus()
        self.cc = CorpusCallosum(self.fc, self.nexus)

    def test_synthesize_context(self):
        # ... (기존 로직)
        context = self.cc.synthesize_context(user_query="Hello")
        self.assertIn("AIN NEURAL CONTEXT", context)
        self.assertIn("Hello", context)
        self.assertIn("Mock History", context)

    def test_bridge_to_arrow(self):
        # pyarrow가 설치되어 있을 때만 실행
        try:
            import pyarrow as pa
            data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
            table = self.cc.bridge_to_arrow(data)
            self.assertIsInstance(table, pa.Table)
            self.assertEqual(table.num_rows, 2)
        except ImportError:
            self.skipTest("pyarrow not installed")

    def tearDown(self):
        import os
        if os.path.exists("test_cc_fact.json"):
            os.remove("test_cc_fact.json")

if __name__ == "__main__":
    unittest.main()
