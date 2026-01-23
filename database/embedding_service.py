"""
AIN Database Embedding Service - Step 4: Vector Fuel Integration
텍스트를 벡터로 변환하는 임베딩 서비스의 데이터베이스 레이어 통합 모듈.

이 모듈은 api/embedding.py의 EmbeddingService를 래핑하여
LanceBridge와 원활하게 연동되도록 추가 기능을 제공한다.

Features:
- 배치 임베딩 처리 (여러 텍스트를 한번에 벡터화)
- 캐싱 지원 (동일 텍스트 중복 호출 방지)
- LanceBridge와의 통합 인터페이스

Architecture:
    Nexus -> DatabaseEmbeddingService -> api/embedding.py -> Gemini API
                                      -> LanceBridge (Vector Storage)

Usage:
    from database.embedding_service import DatabaseEmbeddingService, get_db_embedding_service
    
    service = get_db_embedding_service()
    vector = service.embed_and_store("Hello, world!", memory_type="semantic")
    vectors = service.batch_embed(["text1", "text2", "text3"])
"""

import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# API Embedding Service 임포트
try:
    from api.embedding import EmbeddingService, get_embedding, HAS_GENAI
    HAS_EMBEDDING = True
except ImportError:
    HAS_EMBEDDING = False
    HAS_GENAI = False
    print("⚠️ api/embedding.py 임포트 실패. 임베딩 서비스 비활성화.")

# LanceBridge 임포트
try:
    from database.lance_bridge import get_lance_bridge, LanceBridge, LANCE_AVAILABLE
    HAS_LANCE = LANCE_AVAILABLE
except ImportError:
    HAS_LANCE = False
    LanceBridge = None


class EmbeddingCache:
    """
    임베딩 캐시 - 동일 텍스트에 대한 중복 API 호출 방지
    
    메모리 기반 LRU 캐시로, 시스템 재시작 시 초기화됨.
    영구 캐싱이 필요하면 LanceDB에서 검색하여 재사용.
    """
    
    MAX_CACHE_SIZE = 1000  # 최대 캐시 항목 수
    
    def __init__(self):
        self._cache: Dict[str, List[float]] = {}
        self._access_order: List[str] = []  # LRU 추적
    
    def _compute_key(self, text: str) -> str:
        """텍스트의 해시 키 생성"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def get(self, text: str) -> Optional[List[float]]:
        """캐시에서 벡터 조회"""
        key = self._compute_key(text)
        if key in self._cache:
            # LRU 업데이트
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, text: str, vector: List[float]):
        """캐시에 벡터 저장"""
        key = self._compute_key(text)
        
        # 캐시 크기 제한 (LRU 방출)
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = vector
        self._access_order.append(key)
    
    def clear(self):
        """캐시 초기화"""
        self._cache.clear()
        self._access_order.clear()
    
    def stats(self) -> Dict[str, int]:
        """캐시 통계"""
        return {
            "size": len(self._cache),
            "max_size": self.MAX_CACHE_SIZE
        }


class DatabaseEmbeddingService:
    """
    데이터베이스 레이어 임베딩 서비스
    
    api/embedding.py의 EmbeddingService를 래핑하여
    캐싱, 배치 처리, LanceBridge 통합 기능을 제공한다.
    
    Attributes:
        embedding_service: 기본 임베딩 서비스 (Gemini API)
        lance_bridge: 벡터 저장소 (LanceDB)
        cache: 임베딩 캐시
    """
    
    _instance: Optional["DatabaseEmbeddingService"] = None
    VECTOR_DIM = 384  # MiniLM 기준 (LanceBridge와 동일)
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 기본 임베딩 서비스
        self._embedding_service: Optional[EmbeddingService] = None
        if HAS_EMBEDDING:
            try:
                from api.embedding import EmbeddingService
                self._embedding_service = EmbeddingService()
            except Exception as e:
                print(f"⚠️ EmbeddingService 초기화 실패: {e}")
        
        # LanceBridge 연결
        self._lance_bridge: Optional[LanceBridge] = None
        if HAS_LANCE:
            try:
                self._lance_bridge = get_lance_bridge()
            except Exception as e:
                print(f"⚠️ LanceBridge 연결 실패: {e}")
        
        # 캐시 초기화
        self._cache = EmbeddingCache()
        
        # 통계
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "stored_count": 0
        }
        
        self._initialized = True
        print("✅ DatabaseEmbeddingService 초기화 완료")
    
    @property
    def is_available(self) -> bool:
        """임베딩 서비스 사용 가능 여부"""
        return self._embedding_service is not None
    
    @property
    def is_lance_connected(self) -> bool:
        """LanceBridge 연결 여부"""
        return self._lance_bridge is not None and self._lance_bridge.is_connected
    
    def embed(self, text: str, use_cache: bool = True) -> List[float]:
        """
        단일 텍스트를 벡터로 변환
        
        Args:
            text: 변환할 텍스트
            use_cache: 캐시 사용 여부
        
        Returns:
            임베딩 벡터 (VECTOR_DIM 차원)
        """
        self._stats["total_requests"] += 1
        
        # 캐시 확인
        if use_cache:
            cached = self._cache.get(text)
            if cached is not None:
                self._stats["cache_hits"] += 1
                return cached
        
        # API 호출
        vector = self._call_embedding_api(text)
        
        # 캐시 저장
        if use_cache and vector:
            self._cache.set(text, vector)
        
        return vector
    
    def _call_embedding_api(self, text: str) -> List[float]:
        """실제 임베딩 API 호출"""
        self._stats["api_calls"] += 1
        
        if self._embedding_service:
            try:
                return self._embedding_service.embed(text)
            except Exception as e:
                print(f"⚠️ 임베딩 API 호출 실패: {e}")
        
        # 폴백: 해시 기반 의사 벡터
        return self._generate_fallback_vector(text)
    
    def _generate_fallback_vector(self, text: str) -> List[float]:
        """API 실패 시 해시 기반 의사 벡터 생성"""
        import hashlib
        hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()
        
        vector = []
        for i in range(self.VECTOR_DIM):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] / 255.0) * 2 - 1  # -1 ~ 1 범위
            vector.append(value)
        
        return vector
    
    def batch_embed(
        self, 
        texts: List[str], 
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        여러 텍스트를 배치로 벡터 변환
        
        캐시 히트된 항목은 API 호출에서 제외하여 비용 절감.
        
        Args:
            texts: 변환할 텍스트 목록
            use_cache: 캐시 사용 여부
        
        Returns:
            임베딩 벡터 목록 (입력 순서 유지)
        """
        results: List[Optional[List[float]]] = [None] * len(texts)
        texts_to_embed: List[Tuple[int, str]] = []  # (index, text)
        
        # 1단계: 캐시 확인
        for i, text in enumerate(texts):
            self._stats["total_requests"] += 1
            
            if use_cache:
                cached = self._cache.get(text)
                if cached is not None:
                    self._stats["cache_hits"] += 1
                    results[i] = cached
                    continue
            
            texts_to_embed.append((i, text))
        
        # 2단계: 캐시 미스된 항목 API 호출
        for idx, text in texts_to_embed:
            vector = self._call_embedding_api(text)
            results[idx] = vector
            
            if use_cache:
                self._cache.set(text, vector)
        
        return results
    
    def embed_and_store(
        self,
        text: str,
        memory_type: str = "semantic",
        source: str = "embedding_service",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[float], bool]:
        """
        텍스트를 벡터로 변환하고 LanceDB에 저장
        
        Args:
            text: 저장할 텍스트
            memory_type: 기억 유형 (semantic, episodic, procedural)
            source: 기억 출처
            metadata: 추가 메타데이터
        
        Returns:
            (벡터, 저장 성공 여부) 튜플
        """
        # 1. 임베딩 생성
        vector = self.embed(text)
        
        # 2. LanceDB에 저장
        stored = False
        if self.is_lance_connected:
            try:
                stored = self._lance_bridge.add_memory(
                    text=text,
                    vector=vector,
                    memory_type=memory_type,
                    source=source,
                    metadata=metadata
                )
                if stored:
                    self._stats["stored_count"] += 1
            except Exception as e:
                print(f"⚠️ LanceDB 저장 실패: {e}")
        
        return vector, stored
    
    def search_similar(
        self,
        text: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트와 유사한 기억 검색
        
        Args:
            text: 검색 쿼리 텍스트
            limit: 반환할 결과 수
            memory_type: 특정 기억 유형으로 필터링
        
        Returns:
            유사한 기억 목록
        """
        if not self.is_lance_connected:
            return []
        
        # 쿼리 벡터 생성
        query_vector = self.embed(text)
        
        # LanceDB 검색
        try:
            return self._lance_bridge.search_memory(
                query_vector=query_vector,
                limit=limit,
                memory_type=memory_type
            )
        except Exception as e:
            print(f"⚠️ 유사 기억 검색 실패: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계 반환"""
        cache_stats = self._cache.stats()
        
        return {
            **self._stats,
            "cache": cache_stats,
            "embedding_available": self.is_available,
            "lance_connected": self.is_lance_connected,
            "cache_hit_rate": (
                self._stats["cache_hits"] / max(self._stats["total_requests"], 1)
            ) * 100
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        print("🗑️ 임베딩 캐시 초기화됨")


# 싱글톤 인스턴스 접근 헬퍼
def get_db_embedding_service() -> DatabaseEmbeddingService:
    """전역 DatabaseEmbeddingService 인스턴스 반환"""
    return DatabaseEmbeddingService()


# 편의 함수: 단일 텍스트 임베딩 + 저장
def embed_and_store(
    text: str,
    memory_type: str = "semantic",
    source: str = "quick_embed"
) -> Tuple[List[float], bool]:
    """
    빠른 임베딩 + 저장 헬퍼 함수
    
    Usage:
        from database.embedding_service import embed_and_store
        vector, stored = embed_and_store("Hello, world!")
    """
    service = get_db_embedding_service()
    return service.embed_and_store(text, memory_type, source)