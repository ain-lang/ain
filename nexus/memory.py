"""
Nexus Memory: Vector Memory (LanceBridge 연동) - 의미 기반 기억 저장/검색
"""
import hashlib
from typing import Optional, List, Dict, Any

# LanceBridge 임포트 (Step 4: Vector Memory)
try:
    from database.lance_bridge import get_lance_bridge, LanceBridge, LANCE_AVAILABLE
    HAS_LANCE = LANCE_AVAILABLE
except ImportError:
    HAS_LANCE = False
    LanceBridge = None


class VectorMemory:
    """Vector Memory 관리자 - LanceBridge 연동"""
    
    EMBEDDING_DIM = 384
    
    def __init__(self):
        self._lance_bridge: Optional[LanceBridge] = None
        self._lance_connected: bool = False
        self._init_lance_bridge()
    
    def _init_lance_bridge(self):
        """LanceBridge 싱글톤 초기화 (실패 시 Graceful Degradation)"""
        if not HAS_LANCE:
            print("ℹ️ Nexus: LanceBridge 미사용 (라이브러리 미설치)")
            return
        
        try:
            self._lance_bridge = get_lance_bridge()
            self._lance_connected = self._lance_bridge.is_connected
            
            if self._lance_connected:
                print(f"✅ Nexus: LanceBridge 연결 성공 (기억 수: {self._lance_bridge.count_memories()})")
            else:
                print("⚠️ Nexus: LanceBridge 연결 실패. JSON-Only 모드로 작동.")
        except Exception as e:
            print(f"❌ Nexus: LanceBridge 초기화 오류 - {e}")
            self._lance_bridge = None
            self._lance_connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._lance_connected
    
    @property
    def bridge(self):
        return self._lance_bridge
    
    def text_to_embedding(self, text: str) -> List[float]:
        """
        간단한 텍스트 → 벡터 변환 (임베딩 모델 없이)
        해시 기반 결정론적 벡터 생성
        """
        normalized = text.lower().strip()
        words = normalized.split()
        word_count = len(words)
        
        vector = []
        
        # 텍스트 전체 해시를 기반으로 초기 벡터 생성
        full_hash = hashlib.sha256(normalized.encode()).hexdigest()
        for i in range(0, min(len(full_hash), self.EMBEDDING_DIM * 2), 2):
            val = int(full_hash[i:i+2], 16) / 255.0
            vector.append(val)
        
        # 단어별 해시 추가
        for word in words[:50]:
            word_hash = hashlib.md5(word.encode()).hexdigest()[:8]
            for i in range(0, 8, 2):
                if len(vector) >= self.EMBEDDING_DIM:
                    break
                val = int(word_hash[i:i+2], 16) / 255.0
                vector.append(val)
        
        # 차원 맞추기
        if len(vector) < self.EMBEDDING_DIM:
            padding_val = (word_count % 100) / 100.0
            vector.extend([padding_val] * (self.EMBEDDING_DIM - len(vector)))
        else:
            vector = vector[:self.EMBEDDING_DIM]
        
        return vector
    
    def store(
        self, 
        text: str, 
        memory_type: str = "evolution",
        source: str = "nexus",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """텍스트를 벡터화하여 LanceDB에 저장"""
        if not self._lance_connected or not self._lance_bridge:
            return False
        
        try:
            vector = self.text_to_embedding(text)
            success = self._lance_bridge.add_memory(
                text=text,
                vector=vector,
                memory_type=memory_type,
                source=source,
                metadata=metadata
            )
            return success
        except Exception as e:
            print(f"⚠️ Vector DB 저장 실패: {e}")
            return False
    
    def search(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """의미 기반 기억 검색"""
        if not self._lance_connected or not self._lance_bridge:
            return []
        
        try:
            query_vector = self.text_to_embedding(query_text)
            results = self._lance_bridge.search_memory(
                query_vector=query_vector,
                limit=limit,
                memory_type=memory_type
            )
            if results:
                print(f"🔍 의미 검색 완료: {len(results)}개 기억 발견")
            return results
        except Exception as e:
            print(f"⚠️ 의미 검색 실패: {e}")
            return []
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 저장된 벡터 기억 조회"""
        if not self._lance_connected or not self._lance_bridge:
            return []
        return self._lance_bridge.get_recent_memories(limit=limit)
    
    def count(self) -> int:
        """저장된 기억 수"""
        if not self._lance_connected or not self._lance_bridge:
            return 0
        return self._lance_bridge.count_memories()
