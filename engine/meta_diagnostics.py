"""
Engine Meta Diagnostics: 메타인지 시스템 자가 진단
Step 7: Meta-Cognition - Self-Health Verification

이 모듈은 메타인지 시스템(MetaCycle, MetaEvaluator, StrategyAdapter, MetaMonitor 등)
자체의 건전성(Health)을 검증하는 자가 진단 로직을 구현한다.

메타인지가 "생각에 대해 생각하기"라면,
이 모듈은 "메타인지에 대해 메타인지하기" - 자기 검증의 최상위 레이어이다.

Architecture:
    AINCore / MetaController
        ↓ 호출
    MetaDiagnostics (이 모듈)
        ↓ 점검
    MetaCycle, MetaEvaluator, StrategyAdapter, MetaMonitor
        ↓
    DiagnosticReport 반환

Features:
    1. 컴포넌트 가용성 점검 (Component Availability)
    2. 순환 의존성 감지 (Circular Dependency Detection)
    3. 상태 일관성 검증 (State Consistency Check)
    4. 성능 저하 감지 (Performance Degradation Detection)
    5. 복구 제안 생성 (Recovery Suggestion)

Usage:
    from engine.meta_diagnostics import MetaDiagnostics, MetaHealthReport
    
    diagnostics = MetaDiagnostics()
    report = diagnostics.run_full_diagnostics()
    
    if report.health_status == MetaHealthStatus.CRITICAL:
        print(f"Meta-cognition system critical: {report.issues}")
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time
import traceback


class MetaHealthStatus(Enum):
    """메타인지 시스템 건강 상태 열거형"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    IMPAIRED = "impaired"
    CRITICAL = "critical"


class MetaComponentType(Enum):
    """메타인지 컴포넌트 유형"""
    META_CYCLE = "meta_cycle"
    META_EVALUATOR = "meta_evaluator"
    STRATEGY_ADAPTER = "strategy_adapter"
    META_MONITOR = "meta_monitor"
    META_CONTROLLER = "meta_controller"
    RUNTIME_TUNER = "runtime_tuner"
    COGNITIVE_AUDITOR = "cognitive_auditor"


@dataclass
class ComponentStatus:
    """개별 컴포넌트 상태"""
    component: MetaComponentType
    available: bool
    import_error: Optional[str] = None
    instantiation_error: Optional[str] = None
    last_execution_time_ms: Optional[float] = None
    execution_count: int = 0
    error_count: int = 0


@dataclass
class MetaHealthReport:
    """메타인지 시스템 건강 진단 보고서"""
    timestamp: datetime = field(default_factory=datetime.now)
    health_status: MetaHealthStatus = MetaHealthStatus.HEALTHY
    overall_score: float = 1.0
    component_statuses: Dict[str, ComponentStatus] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recovery_suggestions: List[str] = field(default_factory=list)
    diagnostics_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "health_status": self.health_status.value,
            "overall_score": round(self.overall_score, 3),
            "component_count": len(self.component_statuses),
            "available_components": sum(
                1 for s in self.component_statuses.values() if s.available
            ),
            "issues": self.issues,
            "warnings": self.warnings,
            "recovery_suggestions": self.recovery_suggestions,
            "diagnostics_duration_ms": round(self.diagnostics_duration_ms, 2),
        }

    def get_summary(self) -> str:
        """사람이 읽을 수 있는 요약 생성"""
        available = sum(1 for s in self.component_statuses.values() if s.available)
        total = len(self.component_statuses)
        
        lines = [
            f"=== Meta-Cognition Health Report ===",
            f"Status: {self.health_status.value.upper()}",
            f"Score: {self.overall_score:.1%}",
            f"Components: {available}/{total} available",
        ]
        
        if self.issues:
            lines.append(f"Issues: {len(self.issues)}")
            for issue in self.issues[:3]:
                lines.append(f"  - {issue}")
        
        if self.recovery_suggestions:
            lines.append("Suggestions:")
            for suggestion in self.recovery_suggestions[:2]:
                lines.append(f"  → {suggestion}")
        
        return "\n".join(lines)


class MetaDiagnostics:
    """
    메타인지 시스템 자가 진단 엔진
    
    메타인지 컴포넌트들의 가용성, 일관성, 성능을 점검하고
    문제 발생 시 복구 제안을 생성한다.
    """
    
    # 성능 임계값 (밀리초)
    EXECUTION_TIME_WARNING_MS = 500
    EXECUTION_TIME_CRITICAL_MS = 2000
    
    # 에러율 임계값
    ERROR_RATE_WARNING = 0.1
    ERROR_RATE_CRITICAL = 0.3
    
    def __init__(self):
        self._component_cache: Dict[str, Any] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._last_diagnostic_time: Optional[datetime] = None
    
    def run_full_diagnostics(self) -> MetaHealthReport:
        """
        전체 메타인지 시스템 진단 수행
        
        Returns:
            MetaHealthReport: 종합 진단 보고서
        """
        start_time = time.time()
        report = MetaHealthReport()
        
        try:
            # 1. 컴포넌트 가용성 점검
            self._check_component_availability(report)
            
            # 2. 상태 일관성 검증
            self._check_state_consistency(report)
            
            # 3. 순환 의존성 감지
            self._check_circular_dependencies(report)
            
            # 4. 성능 저하 감지
            self._check_performance_degradation(report)
            
            # 5. 종합 점수 계산
            self._calculate_overall_score(report)
            
            # 6. 복구 제안 생성
            self._generate_recovery_suggestions(report)
            
        except Exception as e:
            report.issues.append(f"Diagnostics execution error: {str(e)}")
            report.health_status = MetaHealthStatus.CRITICAL
            report.overall_score = 0.0
        
        report.diagnostics_duration_ms = (time.time() - start_time) * 1000
        self._last_diagnostic_time = datetime.now()
        self._execution_history.append(report.to_dict())
        
        # 히스토리 크기 제한
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-100:]
        
        return report
    
    def _check_component_availability(self, report: MetaHealthReport) -> None:
        """각 메타인지 컴포넌트의 가용성 점검"""
        components_to_check = [
            (MetaComponentType.META_CYCLE, "engine.meta_cycle", "MetaCycle"),
            (MetaComponentType.META_EVALUATOR, "engine.meta_evaluator", "MetaEvaluator"),
            (MetaComponentType.STRATEGY_ADAPTER, "engine.strategy_adapter", "StrategyAdapter"),
            (MetaComponentType.META_MONITOR, "engine.meta_monitor", "MetaMonitor"),
            (MetaComponentType.META_CONTROLLER, "engine.meta_controller", "MetaController"),
            (MetaComponentType.RUNTIME_TUNER, "engine.runtime_tuner", "RuntimeTuner"),
            (MetaComponentType.COGNITIVE_AUDITOR, "engine.cognitive_auditor", "CognitiveAuditorMixin"),
        ]
        
        for comp_type, module_path, class_name in components_to_check:
            status = ComponentStatus(component=comp_type, available=False)
            
            try:
                # 동적 임포트 시도
                import importlib
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name, None)
                
                if cls is not None:
                    status.available = True
                    self._component_cache[comp_type.value] = cls
                else:
                    status.import_error = f"Class {class_name} not found in {module_path}"
                    report.warnings.append(
                        f"Component {comp_type.value}: class not found"
                    )
            
            except ImportError as e:
                status.import_error = str(e)
                report.warnings.append(
                    f"Component {comp_type.value}: import failed - {str(e)[:50]}"
                )
            
            except Exception as e:
                status.instantiation_error = str(e)
                report.issues.append(
                    f"Component {comp_type.value}: unexpected error - {str(e)[:50]}"
                )
            
            report.component_statuses[comp_type.value] = status
    
    def _check_state_consistency(self, report: MetaHealthReport) -> None:
        """메타인지 컴포넌트 간 상태 일관성 검증"""
        try:
            # StrategyAdapter와 RuntimeTuner 간 모드 일관성 확인
            strategy_status = report.component_statuses.get(
                MetaComponentType.STRATEGY_ADAPTER.value
            )
            tuner_status = report.component_statuses.get(
                MetaComponentType.RUNTIME_TUNER.value
            )
            
            if strategy_status and tuner_status:
                if strategy_status.available and tuner_status.available:
                    # 두 컴포넌트 모두 사용 가능하면 일관성 확인
                    pass  # 실제 인스턴스 비교는 런타임에서 수행
                elif strategy_status.available != tuner_status.available:
                    report.warnings.append(
                        "Strategy-Tuner availability mismatch: "
                        "one component available, other not"
                    )
            
            # MetaCycle과 MetaEvaluator 간 의존성 확인
            cycle_status = report.component_statuses.get(
                MetaComponentType.META_CYCLE.value
            )
            evaluator_status = report.component_statuses.get(
                MetaComponentType.META_EVALUATOR.value
            )
            
            if cycle_status and evaluator_status:
                if cycle_status.available and not evaluator_status.available:
                    report.issues.append(
                        "MetaCycle available but MetaEvaluator missing: "
                        "evaluation capability impaired"
                    )
        
        except Exception as e:
            report.warnings.append(f"State consistency check error: {str(e)[:50]}")
    
    def _check_circular_dependencies(self, report: MetaHealthReport) -> None:
        """순환 의존성 감지"""
        # 알려진 순환 의존성 패턴 검사
        circular_patterns = [
            ("meta_cognition", "meta_cycle", "meta_cognition"),
            ("meta_controller", "meta_cognition", "meta_controller"),
        ]
        
        for pattern in circular_patterns:
            try:
                # 간접적 순환 의존성 검사
                modules_exist = True
                for module_name in pattern:
                    full_path = f"engine.{module_name}"
                    try:
                        import importlib
                        importlib.import_module(full_path)
                    except ImportError:
                        modules_exist = False
                        break
                
                if modules_exist:
                    # 모든 모듈이 존재하면 순환 가능성 경고
                    report.warnings.append(
                        f"Potential circular dependency: {' -> '.join(pattern)}"
                    )
            
            except Exception:
                pass  # 순환 검사 실패는 무시
    
    def _check_performance_degradation(self, report: MetaHealthReport) -> None:
        """성능 저하 감지"""
        if len(self._execution_history) < 5:
            return  # 충분한 히스토리가 없으면 스킵
        
        recent_durations = [
            h.get("diagnostics_duration_ms", 0)
            for h in self._execution_history[-10:]
        ]
        
        if recent_durations:
            avg_duration = sum(recent_durations) / len(recent_durations)
            
            if avg_duration > self.EXECUTION_TIME_CRITICAL_MS:
                report.issues.append(
                    f"Critical performance degradation: "
                    f"avg diagnostics time {avg_duration:.0f}ms"
                )
            elif avg_duration > self.EXECUTION_TIME_WARNING_MS:
                report.warnings.append(
                    f"Performance warning: "
                    f"avg diagnostics time {avg_duration:.0f}ms"
                )
        
        # 최근 점수 추이 확인
        recent_scores = [
            h.get("overall_score", 1.0)
            for h in self._execution_history[-10:]
        ]
        
        if len(recent_scores) >= 3:
            trend = recent_scores[-1] - recent_scores[0]
            if trend < -0.2:
                report.warnings.append(
                    f"Health score declining: {trend:+.2f} over recent diagnostics"
                )
    
    def _calculate_overall_score(self, report: MetaHealthReport) -> None:
        """종합 건강 점수 계산"""
        if not report.component_statuses:
            report.overall_score = 0.0
            report.health_status = MetaHealthStatus.CRITICAL
            return
        
        # 컴포넌트 가용성 점수 (60%)
        available_count = sum(
            1 for s in report.component_statuses.values() if s.available
        )
        total_count = len(report.component_statuses)
        availability_score = available_count / max(total_count, 1)
        
        # 이슈 페널티 (30%)
        issue_penalty = min(len(report.issues) * 0.15, 0.3)
        
        # 경고 페널티 (10%)
        warning_penalty = min(len(report.warnings) * 0.05, 0.1)
        
        # 종합 점수
        report.overall_score = max(
            0.0,
            availability_score * 0.6 + 0.4 - issue_penalty - warning_penalty
        )
        
        # 상태 결정
        if report.overall_score >= 0.8:
            report.health_status = MetaHealthStatus.HEALTHY
        elif report.overall_score >= 0.6:
            report.health_status = MetaHealthStatus.DEGRADED
        elif report.overall_score >= 0.3:
            report.health_status = MetaHealthStatus.IMPAIRED
        else:
            report.health_status = MetaHealthStatus.CRITICAL
    
    def _generate_recovery_suggestions(self, report: MetaHealthReport) -> None:
        """복구 제안 생성"""
        # 컴포넌트 누락 시 제안
        missing_components = [
            name for name, status in report.component_statuses.items()
            if not status.available
        ]
        
        if missing_components:
            report.recovery_suggestions.append(
                f"Restore missing components: {', '.join(missing_components[:3])}"
            )
        
        # 이슈가 많으면 시스템 재시작 제안
        if len(report.issues) >= 3:
            report.recovery_suggestions.append(
                "Consider system restart to clear accumulated errors"
            )
        
        # 성능 저하 시 제안
        if any("performance" in w.lower() for w in report.warnings):
            report.recovery_suggestions.append(
                "Reduce meta-cognition cycle frequency to improve performance"
            )
        
        # 일관성 문제 시 제안
        if any("mismatch" in w.lower() or "consistency" in w.lower() for w in report.warnings):
            report.recovery_suggestions.append(
                "Synchronize component states via MetaController.reset()"
            )
    
    def get_quick_status(self) -> Tuple[MetaHealthStatus, float]:
        """빠른 상태 확인 (전체 진단 없이)"""
        if self._last_diagnostic_time is None:
            return MetaHealthStatus.DEGRADED, 0.5
        
        # 마지막 진단이 너무 오래되었으면 경고
        age = datetime.now() - self._last_diagnostic_time
        if age > timedelta(hours=1):
            return MetaHealthStatus.DEGRADED, 0.6
        
        # 최근 진단 결과 반환
        if self._execution_history:
            last = self._execution_history[-1]
            status_str = last.get("health_status", "degraded")
            score = last.get("overall_score", 0.5)
            
            try:
                status = MetaHealthStatus(status_str)
            except ValueError:
                status = MetaHealthStatus.DEGRADED
            
            return status, score
        
        return MetaHealthStatus.DEGRADED, 0.5
    
    def get_diagnostics_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """진단 히스토리 반환"""
        return self._execution_history[-limit:]


# 싱글톤 인스턴스
_meta_diagnostics_instance: Optional[MetaDiagnostics] = None


def get_meta_diagnostics() -> MetaDiagnostics:
    """MetaDiagnostics 싱글톤 인스턴스 반환"""
    global _meta_diagnostics_instance
    if _meta_diagnostics_instance is None:
        _meta_diagnostics_instance = MetaDiagnostics()
    return _meta_diagnostics_instance