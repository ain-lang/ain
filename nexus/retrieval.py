"""
Nexus Retrieval: 의미론적 기억 검색 믹스인
Step 4: Vector Memory Integration - Semantic Context Injection

LanceDB에 저장된 의미론적 기억을 검색하여 LLM 프롬프트에 주입할 수 있도록
Nexus 엔진에 기억 검색 기능을 제공하는 Mixin 클래스.

Architecture:
    Nexus (Engine) --inherits--> RetrievalMixin --uses--> VectorMemory --uses--> LanceBridge
"""
from typing import List, Dict, Any, Optional


class RetrievalMixin:
    """
    기억 검색 기능을 제공하는 Mixin
    
    Nexus 클래스에 상속되어 벡터 DB(LanceDB)에서 의미론적 기억을 
    검색하는 기능을 추가한다.
    
    Prerequisites:
        - self.vector_memory: VectorMemory 인스턴스 (nexus/__init__.py에서 초기화)
    """
    
    def retrieve_relevant_memories(
        self, 
        query: str = "", 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        주어진 쿼리와 연관된 의미론적 기억(Semantic Memory)을 벡터 DB에서 검색한다.
        
        Args:
            query: 검색할 텍스트 (User Query or Current Thought)
                   빈 문자열이면 최근 기억을 반환
            limit: 반환할 기억의 개수
            memory_type: 특정 기억 유형으로 필터링 (episodic, semantic, procedural)
            
        Returns:
            기억 리스트 (text, distance, metadata 포함)
            검색 실패 시 빈 리스트 반환
        """
        # VectorMemory 모듈이 초기화되지 않았거나 없는 경우
        if not hasattr(self, 'vector_memory') or self.vector_memory is None:
            return []
        
        # VectorMemory 내부의 LanceBridge 연결 상태 확인
        if not self.vector_memory._lance_connected:
            return []
        
        try:
            # 쿼리가 비어있으면 최근 기억 반환
            if not query or not query.strip():
                return self._get_recent_memories_safe(limit)
            
            # 의미 기반 검색 수행 (VectorMemory.search 활용)
            # VectorMemory는 내부적으로 텍스트를 벡터로 변환하고 LanceDB에서 검색
            results = self.vector_memory.search(
                query_text=query,
                limit=limit,
                memory_type=memory_type
            )
            
            if results:
                print(f"🔍 Retrieval: {len(results)}개 관련 기억 발견 (query: {query[:30]}...)")
            
            return results
            
        except Exception as e:
            print(f"⚠️ Memory Retrieval Failed: {e}")
            # 검색 실패 시 최근 기억으로 Fallback
            return self._get_recent_memories_safe(limit)
    
    def _get_recent_memories_safe(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        최근 기억을 안전하게 가져오는 헬퍼 메서드
        
        Args:
            limit: 반환할 기억의 개수
            
        Returns:
            최근 기억 리스트
        """
        try:
            if hasattr(self, 'vector_memory') and self.vector_memory:
                return self.vector_memory.get_recent(limit=limit)
        except Exception as e:
            print(f"⚠️ Recent Memory Fetch Failed: {e}")
        
        return []
    
    def get_recent_insights(self, limit: int = 3) -> str:
        """
        최근 형성된 통찰(Insight) 기억을 포맷된 문자열로 반환
        
        CorpusCallosum의 synthesize_context에서 프롬프트에 주입할 때 사용.
        
        Args:
            limit: 반환할 통찰의 개수
            
        Returns:
            포맷된 통찰 문자열 (기억이 없으면 안내 메시지)
        """
        memories = self.retrieve_relevant_memories("", limit)
        
        if not memories:
            return "No semantic memories formed yet. (Cold Start)"
        
        formatted_lines = []
        for idx, mem in enumerate(memories, 1):
            text = mem.get('text', '')[:200]  # 텍스트 길이 제한
            source = mem.get('source', 'unknown')
            mem_type = mem.get('memory_type', 'unknown')
            timestamp = mem.get('timestamp', '')[:10]  # 날짜만 표시
            
            # 포맷: [타입] 텍스트 (출처, 날짜)
            formatted_lines.append(
                f"  {idx}. [{mem_type}] {text}... (Source: {source}, {timestamp})"
            )
        
        return "\n".join(formatted_lines)
    
    def has_semantic_memory(self) -> bool:
        """
        의미론적 기억 시스템이 활성화되어 있는지 확인
        
        Returns:
            LanceDB 연결 여부
        """
        if not hasattr(self, 'vector_memory') or self.vector_memory is None:
            return False
        return self.vector_memory._lance_connected
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        기억 시스템의 현재 상태를 반환
        
        Returns:
            기억 통계 딕셔너리
        """
        stats = {
            "vector_memory_active": False,
            "total_memories": 0,
            "lance_connected": False
        }
        
        if hasattr(self, 'vector_memory') and self.vector_memory:
            stats["vector_memory_active"] = True
            stats["lance_connected"] = self.vector_memory._lance_connected
            stats["total_memories"] = self.vector_memory.count()
        
        return stats