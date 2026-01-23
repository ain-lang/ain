"""
AIN Nexus Engine: 시스템의 기억(Evolution History)과 대화(Episodic Memory)를 관리한다.

모듈 구조:
- core.py: 기본 클래스, 모듈 등록, 이벤트 시스템
- storage.py: JSON 파일 I/O
- memory.py: Vector Memory (LanceBridge 연동)
- history.py: Evolution/Conversation 기록
- arrow.py: Arrow Table 변환
"""
from typing import Optional, List, Dict, Any

import pyarrow as pa

from .core import NexusCore
from .storage import load_json, save_json
from .memory import VectorMemory
from .history import HistoryManager
from .arrow import ArrowConverter


class Nexus(NexusCore):
    """
    AIN의 Nexus Engine: 시스템의 기억을 관리한다.
    
    하위 호환성을 위해 기존 인터페이스를 모두 유지하면서
    내부적으로 모듈화된 컴포넌트를 사용한다.
    """
    
    EMBEDDING_DIM = 384  # 하위 호환성
    
    def __init__(
        self, 
        memory_file: str = "evolution_history.json", 
        dialogue_file: str = "dialogue_memory.json"
    ):
        super().__init__()
        
        self.memory_file = memory_file
        self.dialogue_file = dialogue_file
        
        # 모듈화된 컴포넌트
        self._vector_memory = VectorMemory()
        self._history = HistoryManager(
            memory_file=memory_file,
            dialogue_file=dialogue_file,
            vector_memory=self._vector_memory
        )
        self._arrow = ArrowConverter()
        
        # 하위 호환성: 기존 속성 연결
        self._lance_bridge = self._vector_memory.bridge
        self._lance_connected = self._vector_memory.is_connected
        self._evolution_history_cache = self._history.evolution_cache
        self._dialogue_cache = self._history._dialogue_cache

    # =========================================================================
    # Properties (consciousness.py에서 사용)
    # =========================================================================

    @property
    def vector_memory(self):
        """벡터 메모리 인스턴스 (외부 접근용)"""
        return self._vector_memory

    # =========================================================================
    # 하위 호환성 메서드 (기존 인터페이스 유지)
    # =========================================================================
    
    def load_data(self, filename: str):
        """범용 JSON 로드"""
        return load_json(filename)
    
    def save_data(self, filename: str, data) -> bool:
        """범용 JSON 저장"""
        return save_json(filename, data)
    
    def _init_lance_bridge(self):
        """하위 호환성: VectorMemory에서 처리"""
        pass
    
    def _load_metrics(self):
        """하위 호환성: NexusCore에서 처리"""
        super()._load_metrics()
    
    def _save_metrics(self):
        """하위 호환성: NexusCore에서 처리"""
        super()._save_metrics()
    
    def _load_history_cache(self):
        """하위 호환성: HistoryManager에서 처리"""
        pass
    
    # =========================================================================
    # Vector Memory (Step 4)
    # =========================================================================
    
    def _text_to_simple_embedding(self, text: str) -> List[float]:
        """텍스트 → 벡터 변환"""
        return self._vector_memory.text_to_embedding(text)
    
    def _store_to_vector_db(
        self, 
        text: str, 
        memory_type: str = "evolution",
        source: str = "nexus",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """벡터 DB에 저장"""
        return self._vector_memory.store(text, memory_type, source, metadata)
    
    def recall_memories(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """의미 기반 기억 회상"""
        if self._vector_memory.is_connected:
            results = self._vector_memory.search(query_text, limit, memory_type)
            if results:
                return results
        
        print("ℹ️ Vector Memory 비활성화. JSON 기반 검색으로 대체.")
        return self._history.fallback_keyword_search(query_text, limit, memory_type)
    
    def _fallback_keyword_search(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """키워드 기반 검색 (Fallback)"""
        return self._history.fallback_keyword_search(query_text, limit, memory_type)
    
    def recall_similar_evolutions(self, current_error: str, limit: int = 3) -> List[Dict[str, Any]]:
        """유사한 과거 진화 사례 검색"""
        return self.recall_memories(current_error, limit, memory_type="evolution")
    
    def get_recent_vector_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 벡터 기억 조회"""
        return self._vector_memory.get_recent(limit)
    
    # =========================================================================
    # History (Evolution/Conversation)
    # =========================================================================
    
    def record_evolution(
        self, 
        evolution_type: str, 
        action: str, 
        file: str, 
        description: str,
        status: str = "success", 
        error: str = None
    ) -> Dict[str, Any]:
        """진화 기록 저장"""
        record = self._history.record_evolution(
            evolution_type=evolution_type,
            action=action,
            file=file,
            description=description,
            status=status,
            error=error,
            emit_callback=self.emit
        )
        
        # 성장 지표 업데이트
        if status == "success":
            self.increment_growth(10)
        
        # 캐시 동기화
        self._evolution_history_cache = self._history.evolution_cache
        
        return record
    
    def record_conversation(self, role: str, content: str, session_id: str = "default"):
        """대화 기록 저장"""
        return self._history.record_conversation(role, content, session_id)
    
    def get_evolution_summary(self, limit: int = 5) -> str:
        """최근 진화 기록 요약"""
        return self._history.get_evolution_summary(limit)
    
    def get_lessons_learned(self, limit: int = 10) -> str:
        """실패 사례에서 학습한 교훈"""
        return self._history.get_lessons_learned(limit)

    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """전체 진화 기록 반환 (consciousness 모듈 호환용)"""
        return self._history.evolution_cache
    
    # =========================================================================
    # Arrow Table Operations
    # =========================================================================
    
    def export_history_as_arrow(self) -> Optional[pa.Table]:
        """진화 기록을 Arrow Table로 직렬화"""
        return self._arrow.export_history(self._history.evolution_cache)
    
    def load_history_from_arrow(self, table: pa.Table) -> bool:
        """Arrow Table에서 진화 기록 복원"""
        records = self._arrow.import_history(table)
        if records:
            self._history.evolution_cache = records
            self._evolution_history_cache = records
            save_json(self.memory_file, records)
            return True
        return False
    
    # =========================================================================
    # Status Report (확장)
    # =========================================================================
    
    def get_status_report(self) -> str:
        """시스템 상태 종합 보고"""
        report = super().get_status_report()
        report += f"- Cached History Records: {len(self._history.evolution_cache)}\n"
        
        if self._vector_memory.is_connected:
            report += f"- Vector Memories: {self._vector_memory.count()}\n"
            report += f"- Semantic Search: ✅ Enabled\n"
        else:
            report += f"- Vector Memories: N/A (Disabled)\n"
            report += f"- Semantic Search: ❌ Disabled\n"
        
        return report


# 하위 호환성: 기존 import 유지
__all__ = ['Nexus']
