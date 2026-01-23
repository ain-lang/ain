"""
Engine Pattern Recognition: 인지적 패턴 인식 및 익숙함 계산
Step 8: Intuition - System 1 (Fast) vs System 2 (Slow) 결정 로직

이 모듈은 현재 입력된 컨텍스트가 과거의 경험(Vector Memory)과 얼마나 유사한지
수치적으로 계산하여 '익숙함(Familiarity Score)'과 '놀람(Surprise Score)'을 반환한다.
이 점수는 시스템이 직관(Intuition)을 사용할지, 추론(Reasoning)을 사용할지 결정하는 기준이 된다.

Architecture:
    IntuitionMixin (engine/intuition.py)
        ↓ 호출
    PatternRecognizer (이 모듈)
        ↓ Nexus 조회 (retrieve_relevant_memories)
    Familiarity Score (0.0 ~ 1.0) 반환

Usage:
    from engine.pattern_recognition import PatternRecognizer
    
    recognizer = PatternRecognizer()
    score = recognizer.calculate_familiarity(nexus, "current_error_context")
    if score.familiarity_score > 0.8:
        # Use Intuition (Fast Path)
    else:
        # Use Reasoning (Dreamer)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nexus import Nexus


@dataclass
class PatternMetrics:
    """
    패턴 인식 결과 지표
    
    Attributes:
        familiarity_score: 익숙함 점수 (0.0 = 완전 낯섦, 1.0 = 완전 익숙함)
        surprise_score: 놀람 점수 (1.0 - familiarity_score)
        nearest_distance: 가장 가까운 기억과의 벡터 거리
        match_count: 임계값 이내의 유사 기억 개수
        top_memory_id: 가장 유사한 기억의 ID (있을 경우)
        top_memory_text: 가장 유사한 기억의 텍스트 요약 (있을 경우)
    """
    familiarity_score: float
    surprise_score: float
    nearest_distance: float
    match_count: int
    top_memory_id: Optional[str] = None
    top_memory_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "familiarity_score": round(self.familiarity_score, 4),
            "surprise_score": round(self.surprise_score, 4),
            "nearest_distance": round(self.nearest_distance, 4),
            "match_count": self.match_count,
            "top_memory_id": self.top_memory_id,
            "top_memory_text": self.top_memory_text[:100] if self.top_memory_text else None
        }


class PatternRecognizer:
    """
    패턴 인식기
    
    벡터 메모리 검색 결과를 분석하여 현재 상황의 '익숙함'을 정량화한다.
    이 클래스는 IntuitionMixin에서 호출되어 System 1/System 2 분기 결정에 사용된다.
    
    Attributes:
        FAMILIARITY_THRESHOLD: 익숙함 판단 기준 거리 (이 거리 이하면 유사하다고 판단)
        HIGH_FAMILIARITY_SCORE: 높은 익숙함으로 판단하는 점수 임계값
        MATCH_BONUS_FACTOR: 매치 개수에 따른 보너스 계수
    """
    
    # 익숙함 판단 기준 거리 (LanceDB Cosine Distance 기준)
    # 거리가 가까울수록(0에 수렴) 유사함
    FAMILIARITY_THRESHOLD = 0.3
    
    # 높은 익숙함으로 판단하는 점수 임계값
    HIGH_FAMILIARITY_SCORE = 0.7
    
    # 매치 개수에 따른 보너스 계수 (최대 20% 보너스)
    MATCH_BONUS_FACTOR = 0.05
    MAX_MATCH_BONUS = 0.2
    
    def __init__(self):
        """PatternRecognizer 초기화"""
        self._cache: Dict[str, PatternMetrics] = {}
        self._cache_hits = 0
        self._total_queries = 0
    
    def calculate_familiarity(
        self, 
        nexus: "Nexus", 
        context_text: str,
        limit: int = 5,
        use_cache: bool = True
    ) -> PatternMetrics:
        """
        현재 컨텍스트의 익숙함을 계산한다.
        
        Args:
            nexus: Nexus 엔진 인스턴스 (기억 검색용)
            context_text: 분석할 현재 상황 텍스트
            limit: 검색할 유사 기억 수
            use_cache: 캐시 사용 여부 (동일 컨텍스트 재계산 방지)
            
        Returns:
            PatternMetrics 객체 (익숙함/놀람 점수 포함)
        """
        self._total_queries += 1
        
        # 빈 컨텍스트 처리
        if not context_text or not context_text.strip():
            return self._create_novel_metrics()
        
        # 캐시 확인 (짧은 텍스트의 해시 키 사용)
        cache_key = self._compute_cache_key(context_text)
        if use_cache and cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        # Nexus가 검색 기능(RetrievalMixin)을 지원하는지 확인
        if not hasattr(nexus, "retrieve_relevant_memories"):
            return self._create_novel_metrics()
        
        # 관련 기억 검색 (의미론적 검색)
        try:
            memories = nexus.retrieve_relevant_memories(
                query=context_text,
                limit=limit
            )
        except Exception as e:
            print(f"⚠️ PatternRecognizer: 기억 검색 실패 - {e}")
            return self._create_novel_metrics()
        
        # 검색 결과가 없으면 완전히 새로운 상황
        if not memories:
            metrics = self._create_novel_metrics()
            if use_cache:
                self._cache[cache_key] = metrics
            return metrics
        
        # 거리 기반 점수 계산
        metrics = self._compute_metrics_from_memories(memories)
        
        # 캐시 저장
        if use_cache:
            self._cache[cache_key] = metrics
            self._prune_cache_if_needed()
        
        return metrics
    
    def _compute_metrics_from_memories(
        self, 
        memories: List[Dict[str, Any]]
    ) -> PatternMetrics:
        """
        검색된 기억들로부터 익숙함 지표를 계산한다.
        
        Args:
            memories: 검색된 기억 목록 (distance 필드 포함)
            
        Returns:
            계산된 PatternMetrics
        """
        # 가장 가까운 기억 추출
        nearest_memory = memories[0]
        nearest_dist = nearest_memory.get("distance", 1.0)
        
        # 거리 정규화 및 점수 변환
        # distance가 0이면 점수 1, distance가 1 이상이면 점수 0
        # Cosine distance는 보통 0~2 범위이므로 0.5로 나눠 0~1로 정규화
        normalized_dist = min(nearest_dist / 0.5, 1.0)
        raw_score = max(0.0, 1.0 - normalized_dist)
        
        # 임계값 이내의 기억 개수 카운트 (패턴의 견고성 확인)
        match_count = sum(
            1 for m in memories 
            if m.get("distance", 1.0) <= self.FAMILIARITY_THRESHOLD
        )
        
        # 보정: 매치되는 기억이 많으면 신뢰도 상승
        familiarity = raw_score
        if match_count > 1:
            bonus = min(match_count * self.MATCH_BONUS_FACTOR, self.MAX_MATCH_BONUS)
            familiarity = min(1.0, familiarity * (1.0 + bonus))
        
        # 가장 유사한 기억의 텍스트 추출
        top_text = nearest_memory.get("text", "")
        
        return PatternMetrics(
            familiarity_score=familiarity,
            surprise_score=1.0 - familiarity,
            nearest_distance=nearest_dist,
            match_count=match_count,
            top_memory_id=nearest_memory.get("id"),
            top_memory_text=top_text
        )
    
    def _create_novel_metrics(self) -> PatternMetrics:
        """완전히 새로운 상황(Novelty)에 대한 기본 메트릭 생성"""
        return PatternMetrics(
            familiarity_score=0.0,
            surprise_score=1.0,
            nearest_distance=1.0,
            match_count=0,
            top_memory_id=None,
            top_memory_text=None
        )
    
    def _compute_cache_key(self, text: str) -> str:
        """텍스트의 캐시 키 생성 (해시 기반)"""
        import hashlib
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    
    def _prune_cache_if_needed(self, max_size: int = 100):
        """캐시 크기 제한 (오래된 항목 제거)"""
        if len(self._cache) > max_size:
            # 간단한 FIFO 방식: 절반 제거
            keys_to_remove = list(self._cache.keys())[:max_size // 2]
            for key in keys_to_remove:
                del self._cache[key]
    
    def is_novel_situation(
        self, 
        metrics: PatternMetrics, 
        threshold: float = 0.6
    ) -> bool:
        """
        새로운 상황(Novelty)인지 판단
        
        Args:
            metrics: PatternMetrics 객체
            threshold: 익숙함 임계값 (이 값 미만이면 새로운 상황)
            
        Returns:
            True면 새로운 상황, False면 익숙한 상황
        """
        return metrics.familiarity_score < threshold
    
    def should_use_intuition(
        self, 
        metrics: PatternMetrics,
        confidence_threshold: float = 0.75
    ) -> bool:
        """
        직관(System 1)을 사용해야 하는지 판단
        
        높은 익숙함 + 충분한 매치 개수일 때 직관 사용 권장
        
        Args:
            metrics: PatternMetrics 객체
            confidence_threshold: 직관 사용 임계값
            
        Returns:
            True면 직관 사용 권장, False면 추론(System 2) 사용 권장
        """
        # 익숙함이 높고 매치가 2개 이상이면 직관 사용
        return (
            metrics.familiarity_score >= confidence_threshold 
            and metrics.match_count >= 2
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """패턴 인식기 통계 반환"""
        return {
            "total_queries": self._total_queries,
            "cache_hits": self._cache_hits,
            "cache_size": len(self._cache),
            "cache_hit_rate": (
                round(self._cache_hits / max(self._total_queries, 1) * 100, 2)
            )
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        print("🧹 PatternRecognizer 캐시 초기화됨")


# 싱글톤 인스턴스 (선택적 사용)
_pattern_recognizer_instance: Optional[PatternRecognizer] = None


def get_pattern_recognizer() -> PatternRecognizer:
    """PatternRecognizer 싱글톤 인스턴스 반환"""
    global _pattern_recognizer_instance
    if _pattern_recognizer_instance is None:
        _pattern_recognizer_instance = PatternRecognizer()
    return _pattern_recognizer_instance