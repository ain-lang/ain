"""
AIN Embedding Service - Step 4: Vector Fuel
텍스트를 벡터로 변환하는 임베딩 서비스.
Gemini Embedding API를 사용하여 텍스트를 고차원 벡터로 변환한다.

Architecture:
    Nexus (Memory) -> EmbeddingService -> Gemini API -> Vector (List[float])
    
Usage:
    from api.embedding import get_embedding, EmbeddingService
    
    # 간단한 사용
    vector = get_embedding("Hello, world!")
    
    # 서비스 인스턴스 사용
    service = EmbeddingService()
    vector = service.embed("Hello, world!")
"""

import os
from typing import List, Optional

# Gemini API 임포트 (graceful fallback)
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("⚠️ google-generativeai 미설치. 임베딩 서비스 비활성화.")


class EmbeddingService:
    """
    Gemini Embedding API 래퍼 클래스
    
    텍스트를 입력받아 벡터(List[float])로 변환한다.
    API 호출 실패 시 해시 기반 폴백 벡터를 생성하여 시스템 안정성을 보장한다.
    
    Attributes:
        model_name: 사용할 임베딩 모델 (기본: text-embedding-004)
        dimension: 출력 벡터 차원 (기본: 768)
    """
    
    # Gemini text-embedding-004 모델 기준 768차원
    DEFAULT_MODEL = "models/text-embedding-004"
    DEFAULT_DIMENSION = 768
    
    _instance: Optional["EmbeddingService"] = None
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.model_name = self.DEFAULT_MODEL
        self.dimension = self.DEFAULT_DIMENSION
        self._api_available = False
        
        self._configure_api()
        self._initialized = True
    
    def _configure_api(self):
        """Gemini API 설정"""
        if not HAS_GENAI:
            print("ℹ️ EmbeddingService: google-generativeai 없음. 폴백 모드.")
            return
        
        # API 키 확인 (환경변수 또는 keys 모듈)
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            try:
                from api.keys import get_config
                config = get_config()
                api_key = config.get("gemini_api_key")
            except ImportError:
                pass
        
        if not api_key:
            print("⚠️ EmbeddingService: GEMINI_API_KEY 미설정. 폴백 모드.")
            return
        
        try:
            genai.configure(api_key=api_key)
            self._api_available = True
            print(f"✅ EmbeddingService 초기화 완료 (모델: {self.model_name})")
        except Exception as e:
            print(f"❌ EmbeddingService 초기화 실패: {e}")
            self._api_available = False
    
    @property
    def is_available(self) -> bool:
        """API 사용 가능 여부"""
        return self._api_available
    
    def embed(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        텍스트를 벡터로 변환
        
        Args:
            text: 변환할 텍스트
            task_type: 임베딩 용도 (retrieval_document, retrieval_query, 
                       semantic_similarity, classification, clustering)
        
        Returns:
            벡터 리스트 (List[float]) - 768차원
        """
        if not text or not text.strip():
            print("⚠️ 빈 텍스트. 영벡터 반환.")
            return [0.0] * self.dimension
        
        # 텍스트 정규화 (너무 긴 텍스트 처리)
        normalized_text = text.strip()
        if len(normalized_text) > 10000:
            normalized_text = normalized_text[:10000]
            print(f"⚠️ 텍스트 길이 초과. 10000자로 잘림.")
        
        # API 사용 가능하면 Gemini 호출
        if self._api_available:
            return self._embed_with_api(normalized_text, task_type)
        
        # 폴백: 해시 기반 결정론적 벡터
        return self._embed_fallback(normalized_text)
    
    def _embed_with_api(self, text: str, task_type: str) -> List[float]:
        """Gemini API를 통한 실제 임베딩 생성"""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type
            )
            
            embedding = result.get("embedding", [])
            
            if not embedding:
                print("⚠️ API 응답에 임베딩 없음. 폴백 사용.")
                return self._embed_fallback(text)
            
            # 차원 검증
            if len(embedding) != self.dimension:
                print(f"ℹ️ 임베딩 차원: {len(embedding)} (예상: {self.dimension})")
                self.dimension = len(embedding)
            
            return embedding
            
        except Exception as e:
            print(f"❌ Gemini Embedding API 오류: {e}")
            return self._embed_fallback(text)
    
    def _embed_fallback(self, text: str) -> List[float]:
        """
        해시 기반 결정론적 폴백 벡터 생성
        
        API 실패 시에도 시스템이 작동하도록 일관된 벡터를 생성한다.
        동일한 텍스트는 항상 동일한 벡터를 반환한다.
        """
        import hashlib
        
        normalized = text.lower().strip()
        
        # SHA-256 해시를 기반으로 벡터 생성
        hash_bytes = hashlib.sha256(normalized.encode('utf-8')).digest()
        
        vector = []
        
        # 해시 바이트를 반복하여 768차원 채우기
        for i in range(self.dimension):
            byte_idx = i % len(hash_bytes)
            # 0~1 범위로 정규화
            val = hash_bytes[byte_idx] / 255.0
            # 약간의 변형 추가 (위치에 따라)
            val = (val + (i % 10) / 100.0) % 1.0
            vector.append(val)
        
        return vector
    
    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """
        여러 텍스트를 배치로 임베딩
        
        Args:
            texts: 변환할 텍스트 리스트
            task_type: 임베딩 용도
        
        Returns:
            벡터 리스트의 리스트
        """
        return [self.embed(text, task_type) for text in texts]


# 싱글톤 인스턴스 접근 헬퍼
def get_embedding_service() -> EmbeddingService:
    """전역 EmbeddingService 인스턴스 반환"""
    return EmbeddingService()


def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    """
    편의 함수: 텍스트를 벡터로 변환
    
    Args:
        text: 변환할 텍스트
        task_type: 임베딩 용도
    
    Returns:
        벡터 리스트 (List[float])
    """
    service = get_embedding_service()
    return service.embed(text, task_type)