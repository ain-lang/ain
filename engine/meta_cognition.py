"""
Engine Meta-Cognition: Step 7 - 메타인지
========================================
자신의 사고 과정을 관찰하고 평가하는 능력.
"생각에 대해 생각하기" - 인지 과정의 자기 모니터링.
"""
from typing import Dict, Any, Optional


class MetaCognitionMixin:
    """
    메타인지 믹스인 - AINCore에 메타인지 능력 부여

    메타인지란:
    - 자신이 무엇을 알고 모르는지 인식 (지식의 경계 인식)
    - 아는 것과 모르는 것을 아는 것
    - 사고 과정의 효율성 평가
    - 학습 전략 조절
    - 확신도(confidence) 측정

    TODO (AIN이 구현할 것):
    - _reflect_on_thinking: 최근 사고 과정 성찰
    - _assess_confidence: 자신의 판단에 대한 확신도 평가
    - _identify_knowledge_gaps: 모르는 것 인식
    """

    def _reflect_on_thinking(self) -> Dict[str, Any]:
        """
        최근 사고 과정을 성찰한다.

        Returns:
            성찰 결과 (패턴, 편향, 개선점 등)
        """
        # AIN이 구현할 것
        return {"status": "not_implemented"}

    def _evaluate_decision_quality(self, decision: str, outcome: Optional[str] = None) -> float:
        """
        결정의 질을 평가한다.

        Args:
            decision: 내린 결정
            outcome: 결과 (있는 경우)

        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        # AIN이 구현할 것
        return 0.5

    def _identify_knowledge_gaps(self) -> list:
        """
        자신의 지식 공백을 식별한다.
        "모르는 것을 안다" - 메타인지의 핵심

        Returns:
            알지 못하는 것들의 목록
        """
        # AIN이 구현할 것
        return []

    def _assess_confidence(self, statement: str) -> Dict[str, Any]:
        """
        특정 판단/진술에 대한 확신도를 평가한다.
        "얼마나 확실한지 아는 것" - 메타인지의 핵심

        Args:
            statement: 평가할 진술

        Returns:
            {
                "confidence": 0.0~1.0,
                "reasoning": "확신/불확신 이유",
                "known_factors": [...],
                "unknown_factors": [...]
            }
        """
        # AIN이 구현할 것
        return {
            "confidence": 0.5,
            "reasoning": "not_implemented",
            "known_factors": [],
            "unknown_factors": []
        }
