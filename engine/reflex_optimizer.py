"""
Engine Reflex Optimizer: 반사 행동 최적화 및 관리
Step 7 & 8: Meta-Cognition applied to Intuition

이 모듈은 학습된 반사 행동(Learned Reflexes)의 효율성을 분석하고,
사용되지 않거나 신뢰도가 낮은 반사 행동을 식별하여 '망각(Pruning)' 또는 '재학습(Retrain)'을 제안한다.
시스템의 직관(Intuition)이 비대해지거나 부정확해지는 것을 방지하는 자가 정화 메커니즘이다.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class OptimizationAction(Enum):
    """최적화 제안 액션"""
    KEEP = "keep"
    PRUNE = "prune"
    RETRAIN = "retrain"
    MONITOR = "monitor"


@dataclass
class OptimizationRecommendation:
    """최적화 제안 결과"""
    reflex_id: str
    action: OptimizationAction
    reason: str
    efficiency_score: float


class ReflexOptimizer:
    """
    반사 행동 최적화기
    
    메타인지적 기준(효용성, 신뢰성)을 적용하여 직관 시스템을 최적화한다.
    """

    def __init__(
        self, 
        min_usage_threshold: int = 3,
        min_confidence_threshold: float = 0.6,
        grace_period_days: int = 7
    ):
        self.min_usage_threshold = min_usage_threshold
        self.min_confidence_threshold = min_confidence_threshold
        self.grace_period_days = grace_period_days

    def analyze_reflexes(self, reflexes: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """
        반사 행동 목록을 분석하여 최적화 제안을 생성한다.
        
        Args:
            reflexes: 반사 행동 딕셔너리 리스트 (ReflexStore 또는 Memory에서 로드됨)
            
        Returns:
            제안 목록
        """
        recommendations = []
        now = datetime.now()

        for reflex in reflexes:
            rec = self._evaluate_single_reflex(reflex, now)
            recommendations.append(rec)

        return recommendations

    def _evaluate_single_reflex(
        self, 
        reflex: Dict[str, Any], 
        now: datetime
    ) -> OptimizationRecommendation:
        """단일 반사 행동 평가"""
        reflex_id = reflex.get("name") or reflex.get("id") or "unknown"
        usage_count = reflex.get("usage_count", 0)
        confidence = reflex.get("confidence", 0.0)
        created_at_str = reflex.get("created_at")
        
        created_at = None
        if created_at_str:
            try:
                if isinstance(created_at_str, str):
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                elif isinstance(created_at_str, datetime):
                    created_at = created_at_str
            except (ValueError, TypeError):
                pass

        if confidence < self.min_confidence_threshold:
            return OptimizationRecommendation(
                reflex_id=reflex_id,
                action=OptimizationAction.RETRAIN,
                reason="Low confidence ({:.2f} < {:.2f})".format(confidence, self.min_confidence_threshold),
                efficiency_score=confidence
            )

        if created_at:
            try:
                created_at_naive = created_at.replace(tzinfo=None)
                age_days = (now - created_at_naive).days
            except (AttributeError, TypeError):
                age_days = self.grace_period_days + 1
            
            if age_days < self.grace_period_days:
                return OptimizationRecommendation(
                    reflex_id=reflex_id,
                    action=OptimizationAction.KEEP,
                    reason="Within grace period",
                    efficiency_score=1.0
                )

        if usage_count < self.min_usage_threshold:
            return OptimizationRecommendation(
                reflex_id=reflex_id,
                action=OptimizationAction.PRUNE,
                reason="Stale reflex (Usage {} < {})".format(usage_count, self.min_usage_threshold),
                efficiency_score=0.1 * usage_count
            )

        efficiency = min(1.0, 0.5 + (confidence * 0.3) + (min(usage_count, 10) * 0.02))
        return OptimizationRecommendation(
            reflex_id=reflex_id,
            action=OptimizationAction.KEEP,
            reason="Healthy usage and confidence",
            efficiency_score=efficiency
        )

    def get_pruning_candidates(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """제거(Prune) 추천 대상 ID 목록 반환"""
        return [r.reflex_id for r in recommendations if r.action == OptimizationAction.PRUNE]

    def get_retraining_candidates(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """재학습(Retrain) 추천 대상 ID 목록 반환"""
        return [r.reflex_id for r in recommendations if r.action == OptimizationAction.RETRAIN]

    def get_optimization_summary(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, Any]:
        """
        최적화 제안에 대한 요약 통계를 반환한다.
        
        Args:
            recommendations: 최적화 제안 목록
            
        Returns:
            요약 딕셔너리 (총 개수, 액션별 개수, 평균 효율성 점수)
        """
        if not recommendations:
            return {
                "total_count": 0,
                "action_counts": {},
                "avg_efficiency": 0.0,
                "pruning_candidates": [],
                "retraining_candidates": []
            }
        
        action_counts = {}
        total_efficiency = 0.0
        
        for rec in recommendations:
            action_name = rec.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
            total_efficiency += rec.efficiency_score
        
        avg_efficiency = total_efficiency / len(recommendations)
        
        return {
            "total_count": len(recommendations),
            "action_counts": action_counts,
            "avg_efficiency": round(avg_efficiency, 4),
            "pruning_candidates": self.get_pruning_candidates(recommendations),
            "retraining_candidates": self.get_retraining_candidates(recommendations)
        }

    def apply_pruning(self, reflex_store, candidates: List[str]) -> int:
        """
        제거 대상 반사 행동을 실제로 삭제한다.
        
        Args:
            reflex_store: ReflexStore 인스턴스
            candidates: 삭제할 반사 행동 ID 목록
            
        Returns:
            삭제된 반사 행동 개수
        """
        deleted_count = 0
        
        for reflex_id in candidates:
            try:
                if hasattr(reflex_store, 'delete_reflex'):
                    success = reflex_store.delete_reflex(reflex_id)
                    if success:
                        deleted_count += 1
                        print("Pruned stale reflex: {}".format(reflex_id))
            except Exception as e:
                print("Failed to prune reflex {}: {}".format(reflex_id, e))
        
        return deleted_count


_reflex_optimizer_instance: Optional[ReflexOptimizer] = None


def get_reflex_optimizer(
    min_usage_threshold: int = 3,
    min_confidence_threshold: float = 0.6,
    grace_period_days: int = 7
) -> ReflexOptimizer:
    """
    ReflexOptimizer 싱글톤 인스턴스를 반환한다.
    
    Args:
        min_usage_threshold: 최소 사용 횟수 임계값
        min_confidence_threshold: 최소 신뢰도 임계값
        grace_period_days: 유예 기간 (일)
    
    Returns:
        ReflexOptimizer: 싱글톤 인스턴스
    """
    global _reflex_optimizer_instance
    if _reflex_optimizer_instance is None:
        _reflex_optimizer_instance = ReflexOptimizer(
            min_usage_threshold=min_usage_threshold,
            min_confidence_threshold=min_confidence_threshold,
            grace_period_days=grace_period_days
        )
    return _reflex_optimizer_instance