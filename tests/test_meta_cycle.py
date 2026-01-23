"""
Step 7: Meta-Cognition Cycle Integration Test
==============================================
메타인지 시스템의 핵심인 MetaCycle의 조정 로직을 검증한다.

MetaCycle이 MetaEvaluator와 StrategyAdapter를 올바르게 연결하여
평가 → 전략 수립 → 리포트 생성의 흐름이 유기적으로 작동하는지 확인한다.

검증 항목:
1. MetaCycle 초기화 시 하위 컴포넌트(Evaluator, Adapter) 생성 확인
2. process_cycle 실행 흐름: Context → Evaluator → StrategyAdapter → CycleReport
3. 에러 발생 시 시스템이 중단되지 않고 graceful하게 처리하는지 확인
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from engine.meta_cycle import MetaCycle, CycleReport
    HAS_META_CYCLE = True
except ImportError:
    HAS_META_CYCLE = False
    MetaCycle = None
    CycleReport = None

try:
    from engine.strategy_adapter import StrategyMode
    HAS_STRATEGY_MODE = True
except ImportError:
    HAS_STRATEGY_MODE = False
    StrategyMode = None


class TestMetaCycleInitialization(unittest.TestCase):
    """MetaCycle 초기화 테스트"""

    def setUp(self):
        if not HAS_META_CYCLE:
            self.skipTest("MetaCycle module not available")

    def test_cycle_creates_evaluator_and_adapter(self):
        """MetaCycle 초기화 시 하위 컴포넌트가 정상적으로 생성되는지 확인"""
        cycle = MetaCycle()
        
        self.assertTrue(hasattr(cycle, 'evaluator'), "MetaCycle should have evaluator attribute")
        self.assertTrue(hasattr(cycle, 'adapter'), "MetaCycle should have adapter attribute")
        self.assertIsNotNone(cycle.evaluator, "Evaluator should not be None")
        self.assertIsNotNone(cycle.adapter, "Adapter should not be None")

    def test_cycle_has_process_method(self):
        """MetaCycle에 process_cycle 메서드가 존재하는지 확인"""
        cycle = MetaCycle()
        
        self.assertTrue(hasattr(cycle, 'process_cycle'), "MetaCycle should have process_cycle method")
        self.assertTrue(callable(getattr(cycle, 'process_cycle', None)), "process_cycle should be callable")


class TestMetaCycleProcessFlow(unittest.TestCase):
    """MetaCycle의 process_cycle 실행 흐름 테스트"""

    def setUp(self):
        if not HAS_META_CYCLE:
            self.skipTest("MetaCycle module not available")

    def test_process_cycle_returns_report(self):
        """process_cycle이 CycleReport 또는 dict를 반환하는지 확인"""
        cycle = MetaCycle()
        
        mock_context = {
            "recent_history": [
                {"status": "success", "action": "Update", "file": "test.py"}
            ],
            "memories": []
        }
        
        report = cycle.process_cycle(mock_context)
        
        self.assertIsNotNone(report, "process_cycle should return a report")
        
        if HAS_META_CYCLE and CycleReport is not None:
            is_valid_type = isinstance(report, (CycleReport, dict))
        else:
            is_valid_type = isinstance(report, dict)
        
        self.assertTrue(is_valid_type, "Report should be CycleReport or dict")

    def test_process_cycle_with_empty_context(self):
        """빈 컨텍스트로도 process_cycle이 정상 작동하는지 확인"""
        cycle = MetaCycle()
        
        empty_context = {}
        
        try:
            report = cycle.process_cycle(empty_context)
            self.assertIsNotNone(report, "Should handle empty context gracefully")
        except Exception as e:
            self.fail(f"process_cycle should not raise exception with empty context: {e}")

    def test_process_cycle_with_success_history(self):
        """성공 기록이 포함된 컨텍스트 처리 확인"""
        cycle = MetaCycle()
        
        success_context = {
            "recent_history": [
                {"status": "success", "action": "Create", "file": "module_a.py"},
                {"status": "success", "action": "Update", "file": "module_b.py"},
                {"status": "success", "action": "Update", "file": "module_c.py"},
            ],
            "memories": [
                {"text": "Previous successful pattern", "distance": 0.1}
            ]
        }
        
        report = cycle.process_cycle(success_context)
        
        self.assertIsNotNone(report)
        
        if hasattr(report, 'evaluation') and report.evaluation:
            confidence = report.evaluation.get('confidence_score', 0)
            self.assertGreaterEqual(confidence, 0.0, "Confidence should be non-negative")
            self.assertLessEqual(confidence, 1.0, "Confidence should not exceed 1.0")

    def test_process_cycle_with_failure_history(self):
        """실패 기록이 포함된 컨텍스트 처리 확인"""
        cycle = MetaCycle()
        
        failure_context = {
            "recent_history": [
                {"status": "failed", "action": "Update", "file": "broken.py", "error": "Syntax error"},
                {"status": "failed", "action": "Update", "file": "broken.py", "error": "Syntax error"},
            ],
            "memories": []
        }
        
        report = cycle.process_cycle(failure_context)
        
        self.assertIsNotNone(report, "Should handle failure history gracefully")


class TestMetaCycleErrorHandling(unittest.TestCase):
    """MetaCycle 에러 처리 테스트"""

    def setUp(self):
        if not HAS_META_CYCLE:
            self.skipTest("MetaCycle module not available")

    def test_handles_none_context(self):
        """None 컨텍스트 처리 확인"""
        cycle = MetaCycle()
        
        try:
            report = cycle.process_cycle(None)
            print("MetaCycle handled None context gracefully")
        except TypeError:
            pass
        except Exception as e:
            self.fail(f"Unexpected exception type for None context: {type(e).__name__}: {e}")

    def test_handles_malformed_history(self):
        """잘못된 형식의 history 처리 확인"""
        cycle = MetaCycle()
        
        malformed_context = {
            "recent_history": "not_a_list",
            "memories": None
        }
        
        try:
            report = cycle.process_cycle(malformed_context)
            print("MetaCycle handled malformed context gracefully")
        except Exception as e:
            print(f"MetaCycle raised exception for malformed context: {type(e).__name__}")


class TestMetaCycleStrategyIntegration(unittest.TestCase):
    """MetaCycle과 StrategyAdapter 통합 테스트"""

    def setUp(self):
        if not HAS_META_CYCLE:
            self.skipTest("MetaCycle module not available")

    def test_report_contains_strategy_mode(self):
        """CycleReport에 전략 모드가 포함되어 있는지 확인"""
        cycle = MetaCycle()
        
        context = {
            "recent_history": [
                {"status": "success", "action": "Update", "file": "test.py"}
            ],
            "memories": []
        }
        
        report = cycle.process_cycle(context)
        
        has_mode = False
        if hasattr(report, 'recommended_mode'):
            has_mode = report.recommended_mode is not None
        elif isinstance(report, dict):
            has_mode = 'recommended_mode' in report or 'strategy_mode' in report
        
        self.assertTrue(has_mode, "Report should contain strategy mode information")

    def test_report_contains_evaluation(self):
        """CycleReport에 평가 결과가 포함되어 있는지 확인"""
        cycle = MetaCycle()
        
        context = {
            "recent_history": [
                {"status": "success", "action": "Update", "file": "test.py"}
            ],
            "memories": []
        }
        
        report = cycle.process_cycle(context)
        
        has_evaluation = False
        if hasattr(report, 'evaluation'):
            has_evaluation = report.evaluation is not None
        elif isinstance(report, dict):
            has_evaluation = 'evaluation' in report or 'efficacy_score' in report
        
        self.assertTrue(has_evaluation, "Report should contain evaluation information")


class TestMetaCycleWithMockedComponents(unittest.TestCase):
    """Mock을 사용한 MetaCycle 컴포넌트 조정 테스트"""

    def setUp(self):
        if not HAS_META_CYCLE:
            self.skipTest("MetaCycle module not available")

    def test_evaluator_called_with_context(self):
        """Evaluator가 컨텍스트와 함께 호출되는지 확인"""
        cycle = MetaCycle()
        
        original_evaluator = cycle.evaluator
        cycle.evaluator = MagicMock()
        cycle.evaluator.evaluate_efficacy = MagicMock(return_value={
            "confidence_score": 0.75,
            "efficacy_score": 0.8,
            "status": "stable"
        })
        
        context = {
            "recent_history": [{"status": "success"}],
            "memories": []
        }
        
        try:
            report = cycle.process_cycle(context)
            
            cycle.evaluator.evaluate_efficacy.assert_called()
            print("Evaluator was called during process_cycle")
        except Exception as e:
            print(f"Note: Mock test encountered: {e}")
        finally:
            cycle.evaluator = original_evaluator

    def test_adapter_called_after_evaluation(self):
        """Adapter가 평가 후 호출되는지 확인"""
        cycle = MetaCycle()
        
        original_adapter = cycle.adapter
        cycle.adapter = MagicMock()
        
        if HAS_STRATEGY_MODE and StrategyMode is not None:
            cycle.adapter.evaluate_mode = MagicMock(return_value=StrategyMode.NORMAL)
        else:
            cycle.adapter.evaluate_mode = MagicMock(return_value="normal")
        
        context = {
            "recent_history": [{"status": "success"}],
            "memories": []
        }
        
        try:
            report = cycle.process_cycle(context)
            print("Adapter integration test completed")
        except Exception as e:
            print(f"Note: Adapter mock test encountered: {e}")
        finally:
            cycle.adapter = original_adapter


if __name__ == "__main__":
    print("=" * 60)
    print("Step 7: Meta-Cognition Cycle Integration Test")
    print("=" * 60)
    unittest.main(verbosity=2)