"""
Engine Memory Diagnostics: 벡터 메모리 시스템 런타임 진단
Step 4 & 7: Vector Memory + Meta-Cognition Integration

이 모듈은 벡터 메모리 시스템(LanceBridge, VectorMemory)의 런타임 상태와
무결성을 실시간으로 점검하는 메타인지적 도구를 제공한다.

단위 테스트(test_vector_memory.py)가 '외부 검증'이라면,
이 모듈은 '자가 진단' - 시스템이 스스로 자신의 기억 저장소 상태를 인식한다.

Architecture:
    AINCore / MetaCognitionMixin
        ↓ 호출
    MemoryDiagnostics (이 모듈)
        ↓ 점검
    LanceBridge + VectorMemory (nexus/memory.py, database/lance_bridge.py)
        ↓
    DiagnosticReport 반환

Features:
    1. 연결 상태 점검 (Connection Health)
    2. 데이터 무결성 검증 (Integrity Check)
    3. 벡터 차원 일관성 확인 (Dimension Consistency)
    4. 저장소 용량 모니터링 (Capacity Monitoring)
    5. 최근 기억 품질 평가 (Memory Quality Assessment)

Usage:
    from engine.memory_diagnostics import MemoryDiagnostics, DiagnosticReport
    
    diagnostics = MemoryDiagnostics()
    report = diagnostics.run_full_diagnostics()
    
    if report.health_status == HealthStatus.CRITICAL:
        print(f"Memory system critical: {report.issues}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class HealthStatus(Enum):
    """메모리 시스템 건강 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


class DiagnosticCategory(Enum):
    """진단 카테고리"""
    CONNECTION = "connection"
    INTEGRITY = "integrity"
    DIMENSION = "dimension"
    CAPACITY = "capacity"
    QUALITY = "quality"


@dataclass
class DiagnosticIssue:
    """개별 진단 이슈"""
    category: DiagnosticCategory
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DiagnosticReport:
    """
    종합 진단 리포트
    
    Attributes:
        health_status: 전체 건강 상태
        issues: 발견된 이슈 목록
        metrics: 수집된 메트릭
        recommendations: 개선 권고사항
        timestamp: 진단 시각
    """
    health_status: HealthStatus
    issues: List[DiagnosticIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "health_status": self.health_status.value,
            "issues_count": len(self.issues),
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def summary(self) -> str:
        """사람이 읽기 쉬운 요약"""
        lines = [
            f"=== Memory Diagnostics Report ===",
            f"Status: {self.health_status.value.upper()}",
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Issues Found: {len(self.issues)}",
        ]
        
        if self.issues:
            lines.append("\nIssues:")
            for issue in self.issues:
                lines.append(f"  [{issue.severity}] {issue.category.value}: {issue.message}")
        
        if self.recommendations:
            lines.append("\nRecommendations:")
            for rec in self.recommendations:
                lines.append(f"  - {rec}")
        
        if self.metrics:
            lines.append("\nMetrics:")
            for key, value in self.metrics.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


class MemoryDiagnostics:
    """
    벡터 메모리 시스템 진단기
    
    LanceBridge와 VectorMemory의 런타임 상태를 점검하고
    문제가 있을 경우 구체적인 이슈와 권고사항을 제공한다.
    """
    
    EXPECTED_VECTOR_DIM = 768
    CAPACITY_WARNING_THRESHOLD = 10000
    CAPACITY_CRITICAL_THRESHOLD = 50000
    
    def __init__(self):
        self._lance_bridge = None
        self._vector_memory = None
        self._initialized = False
        self._init_components()
    
    def _init_components(self):
        """진단 대상 컴포넌트 초기화"""
        try:
            from database.lance_bridge import get_lance_bridge, LANCE_AVAILABLE
            if LANCE_AVAILABLE:
                self._lance_bridge = get_lance_bridge()
        except ImportError:
            pass
        
        try:
            from nexus.memory import VectorMemory
            self._vector_memory = VectorMemory()
        except ImportError:
            pass
        
        self._initialized = True
    
    def run_full_diagnostics(self) -> DiagnosticReport:
        """
        전체 진단 실행
        
        모든 진단 카테고리를 순차적으로 점검하고 종합 리포트를 반환한다.
        
        Returns:
            DiagnosticReport: 종합 진단 결과
        """
        issues: List[DiagnosticIssue] = []
        metrics: Dict[str, Any] = {}
        recommendations: List[str] = []
        
        conn_issues, conn_metrics = self._check_connection()
        issues.extend(conn_issues)
        metrics.update(conn_metrics)
        
        if metrics.get("lance_connected", False):
            integrity_issues, integrity_metrics = self._check_integrity()
            issues.extend(integrity_issues)
            metrics.update(integrity_metrics)
            
            dim_issues, dim_metrics = self._check_dimension_consistency()
            issues.extend(dim_issues)
            metrics.update(dim_metrics)
            
            cap_issues, cap_metrics = self._check_capacity()
            issues.extend(cap_issues)
            metrics.update(cap_metrics)
            
            quality_issues, quality_metrics = self._check_memory_quality()
            issues.extend(quality_issues)
            metrics.update(quality_metrics)
        
        health_status = self._determine_health_status(issues)
        recommendations = self._generate_recommendations(issues, metrics)
        
        return DiagnosticReport(
            health_status=health_status,
            issues=issues,
            metrics=metrics,
            recommendations=recommendations,
        )
    
    def _check_connection(self) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        """연결 상태 점검"""
        issues = []
        metrics = {
            "lance_available": False,
            "lance_connected": False,
            "vector_memory_available": False,
        }
        
        try:
            from database.lance_bridge import LANCE_AVAILABLE
            metrics["lance_available"] = LANCE_AVAILABLE
        except ImportError:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONNECTION,
                severity="critical",
                message="LanceBridge module not importable",
            ))
            return issues, metrics
        
        if not LANCE_AVAILABLE:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONNECTION,
                severity="warning",
                message="LanceDB library not installed",
            ))
            return issues, metrics
        
        if self._lance_bridge is not None:
            metrics["lance_connected"] = self._lance_bridge.is_connected
            if not self._lance_bridge.is_connected:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.CONNECTION,
                    severity="critical",
                    message="LanceBridge not connected to database",
                ))
        else:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CONNECTION,
                severity="critical",
                message="LanceBridge instance not available",
            ))
        
        if self._vector_memory is not None:
            metrics["vector_memory_available"] = True
            metrics["vector_memory_connected"] = self._vector_memory.is_connected
        
        return issues, metrics
    
    def _check_integrity(self) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        """데이터 무결성 점검"""
        issues = []
        metrics = {}
        
        if self._lance_bridge is None or not self._lance_bridge.is_connected:
            return issues, metrics
        
        try:
            count = self._lance_bridge.count_memories()
            metrics["total_memories"] = count
            
            if count == 0:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.INTEGRITY,
                    severity="info",
                    message="Memory bank is empty (no memories stored yet)",
                ))
            elif count == 1:
                recent = self._lance_bridge.get_recent_memories(limit=1)
                if recent and recent[0].get("id") == "init_0":
                    metrics["has_only_init_record"] = True
        except Exception as e:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.INTEGRITY,
                severity="warning",
                message=f"Failed to count memories: {str(e)}",
            ))
        
        return issues, metrics
    
    def _check_dimension_consistency(self) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        """벡터 차원 일관성 점검"""
        issues = []
        metrics = {
            "expected_dimension": self.EXPECTED_VECTOR_DIM,
        }
        
        if self._lance_bridge is None or not self._lance_bridge.is_connected:
            return issues, metrics
        
        try:
            bridge_dim = getattr(self._lance_bridge, "VECTOR_DIM", None)
            if bridge_dim is not None:
                metrics["lance_bridge_dimension"] = bridge_dim
                if bridge_dim != self.EXPECTED_VECTOR_DIM:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.DIMENSION,
                        severity="warning",
                        message=f"LanceBridge dimension mismatch: {bridge_dim} vs expected {self.EXPECTED_VECTOR_DIM}",
                    ))
        except Exception as e:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.DIMENSION,
                severity="info",
                message=f"Could not verify dimension: {str(e)}",
            ))
        
        if self._vector_memory is not None:
            vm_dim = getattr(self._vector_memory, "EMBEDDING_DIM", None)
            if vm_dim is not None:
                metrics["vector_memory_dimension"] = vm_dim
        
        return issues, metrics
    
    def _check_capacity(self) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        """저장소 용량 점검"""
        issues = []
        metrics = {}
        
        if self._lance_bridge is None or not self._lance_bridge.is_connected:
            return issues, metrics
        
        try:
            count = self._lance_bridge.count_memories()
            metrics["memory_count"] = count
            
            if count >= self.CAPACITY_CRITICAL_THRESHOLD:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.CAPACITY,
                    severity="critical",
                    message=f"Memory count ({count}) exceeds critical threshold ({self.CAPACITY_CRITICAL_THRESHOLD})",
                ))
            elif count >= self.CAPACITY_WARNING_THRESHOLD:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.CAPACITY,
                    severity="warning",
                    message=f"Memory count ({count}) approaching capacity threshold",
                ))
            
            utilization = (count / self.CAPACITY_CRITICAL_THRESHOLD) * 100
            metrics["capacity_utilization_percent"] = round(utilization, 2)
        except Exception as e:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.CAPACITY,
                severity="info",
                message=f"Could not check capacity: {str(e)}",
            ))
        
        return issues, metrics
    
    def _check_memory_quality(self) -> Tuple[List[DiagnosticIssue], Dict[str, Any]]:
        """최근 기억 품질 평가"""
        issues = []
        metrics = {}
        
        if self._lance_bridge is None or not self._lance_bridge.is_connected:
            return issues, metrics
        
        try:
            recent = self._lance_bridge.get_recent_memories(limit=10)
            metrics["recent_memories_count"] = len(recent)
            
            if recent:
                empty_text_count = sum(1 for m in recent if not m.get("text", "").strip())
                if empty_text_count > 0:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.QUALITY,
                        severity="warning",
                        message=f"{empty_text_count} recent memories have empty text",
                    ))
                
                types = {}
                for m in recent:
                    mtype = m.get("memory_type", "unknown")
                    types[mtype] = types.get(mtype, 0) + 1
                metrics["recent_memory_types"] = types
        except Exception as e:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.QUALITY,
                severity="info",
                message=f"Could not assess memory quality: {str(e)}",
            ))
        
        return issues, metrics
    
    def _determine_health_status(self, issues: List[DiagnosticIssue]) -> HealthStatus:
        """이슈 목록을 바탕으로 전체 건강 상태 결정"""
        critical_count = sum(1 for i in issues if i.severity == "critical")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count >= 3:
            return HealthStatus.DEGRADED
        elif warning_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _generate_recommendations(
        self, 
        issues: List[DiagnosticIssue], 
        metrics: Dict[str, Any]
    ) -> List[str]:
        """이슈와 메트릭을 바탕으로 개선 권고사항 생성"""
        recommendations = []
        
        if not metrics.get("lance_connected", False):
            recommendations.append("Verify LanceDB installation and connection settings")
            recommendations.append("Check LANCEDB_PATH environment variable")
        
        if metrics.get("total_memories", 0) == 0:
            recommendations.append("Store initial memories to bootstrap the vector memory system")
        
        utilization = metrics.get("capacity_utilization_percent", 0)
        if utilization > 80:
            recommendations.append("Consider implementing memory consolidation or pruning")
        
        for issue in issues:
            if issue.category == DiagnosticCategory.DIMENSION:
                recommendations.append("Ensure embedding service and LanceBridge use matching dimensions")
                break
        
        if not recommendations:
            recommendations.append("Memory system is healthy - no immediate action required")
        
        return recommendations
    
    def quick_health_check(self) -> Tuple[HealthStatus, str]:
        """
        빠른 건강 체크 (전체 진단보다 가벼움)
        
        Returns:
            (HealthStatus, 간단한 메시지)
        """
        try:
            from database.lance_bridge import LANCE_AVAILABLE
            if not LANCE_AVAILABLE:
                return HealthStatus.OFFLINE, "LanceDB not available"
        except ImportError:
            return HealthStatus.OFFLINE, "LanceBridge module not found"
        
        if self._lance_bridge is None:
            return HealthStatus.OFFLINE, "LanceBridge not initialized"
        
        if not self._lance_bridge.is_connected:
            return HealthStatus.CRITICAL, "LanceBridge not connected"
        
        try:
            count = self._lance_bridge.count_memories()
            if count >= self.CAPACITY_CRITICAL_THRESHOLD:
                return HealthStatus.CRITICAL, f"Capacity critical: {count} memories"
            elif count >= self.CAPACITY_WARNING_THRESHOLD:
                return HealthStatus.DEGRADED, f"Capacity warning: {count} memories"
            else:
                return HealthStatus.HEALTHY, f"OK: {count} memories stored"
        except Exception as e:
            return HealthStatus.DEGRADED, f"Query error: {str(e)}"


def get_memory_diagnostics() -> MemoryDiagnostics:
    """MemoryDiagnostics 싱글톤 인스턴스 반환"""
    if not hasattr(get_memory_diagnostics, "_instance"):
        get_memory_diagnostics._instance = MemoryDiagnostics()
    return get_memory_diagnostics._instance