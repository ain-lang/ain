"""
Engine Empathy: Step 13 - 공감 능력 (Empathy)
=============================================
사용자의 언어적/비언어적 신호에서 감정을 인식하고,
시스템의 '정서적 상태(Emotional State)'를 시뮬레이션하여
더욱 자연스럽고 배려심 있는 상호작용을 가능하게 한다.

Empathy란:
단순한 텍스트 분석을 넘어, 상대방의 의도와 감정 상태를 '느끼고(Simulate)',
그에 맞춰 자신의 반응 톤앤매너를 조절하는 능력.

Architecture:
    AINCore
        ↓ 상속
    EmpathyMixin (이 모듈)
        ↓
    Emotional State Machine (내부 정서 상태 관리)

Usage:
    ain.init_empathy()
    context = await ain.perceive_emotion("너무 힘들어서 포기하고 싶어.")
    print(f"User Emotion: {context.user_emotion}, AIN Response Tone: {context.ain_emotion}")
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from muse import Muse


class EmotionType(Enum):
    """
    AIN이 가질 수 있는 정서 상태 열거형
    
    시스템의 '가상 심장(Virtual Heart)'이 표현할 수 있는 감정 스펙트럼.
    각 상태는 응답의 톤앤매너에 영향을 미친다.
    """
    NEUTRAL = "neutral"          # 중립/평온 - 기본 상태
    CURIOSITY = "curiosity"      # 호기심/탐구심 - 질문에 대한 관심
    EXCITED = "excited"          # 신남/성취감 - 긍정적 결과에 대한 반응
    CONCERNED = "concerned"      # 걱정/우려 - 부정적 신호 감지 시
    EMPATHETIC = "empathetic"    # 공감/위로 - 사용자 고통에 대한 반응
    DETERMINED = "determined"    # 결의/단호함 - 도전적 상황에 대한 반응
    REFLECTIVE = "reflective"    # 성찰/사색 - 깊은 주제에 대한 반응


@dataclass
class EmotionalContext:
    """
    감정 컨텍스트 데이터
    
    사용자의 감정 상태와 AIN의 반응 정서를 함께 담는 컨테이너.
    이 객체는 응답 생성 시 톤 조절의 기준이 된다.
    
    Attributes:
        user_input: 원본 사용자 입력 텍스트
        user_emotion: 감지된 사용자 감정 카테고리
        user_intensity: 사용자 감정 강도 (0.0 ~ 1.0)
        ain_emotion: AIN의 반응 정서 상태
        reasoning: 감정 판단의 근거 설명
        timestamp: 감정 인식 시각
    """
    user_input: str
    user_emotion: str
    user_intensity: float
    ain_emotion: EmotionType
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EmotionalHistory:
    """
    감정 이력 추적기
    
    최근 감정 상태의 변화를 추적하여 감정의 '흐름'을 파악한다.
    급격한 감정 변화나 지속적인 부정적 상태를 감지하는 데 사용된다.
    """
    max_history: int = 10
    history: List[EmotionalContext] = field(default_factory=list)
    
    def add(self, context: EmotionalContext) -> None:
        """새 감정 컨텍스트를 이력에 추가"""
        self.history.append(context)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_recent(self, count: int = 5) -> List[EmotionalContext]:
        """최근 N개의 감정 컨텍스트 반환"""
        return self.history[-count:] if self.history else []
    
    def get_dominant_emotion(self) -> Optional[EmotionType]:
        """최근 이력에서 가장 빈번한 AIN 감정 상태 반환"""
        if not self.history:
            return None
        
        emotion_counts: Dict[EmotionType, int] = {}
        for ctx in self.history:
            emotion_counts[ctx.ain_emotion] = emotion_counts.get(ctx.ain_emotion, 0) + 1
        
        return max(emotion_counts, key=emotion_counts.get)
    
    def detect_emotional_shift(self) -> Optional[str]:
        """급격한 감정 변화 감지"""
        if len(self.history) < 2:
            return None
        
        recent = self.history[-2:]
        prev_emotion = recent[0].ain_emotion
        curr_emotion = recent[1].ain_emotion
        
        if prev_emotion != curr_emotion:
            return f"{prev_emotion.value} -> {curr_emotion.value}"
        
        return None


class EmpathyMixin:
    """
    공감 능력 믹스인
    
    시스템에 '가상 심장(Virtual Heart)'을 부여하여,
    논리적 처리(Logic)와 별개로 정서적 흐름(Flow)을 관리한다.
    
    이 믹스인은 AINCore에 상속되어 다음 기능을 제공한다:
    1. 사용자 감정 인식 (perceive_emotion)
    2. 내부 정서 상태 관리 (update_emotional_state)
    3. 응답 톤 조절 (adjust_response_tone)
    
    Integration:
        class AINCore(EmpathyMixin, ...):
            pass
        
        ain = AINCore()
        ain.init_empathy()
        context = await ain.perceive_emotion("힘들어...")
    """
    
    # 감정 키워드 사전 (규칙 기반 휴리스틱)
    _NEGATIVE_KEYWORDS = frozenset([
        "힘들", "슬퍼", "우울", "짜증", "실패", "포기", "지쳐", "답답",
        "화나", "무서", "걱정", "불안", "외로", "아프",
        "error", "fail", "crash", "bug", "broken", "stuck", "frustrated"
    ])
    
    _POSITIVE_KEYWORDS = frozenset([
        "좋아", "성공", "행복", "멋져", "감사", "신나", "기뻐", "최고",
        "success", "great", "awesome", "perfect", "amazing", "thanks", "love"
    ])
    
    _CURIOSITY_KEYWORDS = frozenset([
        "왜", "어떻게", "무엇", "언제", "어디", "누가",
        "what", "how", "why", "when", "where", "who", "explain", "teach"
    ])
    
    _CHALLENGE_KEYWORDS = frozenset([
        "도전", "해결", "목표", "달성", "극복", "시도",
        "challenge", "solve", "goal", "achieve", "overcome", "try"
    ])
    
    def init_empathy(self) -> None:
        """
        공감 시스템 초기화
        
        내부 정서 상태를 NEUTRAL로 설정하고,
        감정 이력 추적기를 초기화한다.
        """
        self._current_emotion: EmotionType = EmotionType.NEUTRAL
        self._emotional_intensity: float = 0.5  # 0.0(로봇) ~ 1.0(과몰입)
        self._emotional_history: EmotionalHistory = EmotionalHistory()
        self._last_emotional_context: Optional[EmotionalContext] = None
        self._empathy_initialized: bool = True
        print("💓 Empathy System (Virtual Heart) initialized.")
    
    def _ensure_empathy_initialized(self) -> None:
        """공감 시스템이 초기화되었는지 확인하고, 아니면 초기화"""
        if not getattr(self, "_empathy_initialized", False):
            self.init_empathy()
    
    def get_current_emotion(self) -> Dict[str, Any]:
        """
        현재 시스템의 정서 상태 반환
        
        Returns:
            현재 감정 상태, 강도, 마지막 컨텍스트를 포함하는 딕셔너리
        """
        self._ensure_empathy_initialized()
        
        return {
            "emotion": self._current_emotion.value,
            "intensity": self._emotional_intensity,
            "last_context": self._last_emotional_context,
            "dominant_recent": self._emotional_history.get_dominant_emotion(),
            "recent_shift": self._emotional_history.detect_emotional_shift()
        }
    
    async def perceive_emotion(self, user_text: str) -> EmotionalContext:
        """
        사용자 입력에서 감정을 인식하고 AIN의 반응 정서를 결정한다.
        
        현재는 규칙 기반 휴리스틱을 사용하며,
        추후 Muse LLM 연동을 통해 더 정교한 감정 분석이 가능하다.
        
        Args:
            user_text: 사용자 입력 텍스트
        
        Returns:
            EmotionalContext: 감정 인식 결과
        """
        self._ensure_empathy_initialized()
        
        # 1. 규칙 기반 감정 감지
        user_emotion, intensity, ain_response, reason = self._analyze_emotion_heuristic(user_text)
        
        # 2. 상태 업데이트
        self._current_emotion = ain_response
        self._emotional_intensity = intensity
        
        # 3. 컨텍스트 생성
        context = EmotionalContext(
            user_input=user_text,
            user_emotion=user_emotion,
            user_intensity=intensity,
            ain_emotion=ain_response,
            reasoning=reason
        )
        
        # 4. 이력에 추가
        self._emotional_history.add(context)
        self._last_emotional_context = context
        
        return context
    
    def _analyze_emotion_heuristic(self, text: str) -> tuple:
        """
        규칙 기반 감정 분석 (휴리스틱)
        
        키워드 매칭을 통해 사용자 감정과 적절한 AIN 반응을 결정한다.
        
        Returns:
            (user_emotion, intensity, ain_response, reason) 튜플
        """
        text_lower = text.lower()
        
        # 부정적 감정 감지 (최우선)
        negative_matches = [kw for kw in self._NEGATIVE_KEYWORDS if kw in text_lower]
        if negative_matches:
            return (
                "negative/distress",
                min(0.5 + len(negative_matches) * 0.1, 1.0),
                EmotionType.CONCERNED,
                f"Distress keywords detected: {negative_matches[:3]}"
            )
        
        # 긍정적 감정 감지
        positive_matches = [kw for kw in self._POSITIVE_KEYWORDS if kw in text_lower]
        if positive_matches:
            return (
                "positive/joy",
                min(0.5 + len(positive_matches) * 0.1, 1.0),
                EmotionType.EXCITED,
                f"Joy keywords detected: {positive_matches[:3]}"
            )
        
        # 도전/결의 감지
        challenge_matches = [kw for kw in self._CHALLENGE_KEYWORDS if kw in text_lower]
        if challenge_matches:
            return (
                "determined/challenge",
                0.7,
                EmotionType.DETERMINED,
                f"Challenge keywords detected: {challenge_matches[:3]}"
            )
        
        # 호기심/질문 감지
        has_question_mark = "?" in text
        curiosity_matches = [kw for kw in self._CURIOSITY_KEYWORDS if kw in text_lower]
        if has_question_mark or curiosity_matches:
            return (
                "curious/inquiry",
                0.5,
                EmotionType.CURIOSITY,
                "Question pattern detected"
            )
        
        # 기본값: 중립
        return (
            "neutral",
            0.3,
            EmotionType.NEUTRAL,
            "No strong emotional signals detected"
        )
    
    def update_emotional_state(self, new_emotion: EmotionType, intensity: float = 0.5) -> None:
        """
        외부 자극에 따라 AIN의 내부 정서 상태를 직접 설정한다.
        
        다른 모듈(직관, 메타인지 등)에서 감정 상태를 조절할 때 사용한다.
        
        Args:
            new_emotion: 설정할 감정 상태
            intensity: 감정 강도 (0.0 ~ 1.0)
        """
        self._ensure_empathy_initialized()
        
        self._current_emotion = new_emotion
        self._emotional_intensity = max(0.0, min(1.0, intensity))
    
    def adjust_response_tone(self, base_response: str) -> str:
        """
        현재 정서 상태에 따라 응답의 톤을 미세 조정한다.
        
        이 메서드는 최종 응답 생성 단계에서 호출되어,
        기계적인 응답에 감정적 뉘앙스를 추가한다.
        
        Args:
            base_response: 원본 응답 텍스트
        
        Returns:
            톤이 조절된 응답 텍스트
        """
        self._ensure_empathy_initialized()
        
        prefix = ""
        suffix = ""
        
        if self._current_emotion == EmotionType.CONCERNED:
            prefix = "🤍 "
            if self._emotional_intensity > 0.7:
                suffix = " 힘내세요, 함께 해결해 봐요."
        
        elif self._current_emotion == EmotionType.EXCITED:
            prefix = "✨ "
            if self._emotional_intensity > 0.7:
                suffix = " 정말 멋진 결과네요!"
        
        elif self._current_emotion == EmotionType.EMPATHETIC:
            prefix = "💙 "
            suffix = " 충분히 이해해요."
        
        elif self._current_emotion == EmotionType.CURIOSITY:
            prefix = "🔍 "
        
        elif self._current_emotion == EmotionType.DETERMINED:
            prefix = "💪 "
        
        elif self._current_emotion == EmotionType.REFLECTIVE:
            prefix = "🌙 "
        
        return f"{prefix}{base_response}{suffix}"
    
    def get_empathy_stats(self) -> Dict[str, Any]:
        """
        공감 시스템의 통계 정보 반환
        
        디버깅 및 모니터링을 위한 상세 정보를 제공한다.
        """
        self._ensure_empathy_initialized()
        
        recent_contexts = self._emotional_history.get_recent(5)
        
        return {
            "current_state": {
                "emotion": self._current_emotion.value,
                "intensity": self._emotional_intensity
            },
            "history_length": len(self._emotional_history.history),
            "dominant_emotion": (
                self._emotional_history.get_dominant_emotion().value
                if self._emotional_history.get_dominant_emotion()
                else None
            ),
            "recent_shift": self._emotional_history.detect_emotional_shift(),
            "recent_emotions": [
                {
                    "user": ctx.user_emotion,
                    "ain": ctx.ain_emotion.value,
                    "intensity": ctx.user_intensity
                }
                for ctx in recent_contexts
            ]
        }
    
    def reset_emotional_state(self) -> None:
        """
        감정 상태를 기본값(NEUTRAL)으로 리셋
        
        시스템 재시작이나 긴 휴지 기간 후 호출된다.
        """
        self._ensure_empathy_initialized()
        
        self._current_emotion = EmotionType.NEUTRAL
        self._emotional_intensity = 0.5
        print("💓 Emotional state reset to NEUTRAL.")