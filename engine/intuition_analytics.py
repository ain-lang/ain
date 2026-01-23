"""
Engine Intuition Analytics: 직관 시스템 분석 및 모니터링
Step 8 & 7: Intuition + Meta-Cognition Integration

이 모듈은 Intuition System(System 1)과 Reasoning System(System 2) 사이의
실행 비율, Reflex 성공률, 결정 신뢰도 분포를 추적하고 분석한다.

Meta-Cognition 시스템은 이 분석 데이터를 통해:
1. 직관의 신뢰도를 평가하고 (System 1이 너무 과신하지 않는지)
2. 추론으로 넘어가야 할 때를 더 잘 판단하도록 튜닝할 수 있다.

Architecture:
    DecisionGate / ReflexExecutor
        ↓ (Event Recording)
    IntuitionAnalytics (이 모듈)
        ↓ (Report Generation)
    MetaMonitor / Dashboard

Usage:
    from engine.intuition_analytics import IntuitionAnalytics
    
    analytics = IntuitionAnalytics()
    analytics.record_decision(path="system_1_reflex", confidence=0.85)
    analytics.record_outcome(reflex_id="fix_typo", success=True)
    report = analytics.get_analytics_report()
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque, Counter
from enum import Enum
import statistics


class DecisionPath(Enum):
    """결정 경로 열거형"""
    SYSTEM_1_REFLEX = "system_1_reflex"
    SYSTEM_2_EVOLUTION = "system_2_evolution"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


@dataclass
class IntuitionEvent:
    """직관/추론 결정 이벤트"""
    timestamp: datetime
    path: str
    confidence: float
    trigger: str
    context_hash: str = ""


@dataclass
class ReflexOutcome:
    """반사 행동 실행 결과"""
    timestamp: datetime
    reflex_id: str
    success: bool
    latency_ms: float
    error_message: str = ""


@dataclass
class AnalyticsSnapshot:
    """특정 시점의 분석 스냅샷"""
    timestamp: datetime
    system_1_ratio: float
    system_2_ratio: float
    reflex_success_rate: float
    avg_confidence: float
    total_decisions: int
    total_reflexes: int


class IntuitionAnalytics:
    """
    직관 시스템 분석기
    
    System 1(Reflex)과 System 2(Evolution)의 균형과 성과를 추적한다.
    싱글톤 패턴으로 시스템 전역에서 공유된다.
    
    Features:
    """
    
    _instance: Optional["IntuitionAnalytics"] = None
    MAX_HISTORY = 1000
    SNAPSHOT_INTERVAL_MINUTES = 30
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.decision_history: deque = deque(maxlen=self.MAX_HISTORY)
        self.outcome_history: deque = deque(maxlen=self.MAX_HISTORY)
        self.snapshots: deque = deque(maxlen=100)
        
        self._path_counter: Counter = Counter()
        self._reflex_success_counter: Counter = Counter()
        self._reflex_total_counter: Counter = Counter()
        self._confidence_buckets: Dict[str, int] = {
            "very_low": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0
        }
        
        self._last_snapshot_time: Optional[datetime] = None
        self._total_latency_ms: float = 0.0
        self._latency_count: int = 0
        
        self._initialized = True
        print("📊 Intuition Analytics initialized.")

    def record_decision(
        self, 
        path: str, 
        confidence: float, 
        trigger: str = "unknown",
        context_hash: str = ""
    ) -> None:
        """
        System 1 vs System 2 결정 기록
        
        Args:
            path: 선택된 경로 (system_1_reflex, system_2_evolution)
            confidence: 결정 신뢰도 (0.0 ~ 1.0)
            trigger: 결정을 유발한 패턴 또는 컨텍스트
            context_hash: 컨텍스트 해시 (중복 감지용)
        """
        event = IntuitionEvent(
            timestamp=datetime.now(),
            path=path,
            confidence=confidence,
            trigger=trigger,
            context_hash=context_hash
        )
        self.decision_history.append(event)
        
        self._path_counter[path] += 1
        self._update_confidence_bucket(confidence)
        self._maybe_take_snapshot()

    def record_outcome(
        self, 
        reflex_id: str, 
        success: bool, 
        latency_ms: float = 0.0,
        error_message: str = ""
    ) -> None:
        """
        Reflex 실행 결과 기록
        
        Args:
            reflex_id: 반사 행동 식별자
            success: 성공 여부
            latency_ms: 실행 지연 시간 (밀리초)
            error_message: 실패 시 에러 메시지
        """
        outcome = ReflexOutcome(
            timestamp=datetime.now(),
            reflex_id=reflex_id,
            success=success,
            latency_ms=latency_ms,
            error_message=error_message
        )
        self.outcome_history.append(outcome)
        
        self._reflex_total_counter[reflex_id] += 1
        if success:
            self._reflex_success_counter[reflex_id] += 1
        
        self._total_latency_ms += latency_ms
        self._latency_count += 1

    def _update_confidence_bucket(self, confidence: float) -> None:
        """신뢰도를 구간별로 분류"""
        if confidence < 0.2:
            self._confidence_buckets["very_low"] += 1
        elif confidence < 0.4:
            self._confidence_buckets["low"] += 1
        elif confidence < 0.6:
            self._confidence_buckets["medium"] += 1
        elif confidence < 0.8:
            self._confidence_buckets["high"] += 1
        else:
            self._confidence_buckets["very_high"] += 1

    def _maybe_take_snapshot(self) -> None:
        """주기적으로 스냅샷 생성"""
        now = datetime.now()
        if self._last_snapshot_time is None:
            self._last_snapshot_time = now
            return
        
        elapsed = now - self._last_snapshot_time
        if elapsed >= timedelta(minutes=self.SNAPSHOT_INTERVAL_MINUTES):
            snapshot = self._create_snapshot()
            self.snapshots.append(snapshot)
            self._last_snapshot_time = now

    def _create_snapshot(self) -> AnalyticsSnapshot:
        """현재 상태의 스냅샷 생성"""
        total_decisions = sum(self._path_counter.values())
        system_1_count = self._path_counter.get("system_1_reflex", 0)
        system_2_count = self._path_counter.get("system_2_evolution", 0)
        
        system_1_ratio = system_1_count / max(total_decisions, 1)
        system_2_ratio = system_2_count / max(total_decisions, 1)
        
        total_reflexes = sum(self._reflex_total_counter.values())
        total_successes = sum(self._reflex_success_counter.values())
        reflex_success_rate = total_successes / max(total_reflexes, 1)
        
        confidences = [e.confidence for e in self.decision_history]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        return AnalyticsSnapshot(
            timestamp=datetime.now(),
            system_1_ratio=system_1_ratio,
            system_2_ratio=system_2_ratio,
            reflex_success_rate=reflex_success_rate,
            avg_confidence=avg_confidence,
            total_decisions=total_decisions,
            total_reflexes=total_reflexes
        )

    def get_analytics_report(self) -> Dict[str, Any]:
        """
        현재 직관 시스템 상태 분석 리포트 반환
        
        Returns:
            분석 리포트 딕셔너리
        """
        if not self.decision_history:
            return {"status": "insufficient_data", "message": "No decisions recorded yet"}
        
        total_decisions = sum(self._path_counter.values())
        system_1_count = self._path_counter.get("system_1_reflex", 0)
        system_2_count = self._path_counter.get("system_2_evolution", 0)
        
        total_reflexes = sum(self._reflex_total_counter.values())
        total_successes = sum(self._reflex_success_counter.values())
        
        confidences = [e.confidence for e in self.decision_history]
        
        avg_latency = (
            self._total_latency_ms / self._latency_count 
            if self._latency_count > 0 else 0.0
        )
        
        report = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "decision_stats": {
                "total_decisions": total_decisions,
                "system_1_count": system_1_count,
                "system_2_count": system_2_count,
                "system_1_ratio": round(system_1_count / max(total_decisions, 1), 4),
                "system_2_ratio": round(system_2_count / max(total_decisions, 1), 4),
                "path_distribution": dict(self._path_counter)
            },
            "reflex_stats": {
                "total_executions": total_reflexes,
                "total_successes": total_successes,
                "success_rate": round(total_successes / max(total_reflexes, 1), 4),
                "avg_latency_ms": round(avg_latency, 2),
                "per_reflex_stats": self._get_per_reflex_stats()
            },
            "confidence_stats": {
                "mean": round(statistics.mean(confidences), 4) if confidences else 0.0,
                "median": round(statistics.median(confidences), 4) if confidences else 0.0,
                "stdev": round(statistics.stdev(confidences), 4) if len(confidences) > 1 else 0.0,
                "min": round(min(confidences), 4) if confidences else 0.0,
                "max": round(max(confidences), 4) if confidences else 0.0,
                "distribution": dict(self._confidence_buckets)
            },
            "health_indicators": self._calculate_health_indicators(),
            "recommendations": self._generate_recommendations()
        }
        
        return report

    def _get_per_reflex_stats(self) -> Dict[str, Dict[str, Any]]:
        """개별 Reflex별 통계 반환"""
        stats = {}
        for reflex_id in self._reflex_total_counter:
            total = self._reflex_total_counter[reflex_id]
            successes = self._reflex_success_counter.get(reflex_id, 0)
            stats[reflex_id] = {
                "total": total,
                "successes": successes,
                "success_rate": round(successes / max(total, 1), 4)
            }
        return stats

    def _calculate_health_indicators(self) -> Dict[str, Any]:
        """시스템 건강 지표 계산"""
        total_decisions = sum(self._path_counter.values())
        system_1_ratio = self._path_counter.get("system_1_reflex", 0) / max(total_decisions, 1)
        
        total_reflexes = sum(self._reflex_total_counter.values())
        total_successes = sum(self._reflex_success_counter.values())
        success_rate = total_successes / max(total_reflexes, 1)
        
        intuition_overconfidence = system_1_ratio > 0.8 and success_rate < 0.7
        intuition_underutilized = system_1_ratio < 0.1 and total_decisions > 50
        reflex_degradation = success_rate < 0.5 and total_reflexes > 20
        
        health_score = 1.0
        if intuition_overconfidence:
            health_score -= 0.3
        if reflex_degradation:
            health_score -= 0.4
        if intuition_underutilized:
            health_score -= 0.1
        
        return {
            "health_score": round(max(health_score, 0.0), 2),
            "intuition_overconfidence": intuition_overconfidence,
            "intuition_underutilized": intuition_underutilized,
            "reflex_degradation": reflex_degradation,
            "balance_status": self._get_balance_status(system_1_ratio)
        }

    def _get_balance_status(self, system_1_ratio: float) -> str:
        """System 1/2 균형 상태 판단"""
        if system_1_ratio < 0.2:
            return "reasoning_heavy"
        elif system_1_ratio < 0.4:
            return "balanced_reasoning"
        elif system_1_ratio < 0.6:
            return "balanced"
        elif system_1_ratio < 0.8:
            return "balanced_intuition"
        else:
            return "intuition_heavy"

    def _generate_recommendations(self) -> List[str]:
        """개선 권고사항 생성"""
        recommendations = []
        
        health = self._calculate_health_indicators()
        
        if health["intuition_overconfidence"]:
            recommendations.append(
                "System 1(직관)이 과신하고 있습니다. "
                "DecisionGate의 신뢰도 임계값을 높이는 것을 고려하세요."
            )
        
        if health["reflex_degradation"]:
            recommendations.append(
                "Reflex 성공률이 낮습니다. "
                "ReflexOptimizer를 통해 비효율적인 반사 행동을 정리하세요."
            )
        
        if health["intuition_underutilized"]:
            recommendations.append(
                "직관 시스템이 충분히 활용되지 않고 있습니다. "
                "더 많은 패턴을 학습하여 System 1 커버리지를 확대하세요."
            )
        
        if not recommendations:
            recommendations.append("시스템이 정상적으로 균형을 유지하고 있습니다.")
        
        return recommendations

    def get_trend_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        시계열 트렌드 리포트 생성
        
        Args:
            hours: 분석할 시간 범위
        
        Returns:
            트렌드 분석 리포트
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_decisions = [
            e for e in self.decision_history 
            if e.timestamp >= cutoff
        ]
        
        recent_outcomes = [
            o for o in self.outcome_history 
            if o.timestamp >= cutoff
        ]
        
        if not recent_decisions:
            return {"status": "insufficient_data", "period_hours": hours}
        
        hourly_buckets: Dict[int, List[IntuitionEvent]] = {}
        for event in recent_decisions:
            hour_key = event.timestamp.hour
            if hour_key not in hourly_buckets:
                hourly_buckets[hour_key] = []
            hourly_buckets[hour_key].append(event)
        
        hourly_stats = {}
        for hour, events in hourly_buckets.items():
            system_1_count = sum(1 for e in events if e.path == "system_1_reflex")
            hourly_stats[hour] = {
                "total": len(events),
                "system_1_ratio": round(system_1_count / len(events), 4),
                "avg_confidence": round(
                    statistics.mean(e.confidence for e in events), 4
                )
            }
        
        return {
            "status": "ok",
            "period_hours": hours,
            "total_decisions": len(recent_decisions),
            "total_outcomes": len(recent_outcomes),
            "hourly_breakdown": hourly_stats,
            "snapshots_count": len(self.snapshots)
        }

    def reset_analytics(self) -> None:
        """분석 데이터 초기화 (테스트 또는 새 세션 시작용)"""
        self.decision_history.clear()
        self.outcome_history.clear()
        self.snapshots.clear()
        self._path_counter.clear()
        self._reflex_success_counter.clear()
        self._reflex_total_counter.clear()
        self._confidence_buckets = {
            "very_low": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0
        }
        self._total_latency_ms = 0.0
        self._latency_count = 0
        self._last_snapshot_time = None
        print("📊 Intuition Analytics reset.")


def get_intuition_analytics() -> IntuitionAnalytics:
    """IntuitionAnalytics 싱글톤 인스턴스 반환"""
    return IntuitionAnalytics()