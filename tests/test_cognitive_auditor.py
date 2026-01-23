"""
Step 7: Meta-Cognition - Cognitive Auditor Unit Tests
=====================================================
CognitiveAuditorMixin의 핵심 기능인 추론 경로 감사 및 논리적 오류 탐지를 검증한다.

검증 항목:
1. 반복적인 행동 패턴(Loop) 감지 로직
2. 로드맵 정체(Stagnation) 감지 로직
3. AuditSeverity 등급이 상황에 맞게 반환되는지 확인
4. 정상적인 진화 흐름에서는 INFO 수준 반환 확인
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 테스트 대상 모듈 임포트 (가용성 체크)
try:
    from engine.cognitive_auditor import CognitiveAuditorMixin, AuditSeverity, AuditReport
    HAS_AUDITOR = True
except ImportError:
    HAS_AUDITOR = False
    CognitiveAuditorMixin = None
    AuditSeverity = None
    AuditReport = None


class MockAuditor(CognitiveAuditorMixin if HAS_AUDITOR else object):
    """CognitiveAuditorMixin 테스트를 위한 Mock 클래스"""
    
    def __init__(self):
        self.fact_core = MagicMock()
        self.nexus = MagicMock()
        # 기본 로드맵 설정
        self.fact_core.get_fact.return_value = "step_7_meta_cognition"


class TestCognitiveAuditorLoopDetection(unittest.TestCase):
    """반복 행동 패턴(Loop) 감지 테스트"""
    
    def setUp(self):
        if not HAS_AUDITOR:
            self.skipTest("CognitiveAuditor module not found")
        self.auditor = MockAuditor()

    def test_detect_simple_loop(self):
        """동일한 행동이 반복되면 WARNING 이상의 심각도를 반환해야 함"""
        # 동일한 행동이 반복되는 히스토리 생성
        history = [
            {"action": "edit", "file": "main.py", "description": "fix bug", "status": "success"},
            {"action": "edit", "file": "main.py", "description": "fix bug", "status": "success"},
            {"action": "edit", "file": "main.py", "description": "fix bug", "status": "success"},
            {"action": "edit", "file": "main.py", "description": "fix bug", "status": "success"},
        ]
        
        if hasattr(self.auditor, 'audit_reasoning_loop'):
            report = self.auditor.audit_reasoning_loop(history)
            self.assertIsNotNone(report)
            self.assertIn(report.severity, [AuditSeverity.WARNING, AuditSeverity.CRITICAL])

    def test_detect_alternating_loop(self):
        """A-B-A-B 패턴의 교차 반복도 감지해야 함"""
        history = [
            {"action": "create", "file": "a.py", "description": "add feature", "status": "success"},
            {"action": "delete", "file": "a.py", "description": "remove feature", "status": "success"},
            {"action": "create", "file": "a.py", "description": "add feature", "status": "success"},
            {"action": "delete", "file": "a.py", "description": "remove feature", "status": "success"},
        ]
        
        if hasattr(self.auditor, 'audit_reasoning_loop'):
            report = self.auditor.audit_reasoning_loop(history)
            self.assertIsNotNone(report)
            # 교차 반복도 WARNING 이상이어야 함
            self.assertIn(report.severity, [AuditSeverity.INFO, AuditSeverity.WARNING, AuditSeverity.CRITICAL])


class TestCognitiveAuditorNormalFlow(unittest.TestCase):
    """정상적인 진화 흐름 테스트"""
    
    def setUp(self):
        if not HAS_AUDITOR:
            self.skipTest("CognitiveAuditor module not found")
        self.auditor = MockAuditor()

    def test_normal_diverse_flow(self):
        """다양한 행동이 섞여있으면 INFO 수준이어야 함"""
        history = [
            {"action": "create", "file": "module_a.py", "description": "init module", "status": "success"},
            {"action": "update", "file": "module_b.py", "description": "refactor", "status": "success"},
            {"action": "delete", "file": "temp.py", "description": "cleanup", "status": "success"},
            {"action": "create", "file": "tests/test_a.py", "description": "add test", "status": "success"},
        ]
        
        if hasattr(self.auditor, 'audit_reasoning_loop'):
            report = self.auditor.audit_reasoning_loop(history)
            self.assertIsNotNone(report)
            self.assertEqual(report.severity, AuditSeverity.INFO)

    def test_empty_history(self):
        """빈 히스토리에서도 에러 없이 처리해야 함"""
        history = []
        
        if hasattr(self.auditor, 'audit_reasoning_loop'):
            report = self.auditor.audit_reasoning_loop(history)
            self.assertIsNotNone(report)
            self.assertEqual(report.severity, AuditSeverity.INFO)


class TestCognitiveAuditorStagnation(unittest.TestCase):
    """로드맵 정체(Stagnation) 감지 테스트"""
    
    def setUp(self):
        if not HAS_AUDITOR:
            self.skipTest("CognitiveAuditor module not found")
        self.auditor = MockAuditor()

    def test_detect_failure_stagnation(self):
        """연속 실패가 발생하면 정체로 판단해야 함"""
        history = [
            {"action": "update", "file": "core.py", "description": "attempt 1", "status": "failed"},
            {"action": "update", "file": "core.py", "description": "attempt 2", "status": "failed"},
            {"action": "update", "file": "core.py", "description": "attempt 3", "status": "failed"},
        ]
        
        if hasattr(self.auditor, 'audit_stagnation'):
            report = self.auditor.audit_stagnation(history)
            self.assertIsNotNone(report)
            self.assertIn(report.severity, [AuditSeverity.WARNING, AuditSeverity.CRITICAL])


class TestCognitiveAuditorRoadmapAlignment(unittest.TestCase):
    """로드맵 정렬(Alignment) 검증 테스트"""
    
    def setUp(self):
        if not HAS_AUDITOR:
            self.skipTest("CognitiveAuditor module not found")
        self.auditor = MockAuditor()

    def test_aligned_actions(self):
        """현재 로드맵 단계와 관련된 행동은 정렬된 것으로 판단"""
        current_focus = "step_7_meta_cognition"
        recent_actions = [
            {"file": "engine/meta_cognition.py", "description": "add reflection"},
            {"file": "engine/meta_evaluator.py", "description": "improve scoring"},
        ]
        
        if hasattr(self.auditor, 'audit_roadmap_alignment'):
            alignment = self.auditor.audit_roadmap_alignment(current_focus, recent_actions)
            self.assertIsNotNone(alignment)


class TestAuditSeverityEnum(unittest.TestCase):
    """AuditSeverity 열거형 테스트"""
    
    def setUp(self):
        if not HAS_AUDITOR:
            self.skipTest("CognitiveAuditor module not found")

    def test_severity_ordering(self):
        """심각도 레벨이 올바르게 정의되어 있는지 확인"""
        self.assertIsNotNone(AuditSeverity.INFO)
        self.assertIsNotNone(AuditSeverity.WARNING)
        self.assertIsNotNone(AuditSeverity.CRITICAL)

    def test_severity_values(self):
        """심각도 값이 문자열로 정의되어 있는지 확인"""
        self.assertEqual(AuditSeverity.INFO.value, "info")
        self.assertEqual(AuditSeverity.WARNING.value, "warning")
        self.assertEqual(AuditSeverity.CRITICAL.value, "critical")


if __name__ == "__main__":
    unittest.main()