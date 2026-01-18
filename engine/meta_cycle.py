"""
Engine Meta Cycle: 메타인지 순환 로직
Step 7: Meta-Cognition - MetaEvaluator와 StrategyAdapter를 연결하는 오케스트레이터

이 모듈은 메타인지의 핵심 순환(Cycle) 과정을 캡슐화한다:
1. MetaEvaluator로 현재 상태를 평가
2. 평가 결과를 StrategyAdapter에 전달하여 최적 전략 도출
3. 결과 리포트 반환

대형 파일인 meta_cognition.py를 수정하지 않고, 이 모듈을 호출하여
메타인지 기능을 확장할 수 있다.

Architecture:
    MetaCognitionMixin (engine/meta_cognition.py)
        ↓ 호출
    MetaCycle (이 모듈)
        ↓ 조율
    MetaEvaluator (평가) + StrategyAdapter (전략)
        ↓
    CycleReport 반환

Usage:
    from engine.meta_cycle import MetaCycle, CycleReport
    
    cycle = MetaCycle()
    report = cycle.process_cycle(context)
    print(report.recommended_mode)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


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


@dataclass
class CycleReport:
    """
    메타인지 순환 결과 리포트
    
    Attributes:
        timestamp: 순환 실행 시각
        efficacy_score: 효율성 점수 (0.0 ~ 1.0)
        confidence_score: 자신감 점수 (0.0 ~ 1.0)
        current_mode: 현재 전략 모드
        recommended_mode: 권장 전략 모드
        mode_changed: 모드 변경 여부
        tuning_params: 권장 튜닝 파라미터
        reasoning: 판단 근거
        suggestions: 개선 제안 목록
    """
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    efficacy_score: float = 0.5
    confidence_score: float = 0.5
    current_mode: str = "normal"
    recommended_mode: str = "normal"
    mode_changed: bool = False
    tuning_params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    suggestions: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp,
            "efficacy_score": self.efficacy_score,
            "confidence_score": self.confidence_score,
            "current_mode": self.current_mode,
            "recommended_mode": self.recommended_mode,
            "mode_changed": self.mode_changed,
            "tuning_params": self.tuning_params,
            "reasoning": self.reasoning,
            "suggestions": self.suggestions,
            "error": self.error,
        }


class MetaCycle:
    """
    메타인지 순환 오케스트레이터
    
    MetaEvaluator와 StrategyAdapter를 연결하여 완전한 메타인지 순환을 수행한다.
    Lazy initialization으로 필요할 때만 컴포넌트를 생성한다.
    
    Attributes:
        evaluator: MetaEvaluator 인스턴스
        adapter: StrategyAdapter 인스턴스
        current_mode: 현재 전략 모드
        cycle_history: 최근 순환 기록 (최대 10개)
    """
    
    MAX_HISTORY = 10
    
    def __init__(self):
        self._evaluator: Optional[MetaEvaluator] = None
        self._adapter: Optional[StrategyAdapter] = None
        self._current_mode: Optional[StrategyMode] = None
        self._cycle_history: List[CycleReport] = []
        self._initialized = False
        
    def _lazy_init(self) -> bool:
        """Lazy initialization - 필요할 때 컴포넌트 생성"""
        if self._initialized:
            return True
            
        if not HAS_EVALUATOR or not HAS_ADAPTER:
            print("⚠️ MetaCycle: 필수 컴포넌트 누락 (MetaEvaluator 또는 StrategyAdapter)")
            return False
        
        try:
            self._evaluator = MetaEvaluator()
            self._adapter = StrategyAdapter()
            self._current_mode = StrategyMode.NORMAL
            self._initialized = True
            print("🧠 MetaCycle 초기화 완료")
            return True
        except Exception as e:
            print(f"❌ MetaCycle 초기화 실패: {e}")
            return False
    
    @property
    def is_available(self) -> bool:
        """메타인지 순환 사용 가능 여부"""
        return HAS_EVALUATOR and HAS_ADAPTER
    
    @property
    def current_mode(self) -> str:
        """현재 전략 모드 (문자열)"""
        if self._current_mode is None:
            return "unknown"
        return self._current_mode.value if hasattr(self._current_mode, 'value') else str(self._current_mode)
    
    def process_cycle(
        self,
        recent_history: List[Dict[str, Any]] = None,
        relevant_memories: List[Dict[str, Any]] = None,
        error_count: int = 0,
        complexity: str = "medium"
    ) -> CycleReport:
        """
        메타인지 순환 실행
        
        1. MetaEvaluator로 현재 상태 평가
        2. 평가 결과를 기반으로 StrategyAdapter에서 최적 모드 결정
        3. 결과 리포트 생성 및 반환
        
        Args:
            recent_history: 최근 진화/활동 기록
            relevant_memories: 관련 벡터 메모리
            error_count: 최근 에러 횟수
            complexity: 현재 작업 복잡도 ("low", "medium", "high")
        
        Returns:
            CycleReport: 순환 결과 리포트
        """
        report = CycleReport()
        
        if not self._lazy_init():
            report.error = "MetaCycle 초기화 실패"
            report.reasoning = "필수 컴포넌트(MetaEvaluator, StrategyAdapter) 누락"
            return report
        
        try:
            recent_history = recent_history or []
            relevant_memories = relevant_memories or []
            
            evaluation = self._evaluator.evaluate_efficacy(
                recent_history=recent_history,
                relevant_memories=relevant_memories
            )
            
            report.efficacy_score = evaluation.get("efficacy_score", 0.5)
            report.confidence_score = evaluation.get("confidence_score", 0.5)
            report.reasoning = evaluation.get("reasoning", "")
            
            new_mode = self._adapter.evaluate_mode(
                efficacy_score=report.efficacy_score,
                error_count=error_count,
                complexity=complexity
            )
            
            old_mode_str = self.current_mode
            report.current_mode = old_mode_str
            report.recommended_mode = new_mode.value if hasattr(new_mode, 'value') else str(new_mode)
            
            if new_mode != self._current_mode:
                report.mode_changed = True
                self._current_mode = new_mode
                print(f"🔄 MetaCycle: 전략 변경 {old_mode_str} → {report.recommended_mode}")
            
            report.tuning_params = self._adapter.get_tuning_params(new_mode)
            
            report.suggestions = self._generate_suggestions(report)
            
            self._record_cycle(report)
            
            return report
            
        except Exception as e:
            report.error = str(e)
            report.reasoning = f"순환 처리 중 예외 발생: {e}"
            print(f"❌ MetaCycle 순환 실패: {e}")
            return report
    
    def _generate_suggestions(self, report: CycleReport) -> List[str]:
        """평가 결과를 기반으로 개선 제안 생성"""
        suggestions = []
        
        if report.efficacy_score < 0.3:
            suggestions.append("효율성이 매우 낮습니다. 접근 방식을 재검토하세요.")
        elif report.efficacy_score < 0.5:
            suggestions.append("효율성이 다소 낮습니다. 작은 단위로 진화를 시도하세요.")
        
        if report.confidence_score < 0.3:
            suggestions.append("자신감이 낮습니다. 관련 기억을 더 참조하세요.")
        
        if report.mode_changed:
            if report.recommended_mode == "conservative":
                suggestions.append("보수적 모드로 전환됨: 검증 강화, 작은 변경 권장")
            elif report.recommended_mode == "accelerated":
                suggestions.append("가속 모드로 전환됨: 빠른 진화 가능, 단 품질 유지 필요")
        
        if not suggestions:
            suggestions.append("현재 상태 양호. 현 전략 유지 권장.")
        
        return suggestions
    
    def _record_cycle(self, report: CycleReport):
        """순환 기록 저장 (최대 MAX_HISTORY개)"""
        self._cycle_history.append(report)
        if len(self._cycle_history) > self.MAX_HISTORY:
            self._cycle_history.pop(0)
    
    def get_cycle_history(self) -> List[Dict[str, Any]]:
        """최근 순환 기록 반환"""
        return [r.to_dict() for r in self._cycle_history]
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """순환 기록 기반 트렌드 분석"""
        if len(self._cycle_history) < 2:
            return {
                "status": "insufficient_data",
                "message": "트렌드 분석에 최소 2회 이상의 순환 기록 필요"
            }
        
        efficacy_scores = [r.efficacy_score for r in self._cycle_history]
        confidence_scores = [r.confidence_score for r in self._cycle_history]
        mode_changes = sum(1 for r in self._cycle_history if r.mode_changed)
        
        avg_efficacy = sum(efficacy_scores) / len(efficacy_scores)
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        efficacy_trend = "stable"
        if len(efficacy_scores) >= 3:
            recent_avg = sum(efficacy_scores[-3:]) / 3
            older_avg = sum(efficacy_scores[:-3]) / max(len(efficacy_scores) - 3, 1) if len(efficacy_scores) > 3 else recent_avg
            if recent_avg > older_avg + 0.1:
                efficacy_trend = "improving"
            elif recent_avg < older_avg - 0.1:
                efficacy_trend = "declining"
        
        return {
            "status": "analyzed",
            "cycle_count": len(self._cycle_history),
            "avg_efficacy": round(avg_efficacy, 3),
            "avg_confidence": round(avg_confidence, 3),
            "efficacy_trend": efficacy_trend,
            "mode_change_frequency": mode_changes / len(self._cycle_history),
            "current_mode": self.current_mode
        }


_meta_cycle_instance: Optional[MetaCycle] = None


def get_meta_cycle() -> MetaCycle:
    """MetaCycle 싱글톤 인스턴스 반환"""
    global _meta_cycle_instance
    if _meta_cycle_instance is None:
        _meta_cycle_instance = MetaCycle()
    return _meta_cycle_instance