"""
AIN Nexus Engine: 시스템의 기억(Evolution History)과 대화(Episodic Memory)를 관리한다.

모듈 구조:

Step 4 Integration:
    Nexus는 이제 RetrievalMixin을 상속받아 벡터 DB(LanceDB)에서
    의미론적 기억을 검색하는 기능을 갖추게 되었다.
"""
from typing import Optional, List, Dict, Any

import pyarrow as pa

from .core import NexusCore
from .storage import load_json, save_json
from .memory import VectorMemory
from .history import HistoryManager
from .arrow import ArrowConverter
from .retrieval import RetrievalMixin


class Nexus(NexusCore, RetrievalMixin):
    """
    AIN의 Nexus Engine: 시스템의 기억을 관리한다.
    
    하위 호환성을 위해 기존 인터페이스를 모두 유지하면서
    내부적으로 모듈화된 컴포넌트를 사용한다.
    
    Step 4 Evolution:
        RetrievalMixin을 상속받아 retrieve_relevant_memories(),
        get_recent_insights() 등의 의미론적 검색 기능을 갖추었다.
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
        self._history_manager = HistoryManager(
            memory_file=memory_file,
            dialogue_file=dialogue_file,
            vector_memory=self._vector_memory
        )
        self._arrow_converter = ArrowConverter()
        
        print("✅ Nexus Engine 초기화 완료 (RetrievalMixin 통합)")
    
    @property
    def vector_memory(self) -> VectorMemory:
        """
        RetrievalMixin이 요구하는 vector_memory 프로퍼티.
        내부 _vector_memory 인스턴스를 노출한다.
        """
        return self._vector_memory
    
    def record_evolution(
        self, 
        action: str, 
        file: str, 
        description: str, 
        status: str = "success",
        error: str = None
    ):
        """진화 기록 저장 (하위 호환성)"""
        self._history_manager.record_evolution(
            action=action,
            file=file,
            description=description,
            status=status,
            error=error
        )
        
        # 메트릭스 업데이트
        if status == "success":
            self.metrics["total_evolutions"] += 1
            self.metrics["growth_score"] += 10
            
            # 레벨업 체크
            new_level = 1 + (self.metrics["total_evolutions"] // 10)
            if new_level > self.metrics["level"]:
                self.metrics["level"] = new_level
                print(f"🎉 Nexus 레벨 업! Lv.{self.metrics['level']}")
            
            self._save_metrics()
        
        # 이벤트 발생
        self.emit("evolution_recorded", {
            "action": action,
            "file": file,
            "status": status
        })
    
    def record_conversation(self, role: str, content: str, metadata: Dict = None):
        """대화 기록 저장 (하위 호환성)"""
        self._history_manager.record_conversation(
            role=role,
            content=content,
            metadata=metadata
        )
    
    def get_evolution_summary(self, limit: int = 10) -> str:
        """진화 기록 요약 (하위 호환성)"""
        return self._history_manager.get_evolution_summary(limit=limit)
    
    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 진화 기록 반환 (하위 호환성)"""
        return self._history_manager.get_recent_history(limit=limit)
    
    def get_dialogue_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """대화 컨텍스트 반환 (하위 호환성)"""
        return self._history_manager.get_dialogue_context(limit=limit)
    
    def export_history_as_arrow(self) -> Optional[pa.Table]:
        """진화 기록을 Arrow Table로 직렬화 (하위 호환성)"""
        history_cache = self._history_manager._evolution_cache
        return self._arrow_converter.export_history(history_cache)
    
    def text_to_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩 벡터로 변환 (하위 호환성)"""
        return self._vector_memory.text_to_embedding(text)
    
    def store_semantic_memory(
        self, 
        text: str, 
        memory_type: str = "evolution",
        source: str = "nexus",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """의미론적 기억 저장 (하위 호환성)"""
        return self._vector_memory.store(
            text=text,
            memory_type=memory_type,
            source=source,
            metadata=metadata
        )
    
    def search_semantic_memory(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """의미 기반 기억 검색 (하위 호환성)"""
        return self._vector_memory.search(
            query_text=query_text,
            limit=limit,
            memory_type=memory_type
        )
    
    def get_memory_count(self) -> int:
        """저장된 벡터 기억 수 (하위 호환성)"""
        return self._vector_memory.count()
    
    def is_vector_memory_connected(self) -> bool:
        """벡터 메모리 연결 상태 (하위 호환성)"""
        return self._vector_memory.is_connected