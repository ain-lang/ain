"""
Engine Reflex Diagnostics: 직관 시스템(Reflex) 무결성 진단
Step 7 & 8: Meta-Cognition applied to Intuition System

이 모듈은 메타인지 시스템이 직관(System 1) 하위 시스템의 건전성을
스스로 점검할 수 있는 진단 도구를 제공한다.

DecisionGate가 직관에 의존하기 전에, 이 모듈을 통해
ReflexRegistry, ReflexStore, ReflexArrowBridge가 정상 작동하는지 확인한다.

Architecture:
    MetaDiagnostics (engine/meta_diagnostics.py)
        ↓ 호출
    ReflexDiagnostics (이 모듈)
        ↓ 점검
    ReflexRegistry, ReflexStore, ReflexArrowBridge
        ↓
    Health Report 반환

Usage:
    from engine.reflex_diagnostics import ReflexDiagnostics
    
    diagnostics = ReflexDiagnostics()
    report = diagnostics.run_diagnostics()
    if not report["registry_active"]:
        print("⚠️ Warning: System 1 (Intuition) is inactive.")
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

# Reflex Core Components
try:
    from engine.reflex import ReflexRegistry
    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False
    ReflexRegistry = None

try:
    from engine.reflex_store import ReflexStore
    HAS_STORE = True
except ImportError:
    HAS_STORE = False
    ReflexStore = None

# Arrow Bridge (Step 8 Integration)
try:
    from database.reflex_arrow_bridge import get_reflex_arrow_bridge
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False


class ReflexDiagnostics:
    """
    직관 시스템(Reflex) 진단기
    
    System 1의 구성 요소들이 정상적으로 로드되고 연결되었는지 확인한다.
    
    Components Checked:
    
    Usage:
        diagnostics = ReflexDiagnostics()
        report = diagnostics.run_diagnostics()
        
        if report["system_1_ready"]:
            print("System 1 (Intuition) is operational")
        else:
            print(f"System 1 health: {report['health_score']}")
    """
    
    def __init__(self, base_path: str = "."):
        """
        ReflexDiagnostics 초기화
        
        Args:
            base_path: 프로젝트 루트 경로 (ReflexStore 파일 위치 기준)
        """
        self.base_path = base_path
        self._store: Optional[ReflexStore] = None
        
        if HAS_STORE:
            try:
                self._store = ReflexStore(base_path)
            except Exception as e:
                print(f"⚠️ ReflexStore 초기화 실패: {e}")
                self._store = None

    def run_diagnostics(self) -> Dict[str, Any]:
        """
        전체 직관 시스템 진단 실행
        
        Returns:
            진단 결과 딕셔너리:
        """
        registry_status = self._check_registry()
        store_status = self._check_store()
        bridge_status = self._check_bridge()
        
        # 종합 점수 계산 (0.0 ~ 1.0)
        health_score = 0.0
        checks = [
            registry_status.get("active", False),
            store_status.get("accessible", False),
            bridge_status.get("connected", False)
        ]
        if checks:
            health_score = sum(1.0 for c in checks if c) / len(checks)

        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": round(health_score, 2),
            "registry": registry_status,
            "store": store_status,
            "bridge": bridge_status,
            "system_1_ready": health_score > 0.6,
            "components_available": {
                "registry": HAS_REGISTRY,
                "store": HAS_STORE,
                "bridge": HAS_BRIDGE
            }
        }

    def _check_registry(self) -> Dict[str, Any]:
        """
        ReflexRegistry 상태 점검
        
        Returns:
            레지스트리 상태 딕셔너리:
        """
        if not HAS_REGISTRY:
            return {
                "active": False,
                "error": "ReflexRegistry module not found",
                "count": 0,
                "status": "unavailable"
            }
            
        try:
            count = ReflexRegistry.count()
            return {
                "active": True,
                "count": count,
                "status": "healthy" if count > 0 else "empty",
                "error": None
            }
        except Exception as e:
            return {
                "active": False,
                "error": str(e),
                "count": 0,
                "status": "error"
            }

    def _check_store(self) -> Dict[str, Any]:
        """
        ReflexStore 파일 접근성 점검
        
        Returns:
            저장소 상태 딕셔너리:
        """
        if not HAS_STORE or self._store is None:
            return {
                "accessible": False,
                "error": "ReflexStore not initialized or module not found",
                "file_exists": False,
                "file_size_bytes": 0,
                "path": None,
                "reflex_count": 0
            }
            
        try:
            storage_file = getattr(self._store, "STORAGE_FILE", "learned_reflexes.json")
            file_path = os.path.join(self.base_path, storage_file)
            exists = os.path.exists(file_path)
            size = os.path.getsize(file_path) if exists else 0
            
            # 저장된 반사 행동 수 확인
            reflex_count = 0
            if hasattr(self._store, "load_all"):
                try:
                    reflexes = self._store.load_all()
                    reflex_count = len(reflexes) if reflexes else 0
                except Exception:
                    pass
            
            return {
                "accessible": True,
                "file_exists": exists,
                "file_size_bytes": size,
                "path": storage_file,
                "reflex_count": reflex_count,
                "error": None
            }
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e),
                "file_exists": False,
                "file_size_bytes": 0,
                "path": None,
                "reflex_count": 0
            }

    def _check_bridge(self) -> Dict[str, Any]:
        """
        ReflexArrowBridge 연결 점검
        
        Returns:
            브릿지 상태 딕셔너리:
        """
        if not HAS_BRIDGE:
            return {
                "connected": False,
                "error": "ReflexArrowBridge module not found",
                "schema_fields": 0,
                "ready_for_transfer": False
            }
            
        try:
            bridge = get_reflex_arrow_bridge()
            
            # 스키마 확인으로 건전성 테스트
            schema = getattr(bridge, "schema", None)
            schema_fields = len(schema) if schema is not None else 0
            
            return {
                "connected": True,
                "schema_fields": schema_fields,
                "ready_for_transfer": schema_fields > 0,
                "error": None
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "schema_fields": 0,
                "ready_for_transfer": False
            }

    def get_summary(self) -> str:
        """
        진단 결과를 사람이 읽기 쉬운 문자열로 반환
        
        Returns:
            진단 요약 문자열
        """
        report = self.run_diagnostics()
        
        lines = [
            "=== Reflex System Diagnostics ===",
            f"Timestamp: {report['timestamp']}",
            f"Health Score: {report['health_score']:.0%}",
            f"System 1 Ready: {'✅ Yes' if report['system_1_ready'] else '❌ No'}",
            "",
            "Component Status:",
            f"  Registry: {'✅ Active' if report['registry']['active'] else '❌ Inactive'}"
            f" ({report['registry'].get('count', 0)} reflexes)",
            f"  Store: {'✅ Accessible' if report['store']['accessible'] else '❌ Inaccessible'}"
            f" ({report['store'].get('reflex_count', 0)} learned)",
            f"  Bridge: {'✅ Connected' if report['bridge']['connected'] else '❌ Disconnected'}"
            f" ({report['bridge'].get('schema_fields', 0)} fields)",
        ]
        
        # 에러 정보 추가
        errors = []
        for component in ["registry", "store", "bridge"]:
            error = report[component].get("error")
            if error:
                errors.append(f"  - {component}: {error}")
        
        if errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(errors)
        
        return "\n".join(lines)


def get_reflex_diagnostics(base_path: str = ".") -> ReflexDiagnostics:
    """
    ReflexDiagnostics 싱글톤 인스턴스 반환
    
    Args:
        base_path: 프로젝트 루트 경로
    
    Returns:
        ReflexDiagnostics 인스턴스
    """
    if not hasattr(get_reflex_diagnostics, "_instance"):
        get_reflex_diagnostics._instance = ReflexDiagnostics(base_path)
    return get_reflex_diagnostics._instance