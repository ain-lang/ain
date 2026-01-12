"""
SurrealDB API Client (DEPRECATED)
=================================
⚠️ DEPRECATION WARNING ⚠️

이 모듈은 더 이상 사용되지 않습니다.
모든 SurrealDB 접근은 `database/surreal_bridge.py`를 통해 이루어져야 합니다.

Migration Guide:
    # 기존 코드 (Deprecated)
    from api.surrealdb import SurrealDBClient
    client = SurrealDBClient()
    result = client.query("SELECT * FROM table")
    
    # 새로운 코드 (Recommended)
    from database import get_bridge
    bridge = get_bridge()
    result = bridge.query_sync("SELECT * FROM table")

이 파일은 하위 호환성을 위해 유지되며,
내부적으로 database/surreal_bridge.py로 모든 호출을 위임합니다.
"""

import warnings
from typing import Any, Dict, List, Optional

# Deprecation Warning 발생
warnings.warn(
    "api/surrealdb.py is deprecated. Use database/surreal_bridge.py instead. "
    "Import: from database import get_bridge, SurrealArrowBridge",
    DeprecationWarning,
    stacklevel=2
)

# Bridge로 위임
try:
    from database.surreal_bridge import (
        SurrealArrowBridge,
        get_bridge,
        quick_push,
        quick_pull
    )
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False
    print("⚠️ database.surreal_bridge 임포트 실패. Legacy 모드로 작동합니다.")


class SurrealDBClient:
    """
    DEPRECATED: Legacy SurrealDB Client
    
    이 클래스는 하위 호환성을 위해 유지됩니다.
    내부적으로 SurrealArrowBridge로 모든 호출을 위임합니다.
    
    새로운 코드에서는 다음을 사용하세요:
        from database import get_bridge
        bridge = get_bridge()
    """
    
    def __init__(self, url=None, user=None, password=None, namespace="ain", database="core"):
        """
        Legacy 생성자 - Bridge로 위임
        
        Note: url, user, password 파라미터는 무시됩니다.
        Bridge는 환경변수에서 설정을 읽습니다.
        """
        warnings.warn(
            "SurrealDBClient is deprecated. Use 'from database import get_bridge' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.ns = namespace
        self.db = database
        
        # Bridge 인스턴스 획득
        if HAS_BRIDGE:
            self._bridge = get_bridge()
            print(f"🔗 SurrealDBClient: Bridge로 위임됨 (ns={namespace}, db={database})")
        else:
            self._bridge = None
            print("⚠️ SurrealDBClient: Bridge 없음 - 모든 쿼리가 실패합니다.")
    
    @property
    def bridge(self) -> Optional[SurrealArrowBridge]:
        """내부 Bridge 인스턴스 접근"""
        return self._bridge
    
    def query(self, sql: str) -> Dict[str, Any]:
        """
        SurrealQL 쿼리 실행 (Legacy Interface)
        
        내부적으로 Bridge의 query_sync()로 위임됩니다.
        
        Args:
            sql: SurrealQL 쿼리 문자열
            
        Returns:
            쿼리 결과 딕셔너리
        """
        if not self._bridge:
            return {"error": "Bridge not available", "result": None}
        
        try:
            result = self._bridge.query_sync(sql)
            return {"result": result, "error": None}
        except Exception as e:
            return {"error": str(e), "result": None}
    
    def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        레코드 생성 (Legacy Interface)
        
        Args:
            table: 테이블 이름
            data: 저장할 데이터
            
        Returns:
            생성된 레코드 정보
        """
        if not self._bridge:
            return {"error": "Bridge not available", "result": None}
        
        try:
            # Bridge의 push_batch를 사용하여 단일 레코드 저장
            import pyarrow as pa
            
            # 데이터를 Arrow Table로 변환
            columns = list(data.keys())
            arrays = [pa.array([v]) for v in data.values()]
            table_data = pa.table(dict(zip(columns, arrays)))
            
            success = self._bridge.push_batch(table_data, table)
            
            if success:
                return {"result": data, "error": None}
            else:
                return {"error": "Push failed", "result": None}
                
        except Exception as e:
            return {"error": str(e), "result": None}
    
    def select(self, table: str, record_id: str = None) -> Dict[str, Any]:
        """
        레코드 조회 (Legacy Interface)
        
        Args:
            table: 테이블 이름
            record_id: 특정 레코드 ID (선택)
            
        Returns:
            조회 결과
        """
        if record_id:
            sql = f"SELECT * FROM {table}:{record_id}"
        else:
            sql = f"SELECT * FROM {table}"
        
        return self.query(sql)
    
    def update(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        레코드 업데이트 (Legacy Interface)
        """
        import json
        data_json = json.dumps(data)
        sql = f"UPDATE {table}:{record_id} CONTENT {data_json}"
        return self.query(sql)
    
    def delete(self, table: str, record_id: str) -> Dict[str, Any]:
        """
        레코드 삭제 (Legacy Interface)
        """
        sql = f"DELETE {table}:{record_id}"
        return self.query(sql)
    
    def health_check(self) -> bool:
        """
        연결 상태 확인
        """
        if not self._bridge:
            return False
        return self._bridge.connected
    
    def __repr__(self):
        status = "connected" if self.health_check() else "disconnected"
        return f"<SurrealDBClient(DEPRECATED) ns={self.ns} db={self.db} status={status}>"


# =============================================================================
# Convenience Functions (Legacy Support)
# =============================================================================

def get_client(namespace: str = "ain", database: str = "core") -> SurrealDBClient:
    """
    DEPRECATED: SurrealDBClient 인스턴스 획득
    
    대신 사용하세요:
        from database import get_bridge
        bridge = get_bridge()
    """
    warnings.warn(
        "get_client() is deprecated. Use 'from database import get_bridge' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return SurrealDBClient(namespace=namespace, database=database)


# =============================================================================
# Direct Bridge Access (Recommended Migration Path)
# =============================================================================

def get_bridge_instance() -> Optional[SurrealArrowBridge]:
    """
    새로운 Bridge 인스턴스 직접 접근
    
    이것은 마이그레이션을 위한 편의 함수입니다.
    최종적으로는 직접 database 패키지에서 임포트하세요:
        from database import get_bridge
    """
    if HAS_BRIDGE:
        return get_bridge()
    return None