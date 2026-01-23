"""
Engine Uncertainty Quantifier: 동적 불확실성 정량화 모듈
Step 7 & 8: Meta-Cognition & Intuition Support

이 모듈은 시스템이 현재 마주한 상황이나 데이터에 대해 '자신이 얼마나 모르는지(Epistemic Uncertainty)'를
수치적으로 정량화한다. 이는 DecisionGate가 직관(System 1)을 신뢰할지 결정하는 핵심 지표가 된다.

Intention Goal: "지식의 한계와 경계를 식별하기 위한 동적 불확실성 정량화 알고리즘 개발"

Architecture:
    PatternRecognizer (Familiarity) + MetaEvaluator (Complexity)
        ↓ Inputs
    UncertaintyQuantifier (This Module)
        ↓
    UncertaintyProfile (Score, State, Boundary Type)
        ↓
    DecisionGate / MetaMonitor

Usage:
    from engine.uncertainty_quantifier import UncertaintyQuantifier
    
    quantifier = UncertaintyQuantifier()
    profile = quantifier.quantify(familiarity=0.4, complexity=0.8, conflict_rate=0.1)
    
    if profile.state == KnowledgeState.UNKNOWN:
        # Switch to Slow Path (Reasoning)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime


class KnowledgeState(Enum):
    """지식 상태 분류"""
    KNOWN = "known"
    FRONTIER = "frontier"
    UNKNOWN = "unknown"
    ANOMALY = "anomaly"


class BoundaryType(Enum):
    """지식 경계 유형"""
    SAFE_ZONE = "safe_zone"
    EXPLORATION_EDGE = "exploration_edge"
    TERRA_INCOGNITA = "terra_incognita"
    CONTRADICTION_ZONE = "contradiction_zone"


@dataclass
class UncertaintyProfile:
    """불확실성 분석 결과"""
    score: float
    state: KnowledgeState
    boundary_type: BoundaryType
    primary_factor: str
    reasoning: str
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class UncertaintyQuantifier:
    """
    동적 불확실성 정량화기
    
    다양한 인지 지표를 통합하여 Epistemic Uncertainty(인식적 불확실성)를 계산한다.
    이 점수는 DecisionGate가 System 1(직관)과 System 2(추론) 중 어떤 경로를
    선택할지 결정하는 핵심 기준이 된다.
    
    수학적 모델:
        uncertainty = w1 * (1 - familiarity) + w2 * complexity + w3 * conflict_rate
        
    여기서:
    """
    
    WEIGHT_FAMILIARITY = 0.5
    WEIGHT_COMPLEXITY = 0.3
    WEIGHT_CONFLICT = 0.2
    
    THRESHOLD_KNOWN = 0.3
    THRESHOLD_FRONTIER = 0.6
    THRESHOLD_UNKNOWN = 0.85
    
    CONFLICT_AMPLIFIER = 1.5

    def __init__(
        self,
        weight_familiarity: float = None,
        weight_complexity: float = None,
        weight_conflict: float = None
    ):
        """
        UncertaintyQuantifier 초기화
        
        Args:
            weight_familiarity: 익숙함 가중치 (기본값: 0.5)
            weight_complexity: 복잡도 가중치 (기본값: 0.3)
            weight_conflict: 충돌률 가중치 (기본값: 0.2)
        """
        if weight_familiarity is not None:
            self.WEIGHT_FAMILIARITY = weight_familiarity
        if weight_complexity is not None:
            self.WEIGHT_COMPLEXITY = weight_complexity
        if weight_conflict is not None:
            self.WEIGHT_CONFLICT = weight_conflict
        
        self._history: List[UncertaintyProfile] = []
        self._max_history = 100

    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """값을 지정된 범위로 제한"""
        return max(min_val, min(max_val, value))

    def quantify(
        self, 
        familiarity_score: float, 
        complexity_score: float, 
        conflict_rate: float = 0.0,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> UncertaintyProfile:
        """
        불확실성 정량화 계산
        
        Args:
            familiarity_score (0.0~1.0): 패턴 인식 익숙함 (1.0 = 매우 익숙)
            complexity_score (0.0~1.0): 문제 복잡도 (1.0 = 매우 복잡)
            conflict_rate (0.0~1.0): 내부 정보/기억 간 충돌 비율
            context_metadata: 추가 컨텍스트 정보 (선택적)
            
        Returns:
            UncertaintyProfile: 불확실성 분석 결과
        """
        familiarity = self._clamp(familiarity_score)
        complexity = self._clamp(complexity_score)
        conflict = self._clamp(conflict_rate)
        
        unfamiliarity = 1.0 - familiarity
        
        base_score = (
            (unfamiliarity * self.WEIGHT_FAMILIARITY) +
            (complexity * self.WEIGHT_COMPLEXITY) +
            (conflict * self.WEIGHT_CONFLICT)
        )
        
        if conflict > 0.5:
            conflict_boost = (conflict - 0.5) * self.CONFLICT_AMPLIFIER * self.WEIGHT_CONFLICT
            base_score = min(1.0, base_score + conflict_boost)
        
        factors = {
            "unfamiliarity": round(unfamiliarity * self.WEIGHT_FAMILIARITY, 4),
            "complexity": round(complexity * self.WEIGHT_COMPLEXITY, 4),
            "conflict": round(conflict * self.WEIGHT_CONFLICT, 4)
        }
        primary_factor = max(factors, key=factors.get)
        
        state, boundary_type, reason = self._determine_state(
            base_score, unfamiliarity, complexity, conflict, primary_factor
        )
        
        profile = UncertaintyProfile(
            score=round(base_score, 4),
            state=state,
            boundary_type=boundary_type,
            primary_factor=primary_factor,
            reasoning=reason,
            factors=factors
        )
        
        self._record_history(profile)
        
        return profile

    def _determine_state(
        self,
        score: float,
        unfamiliarity: float,
        complexity: float,
        conflict: float,
        primary_factor: str
    ) -> tuple:
        """점수와 요인을 기반으로 지식 상태 및 경계 유형 결정"""
        
        if conflict > 0.7:
            return (
                KnowledgeState.ANOMALY,
                BoundaryType.CONTRADICTION_ZONE,
                f"High conflict rate ({conflict:.2f}) indicates contradictory information. Requires careful audit."
            )
        
        if score < self.THRESHOLD_KNOWN:
            return (
                KnowledgeState.KNOWN,
                BoundaryType.SAFE_ZONE,
                f"High familiarity and low complexity. Safe for System 1 (Intuition/Reflex)."
            )
        
        if score < self.THRESHOLD_FRONTIER:
            factor_explanation = self._get_factor_explanation(primary_factor, unfamiliarity, complexity, conflict)
            return (
                KnowledgeState.FRONTIER,
                BoundaryType.EXPLORATION_EDGE,
                f"Knowledge boundary detected. {factor_explanation} Verification recommended before action."
            )
        
        if score < self.THRESHOLD_UNKNOWN:
            factor_explanation = self._get_factor_explanation(primary_factor, unfamiliarity, complexity, conflict)
            return (
                KnowledgeState.UNKNOWN,
                BoundaryType.TERRA_INCOGNITA,
                f"Unfamiliar territory. {factor_explanation} System 2 (Deep Reasoning) required."
            )
        
        return (
            KnowledgeState.ANOMALY,
            BoundaryType.CONTRADICTION_ZONE,
            f"Critical uncertainty level ({score:.2f}). Multiple factors contribute to high risk."
        )

    def _get_factor_explanation(
        self,
        primary_factor: str,
        unfamiliarity: float,
        complexity: float,
        conflict: float
    ) -> str:
        """주요 요인에 대한 설명 생성"""
        explanations = {
            "unfamiliarity": f"Low familiarity ({1-unfamiliarity:.2f}) is the primary concern.",
            "complexity": f"High complexity ({complexity:.2f}) increases uncertainty.",
            "conflict": f"Information conflict ({conflict:.2f}) detected."
        }
        return explanations.get(primary_factor, "Multiple factors contribute.")

    def _record_history(self, profile: UncertaintyProfile) -> None:
        """불확실성 프로필을 히스토리에 기록"""
        self._history.append(profile)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def assess_risk(self, profile: UncertaintyProfile) -> str:
        """불확실성 프로필에 기반한 리스크 평가"""
        risk_mapping = {
            KnowledgeState.KNOWN: "LOW_RISK",
            KnowledgeState.FRONTIER: "MODERATE_RISK",
            KnowledgeState.UNKNOWN: "HIGH_RISK",
            KnowledgeState.ANOMALY: "CRITICAL_RISK"
        }
        return risk_mapping.get(profile.state, "UNKNOWN_RISK")

    def get_decision_recommendation(self, profile: UncertaintyProfile) -> Dict[str, Any]:
        """
        불확실성 프로필에 기반한 의사결정 경로 추천
        
        DecisionGate가 이 추천을 참고하여 System 1/2 경로를 선택한다.
        
        Returns:
            Dict containing:
        """
        if profile.state == KnowledgeState.KNOWN:
            return {
                "recommended_path": "system_1",
                "confidence": 1.0 - profile.score,
                "rationale": "High certainty allows fast intuitive response.",
                "allow_reflex": True
            }
        
        if profile.state == KnowledgeState.FRONTIER:
            return {
                "recommended_path": "system_2",
                "confidence": 0.5 + (0.5 - profile.score),
                "rationale": "Boundary zone requires verification before action.",
                "allow_reflex": False
            }
        
        return {
            "recommended_path": "system_2",
            "confidence": max(0.3, 1.0 - profile.score),
            "rationale": f"High uncertainty ({profile.score:.2f}) requires deep reasoning.",
            "allow_reflex": False
        }

    def get_trend_analysis(self, window_size: int = 10) -> Dict[str, Any]:
        """
        최근 불확실성 추세 분석
        
        Args:
            window_size: 분석할 최근 기록 수
            
        Returns:
            추세 분석 결과 (평균, 변화율, 지배적 상태 등)
        """
        if not self._history:
            return {
                "average_score": 0.0,
                "trend": "stable",
                "dominant_state": None,
                "sample_count": 0
            }
        
        recent = self._history[-window_size:]
        scores = [p.score for p in recent]
        states = [p.state for p in recent]
        
        avg_score = sum(scores) / len(scores)
        
        if len(scores) >= 3:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            diff = second_half - first_half
            
            if diff > 0.1:
                trend = "increasing"
            elif diff < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        state_counts = {}
        for s in states:
            state_counts[s] = state_counts.get(s, 0) + 1
        dominant_state = max(state_counts, key=state_counts.get) if state_counts else None
        
        return {
            "average_score": round(avg_score, 4),
            "trend": trend,
            "dominant_state": dominant_state.value if dominant_state else None,
            "sample_count": len(recent),
            "state_distribution": {k.value: v for k, v in state_counts.items()}
        }

    def reset_history(self) -> None:
        """히스토리 초기화"""
        self._history.clear()


def get_uncertainty_quantifier() -> UncertaintyQuantifier:
    """UncertaintyQuantifier 싱글톤 인스턴스 반환"""
    if not hasattr(get_uncertainty_quantifier, "_instance"):
        get_uncertainty_quantifier._instance = UncertaintyQuantifier()
    return get_uncertainty_quantifier._instance