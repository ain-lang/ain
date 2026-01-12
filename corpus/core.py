"""
Corpus Core: CorpusCallosum 기본 초기화 및 연결 관리
"""
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

try:
    from database.surreal_bridge import SurrealArrowBridge
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False

try:
    from database.arrow_schema import get_node_schema
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False

try:
    from database.lance_bridge import get_lance_bridge, LanceBridge, LANCE_AVAILABLE
    HAS_LANCE = LANCE_AVAILABLE
except ImportError:
    HAS_LANCE = False
    LanceBridge = None


class CorpusCallosumCore:
    """CorpusCallosum 기본 클래스"""
    
    EMBEDDING_DIM = 384
    
    def __init__(self, fact_core, nexus):
        self.left_brain = fact_core
        self.right_brain = nexus
        
        # SurrealArrowBridge
        self.bridge: Optional[SurrealArrowBridge] = None
        if HAS_BRIDGE:
            self.bridge = SurrealArrowBridge()
            print("🔗 CorpusCallosum: SurrealArrowBridge 초기화 완료")
        
        # LanceBridge (Vector Memory)
        self.vector_bridge: Optional[LanceBridge] = None
        self._vector_connected: bool = False
        if HAS_LANCE:
            try:
                self.vector_bridge = get_lance_bridge()
                self._vector_connected = self.vector_bridge.is_connected
                if self._vector_connected:
                    print(f"🧠 CorpusCallosum: LanceBridge 연결 성공 (기억 수: {self.vector_bridge.count_memories()})")
                else:
                    print("⚠️ CorpusCallosum: LanceBridge 연결 실패.")
            except Exception as e:
                print(f"❌ CorpusCallosum: LanceBridge 초기화 오류 - {e}")
        
        # 연결 상태 추적
        self._bridge_connected: bool = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_count: int = 0
        self._last_synced_evolution_index: int = 0
        
        # 캐시
        self._last_batch = None
        self._last_table = None
        
        # 스키마 설정
        if HAS_ARROW:
            self.context_schema = pa.schema([
                ('source', pa.string()),
                ('key', pa.string()),
                ('value', pa.string()),
                ('timestamp', pa.timestamp('ms'))
            ])
            
            if HAS_SCHEMA:
                self.fact_schema = get_node_schema()
            else:
                self.fact_schema = pa.schema([
                    ('id', pa.string()),
                    ('label', pa.string()),
                    ('data_json', pa.string()),
                    ('edges_count', pa.int32()),
                    ('timestamp', pa.timestamp('ms'))
                ])
    
    async def initialize_bridge(self) -> bool:
        """브릿지 연결 초기화"""
        if self.bridge:
            try:
                self._bridge_connected = await self.bridge.connect()
                if self._bridge_connected:
                    print("✅ CorpusCallosum: SurrealDB 브릿지 연결 성공")
                else:
                    print("⚠️ CorpusCallosum: 브릿지 연결 실패, Memory-Only 모드")
                return self._bridge_connected
            except Exception as e:
                print(f"❌ CorpusCallosum: 브릿지 초기화 오류 - {e}")
                self._bridge_connected = False
        return False
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """동기화 통계"""
        return {
            "surreal_connected": self._bridge_connected,
            "lance_connected": self._vector_connected,
            "last_sync_time": self._last_sync_time.isoformat() if self._last_sync_time else None,
            "sync_count": self._sync_count,
            "last_synced_evolution_index": self._last_synced_evolution_index,
        }
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """브릿지 상태 정보"""
        return {
            "bridge_active": self.bridge is not None,
            "bridge_connected": self._bridge_connected,
            "vector_connected": self._vector_connected,
            "arrow_available": HAS_ARROW,
            "lance_available": HAS_LANCE,
            "last_sync_time": str(self._last_sync_time) if self._last_sync_time else None,
            "sync_count": self._sync_count,
            "last_batch_rows": self._last_batch.num_rows if self._last_batch else 0,
            "last_table_rows": self._last_table.num_rows if self._last_table else 0,
        }
