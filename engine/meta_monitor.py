"""
Engine Meta Monitor: 인지 상태 통합 진단 모듈
Step 7: Meta-Cognition - 사고 과정 모니터링

이 모듈은 분산된 메타 인지 데이터(전략 모드, 자신감 점수, 학습 지표)를
실시간 '인지 상태(Cognitive State)'로 통합하고 진단하는 역할을 수행한다.

대형 파일인 meta_cognition.py를 직접 수정하지 않고,
이 모듈을 통해 인지 상태 모니터링 기능을 추가한다.

Architecture:
    MetaCognitionMixin (engine/meta_cognition.py)
        ↓ 호출
    MetaMonitor (이 모듈)
        ↓ 데이터 수집
    MetaEvaluator + StrategyAdapter + RuntimeTuner
        ↓
    CognitiveState (통합 상태 객체)

Features:

Usage:
    from engine.meta_monitor import MetaMonitor, CognitiveState
    
    monitor = MetaMonitor()
    state = monitor.capture_state(context)
    diagnosis = monitor.diagnose(state)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import statistics


class CognitiveHealthLevel(Enum):
    """인지 건강 수준 열거형"""
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """경고 심각도 열거형"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CognitiveAlert:
    """
    인지 이상 경고 데이터 클래스
    
    Attributes:
        severity: 경고 심각도
        category: 경고 카테고리 (confidence, strategy, learning, memory 등)
        message: 경고 메시지
        timestamp: 발생 시각
        suggested_action: 권장 조치
    """
    severity: AlertSeverity
    category: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    suggested_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "suggested_action": self.suggested_action
        }


@dataclass
class CognitiveState:
    """
    인지 상태 스냅샷 데이터 클래스
    
    여러 메타인지 컴포넌트에서 수집된 데이터를 통합하여
    현재 시스템의 '인지 상태'를 표현한다.
    
    Attributes:
        timestamp: 스냅샷 생성 시각
        strategy_mode: 현재 전략 모드 (normal, accelerated, conservative 등)
        confidence_score: 자신감 점수 (0.0 ~ 1.0)
        efficacy_score: 효율성 점수 (0.0 ~ 1.0)
        learning_rate: 학습률 (최근 성공률 기반)
        memory_clarity: 기억 명확도 (벡터 메모리 관련성)
        error_rate: 최근 에러율
        complexity_level: 현재 작업 복잡도
        health_level: 종합 인지 건강 수준
        alerts: 발생한 경고 목록
        metadata: 추가 메타데이터
    """
    timestamp: datetime = field(default_factory=datetime.now)
    strategy_mode: str = "normal"
    confidence_score: float = 0.5
    efficacy_score: float = 0.5
    learning_rate: float = 0.5
    memory_clarity: float = 0.5
    error_rate: float = 0.0
    complexity_level: str = "medium"
    health_level: CognitiveHealthLevel = CognitiveHealthLevel.MODERATE
    alerts: List[CognitiveAlert] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "strategy_mode": self.strategy_mode,
            "confidence_score": self.confidence_score,
            "efficacy_score": self.efficacy_score,
            "learning_rate": self.learning_rate,
            "memory_clarity": self.memory_clarity,
            "error_rate": self.error_rate,
            "complexity_level": self.complexity_level,
            "health_level": self.health_level.value,
            "alerts": [a.to_dict() for a in self.alerts],
            "metadata": self.metadata
        }
    
    def get_overall_score(self) -> float:
        """종합 인지 점수 계산 (0.0 ~ 1.0)"""
        weights = {
            "confidence": 0.25,
            "efficacy": 0.25,
            "learning": 0.20,
            "memory": 0.15,
            "error_penalty": 0.15
        }
        
        score = (
            self.confidence_score * weights["confidence"] +
            self.efficacy_score * weights["efficacy"] +
            self.learning_rate * weights["learning"] +
            self.memory_clarity * weights["memory"] +
            (1.0 - self.error_rate) * weights["error_penalty"]
        )
        
        return max(0.0, min(1.0, score))


class MetaMonitor:
    """
    메타 인지 모니터
    
    분산된 메타인지 컴포넌트들로부터 데이터를 수집하고,
    통합된 인지 상태(CognitiveState)를 생성하며,
    이상 징후를 탐지하여 경고를 발생시킨다.
    
    Attributes:
        state_history: 과거 인지 상태 이력 (트렌드 분석용)
        max_history_size: 보관할 최대 이력 수
        alert_thresholds: 경고 발생 임계값
    """
    
    MAX_HISTORY_SIZE = 100
    
    ALERT_THRESHOLDS = {
        "confidence_low": 0.3,
        "confidence_critical": 0.15,
        "efficacy_low": 0.4,
        "efficacy_critical": 0.2,
        "error_rate_high": 0.3,
        "error_rate_critical": 0.5,
        "learning_stagnant": 0.2
    }
    
    HEALTH_THRESHOLDS = {
        CognitiveHealthLevel.OPTIMAL: 0.85,
        CognitiveHealthLevel.GOOD: 0.70,
        CognitiveHealthLevel.MODERATE: 0.50,
        CognitiveHealthLevel.DEGRADED: 0.30
    }
    
    def __init__(self):
        self._state_history: List[CognitiveState] = []
        self._last_capture_time: Optional[datetime] = None
        self._evaluator = None
        self._strategy_adapter = None
        self._init_components()
    
    def _init_components(self):
        """메타인지 컴포넌트 초기화"""
        try:
            from engine.meta_evaluator import MetaEvaluator
            self._evaluator = MetaEvaluator()
        except ImportError:
            self._evaluator = None
        
        try:
            from engine.strategy_adapter import StrategyAdapter
            self._strategy_adapter = StrategyAdapter()
        except ImportError:
            self._strategy_adapter = None
    
    def capture_state(self, context: Dict[str, Any] = None) -> CognitiveState:
        """
        현재 인지 상태를 캡처하여 스냅샷 생성
        
        Args:
            context: 외부에서 전달된 컨텍스트 정보
        
        Returns:
            CognitiveState 스냅샷
        """
        context = context or {}
        
        confidence = self._extract_confidence(context)
        efficacy = self._extract_efficacy(context)
        learning_rate = self._calculate_learning_rate(context)
        memory_clarity = self._assess_memory_clarity(context)
        error_rate = self._calculate_error_rate(context)
        complexity = self._assess_complexity(context)
        strategy_mode = self._get_current_strategy(context)
        
        state = CognitiveState(
            timestamp=datetime.now(),
            strategy_mode=strategy_mode,
            confidence_score=confidence,
            efficacy_score=efficacy,
            learning_rate=learning_rate,
            memory_clarity=memory_clarity,
            error_rate=error_rate,
            complexity_level=complexity,
            metadata={
                "context_keys": list(context.keys()),
                "history_size": len(self._state_history)
            }
        )
        
        alerts = self._detect_alerts(state)
        state.alerts = alerts
        
        health_level = self._determine_health_level(state)
        state.health_level = health_level
        
        self._add_to_history(state)
        self._last_capture_time = datetime.now()
        
        return state
    
    def _extract_confidence(self, context: Dict[str, Any]) -> float:
        """컨텍스트에서 자신감 점수 추출"""
        if "confidence_score" in context:
            return float(context["confidence_score"])
        
        if self._evaluator and "recent_history" in context:
            try:
                result = self._evaluator.evaluate_efficacy(
                    recent_history=context.get("recent_history", []),
                    relevant_memories=context.get("relevant_memories", [])
                )
                return result.get("confidence_score", 0.5)
            except Exception:
                pass
        
        return 0.5
    
    def _extract_efficacy(self, context: Dict[str, Any]) -> float:
        """컨텍스트에서 효율성 점수 추출"""
        if "efficacy_score" in context:
            return float(context["efficacy_score"])
        
        recent_history = context.get("recent_history", [])
        if not recent_history:
            return 0.5
        
        success_count = sum(1 for h in recent_history if h.get("status") == "success")
        total_count = len(recent_history)
        
        if total_count == 0:
            return 0.5
        
        return success_count / total_count
    
    def _calculate_learning_rate(self, context: Dict[str, Any]) -> float:
        """학습률 계산 (최근 성공률 변화 추세)"""
        if len(self._state_history) < 3:
            return 0.5
        
        recent_efficacies = [s.efficacy_score for s in self._state_history[-5:]]
        
        if len(recent_efficacies) < 2:
            return 0.5
        
        trend = recent_efficacies[-1] - recent_efficacies[0]
        
        learning_rate = 0.5 + (trend * 2.5)
        return max(0.0, min(1.0, learning_rate))
    
    def _assess_memory_clarity(self, context: Dict[str, Any]) -> float:
        """기억 명확도 평가"""
        relevant_memories = context.get("relevant_memories", [])
        
        if not relevant_memories:
            return 0.3
        
        distances = [m.get("distance", 1.0) for m in relevant_memories]
        
        if not distances:
            return 0.3
        
        avg_distance = sum(distances) / len(distances)
        clarity = 1.0 - min(avg_distance, 1.0)
        
        return clarity
    
    def _calculate_error_rate(self, context: Dict[str, Any]) -> float:
        """최근 에러율 계산"""
        recent_history = context.get("recent_history", [])
        
        if not recent_history:
            return 0.0
        
        error_count = sum(1 for h in recent_history if h.get("status") == "failed")
        total_count = len(recent_history)
        
        if total_count == 0:
            return 0.0
        
        return error_count / total_count
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """현재 작업 복잡도 평가"""
        if "complexity" in context:
            return context["complexity"]
        
        current_goal = context.get("current_goal", {})
        goal_content = current_goal.get("content", "") if isinstance(current_goal, dict) else ""
        
        complexity_keywords = {
            "high": ["architecture", "refactor", "integration", "migration", "core"],
            "medium": ["implement", "add", "create", "update", "fix"],
            "low": ["test", "document", "comment", "rename", "cleanup"]
        }
        
        goal_lower = goal_content.lower()
        
        for level, keywords in complexity_keywords.items():
            if any(kw in goal_lower for kw in keywords):
                return level
        
        return "medium"
    
    def _get_current_strategy(self, context: Dict[str, Any]) -> str:
        """현재 전략 모드 조회"""
        if "strategy_mode" in context:
            return context["strategy_mode"]
        
        if self._strategy_adapter:
            try:
                efficacy = context.get("efficacy_score", 0.5)
                error_count = int(context.get("error_count", 0))
                complexity = context.get("complexity", "medium")
                
                mode = self._strategy_adapter.evaluate_mode(
                    efficacy_score=efficacy,
                    error_count=error_count,
                    complexity=complexity
                )
                return mode.value
            except Exception:
                pass
        
        return "normal"
    
    def _detect_alerts(self, state: CognitiveState) -> List[CognitiveAlert]:
        """인지 상태에서 이상 징후 탐지"""
        alerts = []
        
        if state.confidence_score < self.ALERT_THRESHOLDS["confidence_critical"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.CRITICAL,
                category="confidence",
                message=f"자신감 점수 위험 수준: {state.confidence_score:.2f}",
                suggested_action="보수적 전략으로 전환하고 검증 강화 권장"
            ))
        elif state.confidence_score < self.ALERT_THRESHOLDS["confidence_low"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.WARNING,
                category="confidence",
                message=f"자신감 점수 저하: {state.confidence_score:.2f}",
                suggested_action="최근 성공 사례 참조 및 단순 작업부터 시작 권장"
            ))
        
        if state.efficacy_score < self.ALERT_THRESHOLDS["efficacy_critical"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.CRITICAL,
                category="efficacy",
                message=f"효율성 점수 위험 수준: {state.efficacy_score:.2f}",
                suggested_action="진화 일시 중단 및 시스템 점검 권장"
            ))
        elif state.efficacy_score < self.ALERT_THRESHOLDS["efficacy_low"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.WARNING,
                category="efficacy",
                message=f"효율성 점수 저하: {state.efficacy_score:.2f}",
                suggested_action="접근 방식 재검토 권장"
            ))
        
        if state.error_rate > self.ALERT_THRESHOLDS["error_rate_critical"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.CRITICAL,
                category="error",
                message=f"에러율 위험 수준: {state.error_rate:.2%}",
                suggested_action="즉시 에러 패턴 분석 및 수정 필요"
            ))
        elif state.error_rate > self.ALERT_THRESHOLDS["error_rate_high"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.WARNING,
                category="error",
                message=f"에러율 상승: {state.error_rate:.2%}",
                suggested_action="에러 로그 검토 권장"
            ))
        
        if state.learning_rate < self.ALERT_THRESHOLDS["learning_stagnant"]:
            alerts.append(CognitiveAlert(
                severity=AlertSeverity.INFO,
                category="learning",
                message=f"학습 정체 감지: {state.learning_rate:.2f}",
                suggested_action="새로운 접근 방식 또는 외부 입력 필요"
            ))
        
        return alerts
    
    def _determine_health_level(self, state: CognitiveState) -> CognitiveHealthLevel:
        """종합 인지 건강 수준 결정"""
        overall_score = state.get_overall_score()
        
        for level, threshold in self.HEALTH_THRESHOLDS.items():
            if overall_score >= threshold:
                return level
        
        return CognitiveHealthLevel.CRITICAL
    
    def _add_to_history(self, state: CognitiveState):
        """상태 이력에 추가"""
        self._state_history.append(state)
        
        if len(self._state_history) > self.MAX_HISTORY_SIZE:
            self._state_history = self._state_history[-self.MAX_HISTORY_SIZE:]
    
    def diagnose(self, state: CognitiveState = None) -> Dict[str, Any]:
        """
        인지 상태 종합 진단
        
        Args:
            state: 진단할 인지 상태 (None이면 최신 상태 사용)
        
        Returns:
            진단 결과 딕셔너리
        """
        if state is None:
            if not self._state_history:
                return {"error": "진단할 상태 없음", "recommendation": "capture_state() 먼저 호출"}
            state = self._state_history[-1]
        
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": state.get_overall_score(),
            "health_level": state.health_level.value,
            "strategy_mode": state.strategy_mode,
            "metrics": {
                "confidence": state.confidence_score,
                "efficacy": state.efficacy_score,
                "learning_rate": state.learning_rate,
                "memory_clarity": state.memory_clarity,
                "error_rate": state.error_rate
            },
            "alerts_count": len(state.alerts),
            "alerts": [a.to_dict() for a in state.alerts],
            "trend": self._analyze_trend(),
            "recommendation": self._generate_recommendation(state)
        }
        
        return diagnosis
    
    def _analyze_trend(self) -> Dict[str, str]:
        """최근 트렌드 분석"""
        if len(self._state_history) < 3:
            return {"status": "insufficient_data", "direction": "unknown"}
        
        recent_scores = [s.get_overall_score() for s in self._state_history[-5:]]
        
        if len(recent_scores) < 2:
            return {"status": "insufficient_data", "direction": "unknown"}
        
        first_half_avg = statistics.mean(recent_scores[:len(recent_scores)//2])
        second_half_avg = statistics.mean(recent_scores[len(recent_scores)//2:])
        
        diff = second_half_avg - first_half_avg
        
        if diff > 0.1:
            direction = "improving"
        elif diff < -0.1:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "status": "analyzed",
            "direction": direction,
            "change": f"{diff:+.2f}"
        }
    
    def _generate_recommendation(self, state: CognitiveState) -> str:
        """상태 기반 권장 사항 생성"""
        if state.health_level == CognitiveHealthLevel.CRITICAL:
            return "시스템 즉시 점검 필요. 진화 일시 중단 권장."
        
        if state.health_level == CognitiveHealthLevel.DEGRADED:
            return "보수적 전략 전환 및 단순 작업 우선 권장."
        
        if state.error_rate > 0.3:
            return "에러 패턴 분석 후 수정 작업 우선 권장."
        
        if state.confidence_score < 0.4:
            return "최근 성공 사례 참조하여 자신감 회복 권장."
        
        if state.learning_rate < 0.3:
            return "새로운 접근 방식 탐색 또는 외부 피드백 수용 권장."
        
        if state.health_level == CognitiveHealthLevel.OPTIMAL:
            return "최적 상태. 도전적인 목표 시도 가능."
        
        return "현재 상태 유지. 꾸준한 진화 지속."
    
    def get_history_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """상태 이력 요약 반환"""
        recent = self._state_history[-limit:] if self._state_history else []
        
        return [
            {
                "timestamp": s.timestamp.isoformat(),
                "overall_score": s.get_overall_score(),
                "health_level": s.health_level.value,
                "alerts_count": len(s.alerts)
            }
            for s in recent
        ]


_monitor_instance: Optional[MetaMonitor] = None


def get_meta_monitor() -> MetaMonitor:
    """MetaMonitor 싱글톤 인스턴스 반환"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MetaMonitor()
    return _monitor_instance