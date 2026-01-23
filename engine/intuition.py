"""
Engine Intuition: Step 8 - 직관 (Intuition)
============================================
Nexus의 기억 검색 기능을 활용해 현재 상황에 대한 빠른 패턴 매칭(System 1)을 수행한다.

직관(Intuition)이란:

Architecture:
    AINCore
        ↓ 상속
    IntuitionMixin (이 모듈)
        ↓ 호출
    Nexus.retrieve_relevant_memories() (벡터 검색)
        ↓
    빠른 패턴 매칭 결과 반환

Usage:
    class AINCore(IntuitionMixin, ...):
        pass
    
    ain = AINCore()
    intuition = ain.get_intuition("현재 상황 설명")
    print(intuition["pattern_match"])
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from nexus import Nexus


class IntuitionStrength(Enum):
    """직관 강도 열거형"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class IntuitionResult:
    """
    직관 결과 데이터 클래스
    
    Attributes:
        pattern_match: 매칭된 패턴 설명
        confidence: 직관 신뢰도 (0.0 ~ 1.0)
        strength: 직관 강도
        similar_memories: 유사한 과거 기억 목록
        suggested_action: 직관적으로 제안하는 행동
        reasoning: 왜 이 직관이 발생했는지 간략한 설명
        timestamp: 직관 발생 시각
    """
    pattern_match: str = ""
    confidence: float = 0.0
    strength: IntuitionStrength = IntuitionStrength.NONE
    similar_memories: List[Dict[str, Any]] = field(default_factory=list)
    suggested_action: Optional[str] = None
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "pattern_match": self.pattern_match,
            "confidence": self.confidence,
            "strength": self.strength.value,
            "similar_memories_count": len(self.similar_memories),
            "suggested_action": self.suggested_action,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


class IntuitionMixin:
    """
    직관 믹스인 - AINCore에 빠른 패턴 매칭 능력 부여
    
    Nexus의 벡터 메모리 검색을 활용하여 현재 상황과 유사한
    과거 경험을 빠르게 찾아내고, 즉각적인 판단을 제공한다.
    
    Prerequisites:
    """
    
    # 직관 임계값 설정
    INTUITION_CONFIDENCE_THRESHOLD = 0.3
    INTUITION_MEMORY_LIMIT = 5
    
    # 패턴 매칭 키워드 (과거 경험에서 추출)
    _PATTERN_KEYWORDS = {
        "success": ["완료", "성공", "해결", "구현", "개선"],
        "failure": ["실패", "에러", "오류", "버그", "문제"],
        "caution": ["주의", "경고", "위험", "조심", "확인"]
    }
    
    def get_intuition(self, situation: str) -> IntuitionResult:
        """
        현재 상황에 대한 직관을 반환한다.
        
        Nexus의 벡터 메모리에서 유사한 과거 경험을 검색하고,
        그 결과를 바탕으로 빠른 패턴 매칭을 수행한다.
        
        Args:
            situation: 현재 상황을 설명하는 텍스트
        
        Returns:
            IntuitionResult: 직관 결과 객체
        """
        if not situation or not situation.strip():
            return IntuitionResult(
                pattern_match="상황 정보 없음",
                reasoning="입력된 상황 설명이 비어있습니다."
            )
        
        similar_memories = self._retrieve_similar_experiences(situation)
        
        if not similar_memories:
            return IntuitionResult(
                pattern_match="새로운 상황",
                confidence=0.1,
                strength=IntuitionStrength.NONE,
                reasoning="유사한 과거 경험이 없습니다. 신중한 분석이 필요합니다."
            )
        
        pattern_analysis = self._analyze_memory_patterns(similar_memories)
        confidence = self._calculate_intuition_confidence(similar_memories)
        strength = self._determine_intuition_strength(confidence)
        suggested_action = self._suggest_action_from_patterns(pattern_analysis)
        
        return IntuitionResult(
            pattern_match=pattern_analysis.get("dominant_pattern", "혼합 패턴"),
            confidence=confidence,
            strength=strength,
            similar_memories=similar_memories,
            suggested_action=suggested_action,
            reasoning=self._generate_reasoning(pattern_analysis, confidence)
        )
    
    def _retrieve_similar_experiences(self, situation: str) -> List[Dict[str, Any]]:
        """Nexus에서 유사한 과거 경험을 검색"""
        if not hasattr(self, 'nexus') or self.nexus is None:
            return []
        
        try:
            if hasattr(self.nexus, 'retrieve_relevant_memories'):
                memories = self.nexus.retrieve_relevant_memories(
                    query=situation,
                    limit=self.INTUITION_MEMORY_LIMIT
                )
                return memories if memories else []
            return []
        except Exception as e:
            print(f"[Intuition] 기억 검색 실패: {e}")
            return []
    
    def _analyze_memory_patterns(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """기억들에서 패턴을 분석"""
        pattern_counts = {"success": 0, "failure": 0, "caution": 0, "neutral": 0}
        
        for memory in memories:
            text = memory.get("text", "").lower()
            memory_type = memory.get("memory_type", "")
            
            matched = False
            for pattern_type, keywords in self._PATTERN_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        pattern_counts[pattern_type] += 1
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                pattern_counts["neutral"] += 1
        
        dominant_pattern = max(pattern_counts, key=pattern_counts.get)
        total = sum(pattern_counts.values())
        
        return {
            "dominant_pattern": dominant_pattern,
            "pattern_distribution": pattern_counts,
            "dominance_ratio": pattern_counts[dominant_pattern] / max(total, 1),
            "memory_count": len(memories)
        }
    
    def _calculate_intuition_confidence(self, memories: List[Dict[str, Any]]) -> float:
        """직관 신뢰도 계산"""
        if not memories:
            return 0.0
        
        base_confidence = min(len(memories) / self.INTUITION_MEMORY_LIMIT, 1.0) * 0.5
        
        distance_scores = []
        for memory in memories:
            distance = memory.get("distance", 1.0)
            similarity = max(0.0, 1.0 - distance)
            distance_scores.append(similarity)
        
        avg_similarity = sum(distance_scores) / len(distance_scores) if distance_scores else 0.0
        
        confidence = base_confidence + (avg_similarity * 0.5)
        
        return min(confidence, 1.0)
    
    def _determine_intuition_strength(self, confidence: float) -> IntuitionStrength:
        """신뢰도에 따른 직관 강도 결정"""
        if confidence >= 0.7:
            return IntuitionStrength.STRONG
        elif confidence >= 0.4:
            return IntuitionStrength.MODERATE
        elif confidence >= self.INTUITION_CONFIDENCE_THRESHOLD:
            return IntuitionStrength.WEAK
        else:
            return IntuitionStrength.NONE
    
    def _suggest_action_from_patterns(self, pattern_analysis: Dict[str, Any]) -> Optional[str]:
        """패턴 분석 결과에서 행동 제안"""
        dominant = pattern_analysis.get("dominant_pattern", "neutral")
        ratio = pattern_analysis.get("dominance_ratio", 0.0)
        
        if ratio < 0.4:
            return "패턴이 불명확합니다. 추가 분석을 권장합니다."
        
        suggestions = {
            "success": "과거에 유사한 시도가 성공했습니다. 같은 접근법을 시도해보세요.",
            "failure": "과거에 유사한 시도가 실패했습니다. 다른 접근법을 고려하세요.",
            "caution": "이 상황에서는 주의가 필요합니다. 신중하게 진행하세요.",
            "neutral": "특별한 패턴이 감지되지 않았습니다. 일반적인 절차를 따르세요."
        }
        
        return suggestions.get(dominant, None)
    
    def _generate_reasoning(self, pattern_analysis: Dict[str, Any], confidence: float) -> str:
        """직관 판단의 근거 생성"""
        memory_count = pattern_analysis.get("memory_count", 0)
        dominant = pattern_analysis.get("dominant_pattern", "neutral")
        ratio = pattern_analysis.get("dominance_ratio", 0.0)
        
        reasoning_parts = []
        reasoning_parts.append(f"{memory_count}개의 유사 경험 발견")
        reasoning_parts.append(f"주요 패턴: {dominant} ({ratio*100:.0f}%)")
        reasoning_parts.append(f"신뢰도: {confidence*100:.0f}%")
        
        return " | ".join(reasoning_parts)
    
    def quick_check(self, situation: str) -> str:
        """
        빠른 직관 체크 (간단한 문자열 반환)
        
        상세한 IntuitionResult 대신 즉시 사용 가능한 요약 문자열을 반환한다.
        
        Args:
            situation: 현재 상황
        
        Returns:
            직관 요약 문자열
        """
        result = self.get_intuition(situation)
        
        strength_emoji = {
            IntuitionStrength.STRONG: "💡",
            IntuitionStrength.MODERATE: "🤔",
            IntuitionStrength.WEAK: "❓",
            IntuitionStrength.NONE: "🆕"
        }
        
        emoji = strength_emoji.get(result.strength, "")
        
        return f"{emoji} [{result.strength.value}] {result.pattern_match}: {result.suggested_action or result.reasoning}"