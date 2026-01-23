"""
Engine Self-Correction: 자가 교정 및 복구 전략 수립
Step 7: Meta-Cognition - Actionable Correction & Recovery

CognitiveAuditor가 감지한 인지적 오류(무한 루프, 정체, 로드맵 이탈 등)를 
해결하기 위한 구체적인 '교정 행동(Correction Action)'을 정의하고 제안한다.
MetaController는 이 제안을 받아 실제 시스템 상태를 강제로 조정할 수 있다.

Architecture:
    CognitiveAuditor (오류 감지)
        ↓ audit_report
    SelfCorrectionManager (이 모듈)
        ↓ CorrectionPlan
    MetaController (교정 실행)

Usage:
    from engine.self_correction import SelfCorrectionManager, CorrectionType, CorrectionPlan
    
    manager = SelfCorrectionManager()
    plan = manager.propose_correction(audit_report, cognitive_state)
    if plan.type != CorrectionType.NONE:
        # Execute correction action
        pass
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CorrectionType(Enum):
    """교정 행동 유형"""
    NONE = "none"
    RESET_CONTEXT = "reset_context"
    ADJUST_STRATEGY = "adjust_strategy"
    FORCE_EVOLUTION = "force_evolution"
    SKIP_GOAL = "skip_goal"
    DEEP_SLEEP = "deep_sleep"
    EMERGENCY_DUMP = "emergency_dump"


@dataclass
class CorrectionPlan:
    """교정 실행 계획"""
    type: CorrectionType
    reason: str
    priority: int = 1
    params: Dict[str, Any] = field(default_factory=dict)
    suggested_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SelfCorrectionManager:
    """
    자가 교정 관리자
    
    CognitiveAuditor의 감사 결과와 현재 MetaState를 분석하여
    시스템이 스스로를 '고칠 수 있는' 방법을 제안한다.
    
    Attributes:
        correction_history: 과거 교정 기록 (패턴 분석용)
        max_history_size: 기록 보관 최대 개수
    """
    
    MAX_HISTORY_SIZE = 100
    
    def __init__(self):
        self.correction_history: List[CorrectionPlan] = []
    
    def propose_correction(
        self, 
        audit_report: Dict[str, Any], 
        cognitive_state: Dict[str, Any]
    ) -> CorrectionPlan:
        """
        감사 결과와 인지 상태를 기반으로 교정 계획 제안
        
        Args:
            audit_report: CognitiveAuditor의 감사 결과
            cognitive_state: 현재 메타인지 상태
        
        Returns:
            CorrectionPlan: 제안된 교정 계획
        """
        severity = audit_report.get("severity", "info")
        error_type = audit_report.get("error_type", "none")
        
        plan = self._determine_correction(severity, error_type, audit_report, cognitive_state)
        
        self._record_correction(plan)
        
        return plan
    
    def _determine_correction(
        self,
        severity: str,
        error_type: str,
        audit_report: Dict[str, Any],
        cognitive_state: Dict[str, Any]
    ) -> CorrectionPlan:
        """심각도와 오류 유형에 따른 교정 계획 결정"""
        
        if severity == "critical":
            return self._handle_critical_error(error_type, audit_report, cognitive_state)
        
        if severity == "warning":
            return self._handle_warning(error_type, audit_report, cognitive_state)
        
        return CorrectionPlan(
            type=CorrectionType.NONE,
            reason="System is operating within normal parameters.",
            priority=0
        )
    
    def _handle_critical_error(
        self,
        error_type: str,
        report: Dict[str, Any],
        state: Dict[str, Any]
    ) -> CorrectionPlan:
        """심각한 오류에 대한 긴급 교정"""
        
        if error_type == "infinite_loop":
            return CorrectionPlan(
                type=CorrectionType.RESET_CONTEXT,
                reason="Critical infinite loop detected in reasoning chain. Resetting context.",
                priority=10,
                params={
                    "scope": "full_context",
                    "preserve_identity": True,
                    "loop_signature": report.get("loop_signature", "unknown")
                }
            )
        
        if error_type == "roadmap_deviation":
            return CorrectionPlan(
                type=CorrectionType.SKIP_GOAL,
                reason="Critical deviation from roadmap. Current goal might be invalid or unreachable.",
                priority=8,
                params={
                    "target_goal": report.get("current_goal"),
                    "deviation_score": report.get("deviation_score", 0),
                    "suggested_next": report.get("suggested_next_goal")
                }
            )
        
        if error_type == "memory_corruption":
            return CorrectionPlan(
                type=CorrectionType.EMERGENCY_DUMP,
                reason="Memory corruption detected. Emergency state dump required.",
                priority=10,
                params={
                    "dump_location": "/data/emergency_dumps",
                    "include_vectors": True
                }
            )
        
        return CorrectionPlan(
            type=CorrectionType.EMERGENCY_DUMP,
            reason=f"Unhandled critical error: {error_type}. Performing emergency dump.",
            priority=10,
            params={"error_type": error_type, "raw_report": report}
        )
    
    def _handle_warning(
        self,
        error_type: str,
        report: Dict[str, Any],
        state: Dict[str, Any]
    ) -> CorrectionPlan:
        """경고 수준 오류에 대한 교정"""
        
        if error_type == "stagnation":
            consecutive_failures = state.get("recent_failures", 0)
            
            if consecutive_failures >= 5:
                return CorrectionPlan(
                    type=CorrectionType.FORCE_EVOLUTION,
                    reason="Severe stagnation detected. Forcing evolution with alternative approach.",
                    priority=8,
                    params={
                        "bypass_validation": False,
                        "use_alternative_model": True,
                        "stagnation_count": consecutive_failures
                    }
                )
            
            return CorrectionPlan(
                type=CorrectionType.ADJUST_STRATEGY,
                reason="System stagnation detected. Switching to ACCELERATED mode.",
                priority=7,
                params={
                    "target_mode": "accelerated",
                    "increase_temperature": True,
                    "stagnation_count": consecutive_failures
                }
            )
        
        if error_type == "low_confidence":
            confidence = state.get("confidence_score", 0.5)
            return CorrectionPlan(
                type=CorrectionType.DEEP_SLEEP,
                reason=f"Low confidence ({confidence:.2f}). Entering deep sleep for consolidation.",
                priority=5,
                params={
                    "sleep_duration_seconds": 300,
                    "consolidate_memories": True,
                    "confidence_threshold": 0.6
                }
            )
        
        if error_type == "repetitive_pattern":
            return CorrectionPlan(
                type=CorrectionType.RESET_CONTEXT,
                reason="Repetitive action pattern detected. Resetting short-term memory.",
                priority=6,
                params={
                    "scope": "short_term_memory",
                    "preserve_identity": True,
                    "pattern_signature": report.get("pattern_signature")
                }
            )
        
        return CorrectionPlan(
            type=CorrectionType.ADJUST_STRATEGY,
            reason=f"Warning level issue: {error_type}. Adjusting strategy.",
            priority=4,
            params={"target_mode": "cautious", "error_type": error_type}
        )
    
    def _record_correction(self, plan: CorrectionPlan) -> None:
        """교정 기록 저장 (패턴 분석용)"""
        if plan.type == CorrectionType.NONE:
            return
        
        self.correction_history.append(plan)
        
        if len(self.correction_history) > self.MAX_HISTORY_SIZE:
            self.correction_history = self.correction_history[-self.MAX_HISTORY_SIZE:]
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """교정 통계 반환"""
        if not self.correction_history:
            return {
                "total_corrections": 0,
                "by_type": {},
                "avg_priority": 0.0
            }
        
        type_counts: Dict[str, int] = {}
        total_priority = 0
        
        for plan in self.correction_history:
            type_name = plan.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            total_priority += plan.priority
        
        return {
            "total_corrections": len(self.correction_history),
            "by_type": type_counts,
            "avg_priority": total_priority / len(self.correction_history),
            "most_common": max(type_counts, key=type_counts.get) if type_counts else None
        }
    
    def should_escalate(self) -> bool:
        """
        최근 교정 패턴을 분석하여 인간 개입이 필요한지 판단
        
        Returns:
            True if human intervention is recommended
        """
        if len(self.correction_history) < 5:
            return False
        
        recent = self.correction_history[-10:]
        
        critical_count = sum(1 for p in recent if p.priority >= 8)
        if critical_count >= 3:
            return True
        
        emergency_count = sum(1 for p in recent if p.type == CorrectionType.EMERGENCY_DUMP)
        if emergency_count >= 2:
            return True
        
        return False


_manager_instance: Optional[SelfCorrectionManager] = None


def get_self_correction_manager() -> SelfCorrectionManager:
    """SelfCorrectionManager 싱글톤 인스턴스 반환"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SelfCorrectionManager()
    return _manager_instance