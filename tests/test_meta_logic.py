"""
Step 7: Meta-Cognition Logic Verification
=========================================
메타인지 시스템의 핵심인 '평가(Evaluator)'와 '전략(Adapter)' 모듈의
논리적 동작을 검증하는 단위 테스트.

검증 항목:
1. MetaEvaluator: 성공/실패 기록에 따른 자신감(Confidence) 및 효율성(Efficacy) 점수 산출
2. StrategyAdapter: 평가 점수와 시스템 상태에 따른 최적 전략 모드(StrategyMode) 결정
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from engine.meta_evaluator import MetaEvaluator
    HAS_EVALUATOR = True
except ImportError:
    HAS_EVALUATOR = False
    MetaEvaluator = None

try:
    from engine.strategy_adapter import StrategyAdapter, StrategyMode
    HAS_ADAPTER = True
except ImportError:
    HAS_ADAPTER = False
    StrategyAdapter = None
    StrategyMode = None


class TestMetaEvaluator(unittest.TestCase):
    """MetaEvaluator 단위 테스트"""

    def setUp(self):
        if not HAS_EVALUATOR:
            self.skipTest("MetaEvaluator module not found in engine/")
        self.evaluator = MetaEvaluator()

    def test_high_efficacy_from_success_streak(self):
        """성공적인 기록이 주어졌을 때 높은 효율성 점수를 반환하는지 검증"""
        recent_history = [
            {"status": "success", "action": "Update", "file": "test.py"},
            {"status": "success", "action": "Create", "file": "new.py"},
            {"status": "success", "action": "Update", "file": "core.py"},
            {"status": "success", "action": "Update", "file": "utils.py"},
            {"status": "success", "action": "Create", "file": "helper.py"},
        ]
        relevant_memories = [
            {"text": "Similar pattern solved before", "distance": 0.1},
            {"text": "Known approach", "distance": 0.2},
        ]

        result = self.evaluator.evaluate_efficacy(recent_history, relevant_memories)

        self.assertIn("confidence_score", result)
        self.assertGreaterEqual(result["confidence_score"], 0.7)
        self.assertIn("status", result)

    def test_low_efficacy_from_failure_streak(self):
        """실패 기록이 많을 때 낮은 효율성 점수를 반환하는지 검증"""
        recent_history = [
            {"status": "failed", "action": "Update", "file": "broken.py"},
            {"status": "failed", "action": "Update", "file": "broken.py"},
            {"status": "failed", "action": "Update", "file": "broken.py"},
            {"status": "success", "action": "Update", "file": "ok.py"},
            {"status": "failed", "action": "Update", "file": "broken.py"},
        ]
        relevant_memories = []

        result = self.evaluator.evaluate_efficacy(recent_history, relevant_memories)

        self.assertIn("confidence_score", result)
        self.assertLessEqual(result["confidence_score"], 0.5)

    def test_empty_history_returns_baseline(self):
        """기록이 없을 때 기본 점수를 반환하는지 검증"""
        result = self.evaluator.evaluate_efficacy([], [])

        self.assertIn("confidence_score", result)
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)

    def test_memory_relevance_boosts_confidence(self):
        """관련 기억이 많을수록 자신감이 높아지는지 검증"""
        history = [{"status": "success", "action": "Update", "file": "test.py"}]

        no_memory_result = self.evaluator.evaluate_efficacy(history, [])

        with_memory_result = self.evaluator.evaluate_efficacy(history, [
            {"text": "Exact match", "distance": 0.05},
            {"text": "Very similar", "distance": 0.1},
            {"text": "Related", "distance": 0.15},
        ])

        self.assertGreaterEqual(
            with_memory_result["confidence_score"],
            no_memory_result["confidence_score"]
        )

    def test_suggest_strategy_returns_valid_string(self):
        """suggest_strategy가 유효한 전략 문자열을 반환하는지 검증"""
        strategies = [
            self.evaluator.suggest_strategy(0.9),
            self.evaluator.suggest_strategy(0.5),
            self.evaluator.suggest_strategy(0.2),
        ]

        for strategy in strategies:
            self.assertIsInstance(strategy, str)
            self.assertGreater(len(strategy), 0)


class TestStrategyAdapter(unittest.TestCase):
    """StrategyAdapter 단위 테스트"""

    def setUp(self):
        if not HAS_ADAPTER:
            self.skipTest("StrategyAdapter module not found in engine/")
        self.adapter = StrategyAdapter()

    def test_normal_mode_for_balanced_state(self):
        """균형 잡힌 상태에서 NORMAL 모드를 반환하는지 검증"""
        mode = self.adapter.evaluate_mode(
            efficacy_score=0.6,
            error_count=1,
            complexity="medium"
        )

        self.assertEqual(mode, StrategyMode.NORMAL)

    def test_accelerated_mode_for_high_efficacy(self):
        """높은 효율성에서 ACCELERATED 모드를 반환하는지 검증"""
        mode = self.adapter.evaluate_mode(
            efficacy_score=0.9,
            error_count=0,
            complexity="low"
        )

        self.assertEqual(mode, StrategyMode.ACCELERATED)

    def test_critical_mode_for_repeated_errors(self):
        """반복 오류 시 CRITICAL 모드를 반환하는지 검증"""
        mode = self.adapter.evaluate_mode(
            efficacy_score=0.3,
            error_count=5,
            complexity="high"
        )

        self.assertEqual(mode, StrategyMode.CRITICAL)

    def test_cautious_mode_for_low_confidence(self):
        """낮은 자신감에서 CAUTIOUS 모드를 반환하는지 검증"""
        mode = self.adapter.evaluate_mode(
            efficacy_score=0.4,
            error_count=2,
            complexity="medium"
        )

        self.assertIn(mode, [StrategyMode.CAUTIOUS, StrategyMode.CRITICAL])

    def test_get_tuning_params_returns_dict(self):
        """get_tuning_params가 딕셔너리를 반환하는지 검증"""
        for mode in StrategyMode:
            params = self.adapter.get_tuning_params(mode)

            self.assertIsInstance(params, dict)
            self.assertIn("interval_multiplier", params)
            self.assertIn("temperature", params)

    def test_tuning_params_vary_by_mode(self):
        """모드에 따라 튜닝 파라미터가 다른지 검증"""
        normal_params = self.adapter.get_tuning_params(StrategyMode.NORMAL)
        accelerated_params = self.adapter.get_tuning_params(StrategyMode.ACCELERATED)
        critical_params = self.adapter.get_tuning_params(StrategyMode.CRITICAL)

        self.assertLess(
            accelerated_params["interval_multiplier"],
            normal_params["interval_multiplier"]
        )
        self.assertGreater(
            critical_params["interval_multiplier"],
            normal_params["interval_multiplier"]
        )

    def test_complexity_affects_mode_selection(self):
        """복잡도가 모드 선택에 영향을 미치는지 검증"""
        low_complexity_mode = self.adapter.evaluate_mode(
            efficacy_score=0.7,
            error_count=1,
            complexity="low"
        )

        high_complexity_mode = self.adapter.evaluate_mode(
            efficacy_score=0.7,
            error_count=1,
            complexity="high"
        )

        self.assertIn(low_complexity_mode, [StrategyMode.NORMAL, StrategyMode.ACCELERATED])
        self.assertIn(high_complexity_mode, [StrategyMode.NORMAL, StrategyMode.CAUTIOUS])


class TestMetaLogicIntegration(unittest.TestCase):
    """MetaEvaluator와 StrategyAdapter 통합 테스트"""

    def setUp(self):
        if not HAS_EVALUATOR or not HAS_ADAPTER:
            self.skipTest("Meta-cognition modules not found in engine/")
        self.evaluator = MetaEvaluator()
        self.adapter = StrategyAdapter()

    def test_evaluator_to_adapter_pipeline(self):
        """평가 결과가 전략 결정으로 올바르게 연결되는지 검증"""
        history = [
            {"status": "success", "action": "Update", "file": "a.py"},
            {"status": "success", "action": "Update", "file": "b.py"},
            {"status": "success", "action": "Create", "file": "c.py"},
        ]
        memories = [{"text": "Known pattern", "distance": 0.1}]

        eval_result = self.evaluator.evaluate_efficacy(history, memories)
        confidence = eval_result["confidence_score"]

        error_count = sum(1 for h in history if h.get("status") == "failed")
        mode = self.adapter.evaluate_mode(
            efficacy_score=confidence,
            error_count=error_count,
            complexity="medium"
        )

        self.assertIsInstance(mode, StrategyMode)

        params = self.adapter.get_tuning_params(mode)
        self.assertIn("interval_multiplier", params)

    def test_failure_cascade_triggers_critical_mode(self):
        """연속 실패가 CRITICAL 모드를 트리거하는지 검증"""
        failure_history = [
            {"status": "failed", "action": "Update", "file": "x.py"},
            {"status": "failed", "action": "Update", "file": "x.py"},
            {"status": "failed", "action": "Update", "file": "x.py"},
            {"status": "failed", "action": "Update", "file": "x.py"},
        ]

        eval_result = self.evaluator.evaluate_efficacy(failure_history, [])
        confidence = eval_result["confidence_score"]

        mode = self.adapter.evaluate_mode(
            efficacy_score=confidence,
            error_count=4,
            complexity="high"
        )

        self.assertEqual(mode, StrategyMode.CRITICAL)


if __name__ == "__main__":
    unittest.main()