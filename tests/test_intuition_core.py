"""
Step 8: Intuition System Core Unit Tests
========================================
직관(Intuition) 시스템의 핵심 컴포넌트인 ReflexRegistry와 
Intuition 데이터 구조의 무결성을 검증한다.

검증 항목:
1. ReflexRegistry의 등록(register) 및 조회(get) 메커니즘
2. ReflexType 열거형 및 ReflexAction 구조체 유효성
3. IntuitionResult 데이터 클래스의 동작 확인
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from engine.reflex import ReflexRegistry, ReflexType, ReflexAction
    HAS_REFLEX = True
except ImportError:
    HAS_REFLEX = False
    ReflexRegistry = None
    ReflexType = None
    ReflexAction = None

try:
    from engine.intuition import IntuitionResult, IntuitionStrength
    HAS_INTUITION = True
except ImportError:
    HAS_INTUITION = False
    IntuitionResult = None
    IntuitionStrength = None


class TestReflexType(unittest.TestCase):
    """ReflexType 열거형 검증"""

    def setUp(self):
        if not HAS_REFLEX:
            self.skipTest("engine.reflex module not available")

    def test_reflex_type_quick_fix_exists(self):
        """QUICK_FIX 타입이 존재하는지 확인"""
        self.assertTrue(hasattr(ReflexType, "QUICK_FIX"))

    def test_reflex_type_ignore_exists(self):
        """IGNORE 타입이 존재하는지 확인"""
        self.assertTrue(hasattr(ReflexType, "IGNORE"))

    def test_reflex_type_value_is_string(self):
        """ReflexType 값이 문자열인지 확인"""
        self.assertIsInstance(ReflexType.QUICK_FIX.value, str)
        self.assertIsInstance(ReflexType.IGNORE.value, str)


class TestIntuitionResult(unittest.TestCase):
    """IntuitionResult 데이터 구조 검증"""

    def setUp(self):
        if not HAS_INTUITION:
            self.skipTest("engine.intuition module not available")

    def test_intuition_result_creation(self):
        """IntuitionResult 객체 생성 확인"""
        result = IntuitionResult(
            pattern_match="test_pattern",
            confidence=0.95,
            strength=IntuitionStrength.STRONG,
            metadata={"source": "test"}
        )
        self.assertIsNotNone(result)

    def test_intuition_result_attributes(self):
        """IntuitionResult 속성 확인"""
        result = IntuitionResult(
            pattern_match="error_pattern_xyz",
            confidence=0.88,
            strength=IntuitionStrength.MODERATE,
            metadata={"key": "value"}
        )
        self.assertEqual(result.pattern_match, "error_pattern_xyz")
        self.assertEqual(result.confidence, 0.88)
        self.assertEqual(result.strength, IntuitionStrength.MODERATE)
        self.assertEqual(result.metadata["key"], "value")

    def test_intuition_strength_enum(self):
        """IntuitionStrength 열거형 값 확인"""
        self.assertTrue(hasattr(IntuitionStrength, "STRONG"))
        self.assertTrue(hasattr(IntuitionStrength, "MODERATE"))
        self.assertTrue(hasattr(IntuitionStrength, "WEAK"))
        self.assertTrue(hasattr(IntuitionStrength, "NONE"))


class TestReflexRegistry(unittest.TestCase):
    """ReflexRegistry 등록 및 조회 검증"""

    def setUp(self):
        if not HAS_REFLEX:
            self.skipTest("engine.reflex module not available")

    def test_registry_get_missing_returns_none(self):
        """존재하지 않는 반사 행동 조회 시 None 반환"""
        action = ReflexRegistry.get("non_existent_reflex_xyz_999")
        self.assertIsNone(action)

    def test_registry_register_and_get(self):
        """반사 행동 등록 및 조회 흐름 검증"""
        test_reflex_id = "test_intuition_core_reflex_001"

        def dummy_handler(context):
            return {"status": "handled", "input": context}

        ReflexRegistry.register(
            name=test_reflex_id,
            reflex_type=ReflexType.QUICK_FIX,
            handler=dummy_handler,
            description="Test Reflex for unit test"
        )

        action = ReflexRegistry.get(test_reflex_id)
        self.assertIsNotNone(action)
        self.assertIsInstance(action, ReflexAction)
        self.assertEqual(action.name, test_reflex_id)
        self.assertEqual(action.reflex_type, ReflexType.QUICK_FIX)

    def test_registered_handler_is_callable(self):
        """등록된 핸들러가 호출 가능한지 확인"""
        test_reflex_id = "test_intuition_core_reflex_002"

        def echo_handler(context):
            return {"echo": context.get("message", "none")}

        ReflexRegistry.register(
            name=test_reflex_id,
            reflex_type=ReflexType.IGNORE,
            handler=echo_handler,
            description="Echo handler for testing"
        )

        action = ReflexRegistry.get(test_reflex_id)
        self.assertIsNotNone(action)
        self.assertTrue(callable(action.handler))

        result = action.handler({"message": "hello"})
        self.assertEqual(result["echo"], "hello")


class TestReflexAction(unittest.TestCase):
    """ReflexAction 데이터 구조 검증"""

    def setUp(self):
        if not HAS_REFLEX:
            self.skipTest("engine.reflex module not available")

    def test_reflex_action_structure(self):
        """ReflexAction이 필요한 필드를 가지는지 확인"""
        def sample_handler(ctx):
            return ctx

        action = ReflexAction(
            name="sample_action",
            reflex_type=ReflexType.QUICK_FIX,
            handler=sample_handler,
            description="Sample action"
        )

        self.assertEqual(action.name, "sample_action")
        self.assertEqual(action.reflex_type, ReflexType.QUICK_FIX)
        self.assertEqual(action.description, "Sample action")
        self.assertTrue(callable(action.handler))


if __name__ == "__main__":
    unittest.main()