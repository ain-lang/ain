"""
Engine Meta Explainer: 메타인지 상태 설명 모듈
Step 7: Meta-Cognition - Human-Readable State Explanation

이 모듈은 시스템의 내부 인지 상태(CognitiveState)와 전략 모드(StrategyMode)를
인간이 이해할 수 있는 자연어로 변환하여 메타인지의 투명성을 확보한다.

MetaMonitor가 '진단(Diagnosis)'을 수행한다면,
MetaExplainer는 그 진단 결과를 '설명(Explanation)'으로 변환한다.

Architecture:
    MetaMonitor (진단)
        ↓ CognitiveState
    MetaExplainer (이 모듈)
        ↓ 자연어 설명
    Telegram / Logs / UI (출력)

Usage:
    from engine.meta_explainer import MetaExplainer
    from engine.meta_monitor import CognitiveState, CognitiveHealthLevel
    from engine.strategy_adapter import StrategyMode
    
    explainer = MetaExplainer()
    state_explanation = explainer.explain_state(cognitive_state)
    strategy_explanation = explainer.explain_strategy(StrategyMode.ACCELERATED, "High momentum detected")
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    pass

try:
    from engine.meta_monitor import CognitiveState, CognitiveHealthLevel
    HAS_META_MONITOR = True
except ImportError:
    HAS_META_MONITOR = False
    CognitiveState = None
    CognitiveHealthLevel = None

try:
    from engine.strategy_adapter import StrategyMode
    HAS_STRATEGY_ADAPTER = True
except ImportError:
    HAS_STRATEGY_ADAPTER = False
    StrategyMode = None


class MetaExplainer:
    """
    메타인지 상태 설명기
    
    CognitiveState와 StrategyMode를 입력받아 인간이 이해할 수 있는
    자연어 설명을 생성한다. 템플릿 기반으로 빠르고 일관된 설명을 제공한다.
    
    Attributes:
        tone_modifiers: 건강 상태별 톤앤매너 수식어
        strategy_descriptions: 전략 모드별 설명 템플릿
    """
    
    def __init__(self):
        self._tone_modifiers = {
            "optimal": ("안정적이고 효율적인", "최적의 상태로"),
            "good": ("양호한", "원활하게"),
            "moderate": ("보통 수준의", "무난하게"),
            "degraded": ("저하된", "다소 어렵게"),
            "critical": ("위험 수준의", "긴급하게"),
        }
        
        self._strategy_descriptions = {
            "normal": "균형 잡힌 표준 운영 모드",
            "accelerated": "높은 성공률을 바탕으로 한 가속 모드",
            "critical": "시스템 안정화를 위한 긴급 복구 모드",
            "conservative": "신중한 접근을 위한 보수적 모드",
            "exploratory": "새로운 영역 탐색을 위한 실험 모드",
        }
        
        self._health_emojis = {
            "optimal": "💚",
            "good": "💙",
            "moderate": "💛",
            "degraded": "🧡",
            "critical": "❤️‍🔥",
        }
    
    def explain_state(self, state: "CognitiveState") -> str:
        """
        인지 상태 객체를 종합적인 상태 요약문으로 변환한다.
        
        Args:
            state: CognitiveState 객체 (MetaMonitor에서 생성)
        
        Returns:
            인간이 읽을 수 있는 상태 요약 문자열
        """
        if state is None:
            return "⚠️ 인지 상태 정보를 사용할 수 없습니다."
        
        if not HAS_META_MONITOR:
            return "⚠️ MetaMonitor 모듈이 로드되지 않았습니다."
        
        health_level = self._get_health_level_string(state)
        health_desc = self._describe_health(health_level)
        emoji = self._health_emojis.get(health_level, "🔵")
        
        lines = [
            f"{emoji} **AIN 인지 상태 보고서**",
            f"",
            f"**건강 상태**: {health_desc['adjective']} ({health_level})",
        ]
        
        if hasattr(state, 'confidence_score'):
            confidence_pct = int(state.confidence_score * 100)
            lines.append(f"**자신감 수준**: {confidence_pct}%")
        
        if hasattr(state, 'current_strategy') and state.current_strategy:
            strategy_name = self._get_strategy_name(state.current_strategy)
            lines.append(f"**현재 전략**: {strategy_name}")
        
        if hasattr(state, 'recent_success_rate'):
            success_pct = int(state.recent_success_rate * 100)
            lines.append(f"**최근 성공률**: {success_pct}%")
        
        if hasattr(state, 'focus_area') and state.focus_area:
            lines.append(f"**집중 영역**: {state.focus_area}")
        
        lines.append("")
        lines.append(f"📝 {health_desc['summary']}")
        
        return "\n".join(lines)
    
    def explain_strategy(self, mode: "StrategyMode", reasoning: str = "") -> str:
        """
        현재 전략 모드가 선택된 이유를 설명한다.
        
        Args:
            mode: StrategyMode 열거형 값
            reasoning: 전략 선택의 근거 (선택적)
        
        Returns:
            전략 설명 문자열
        """
        if mode is None:
            return "⚠️ 전략 모드 정보를 사용할 수 없습니다."
        
        mode_name = self._get_strategy_name(mode)
        mode_key = mode_name.lower() if isinstance(mode_name, str) else "normal"
        
        if hasattr(mode, 'value'):
            mode_key = mode.value
        
        description = self._strategy_descriptions.get(mode_key, "알 수 없는 전략 모드")
        
        lines = [
            f"🎯 **현재 전략: {mode_name}**",
            f"",
            f"📖 {description}",
        ]
        
        if reasoning:
            lines.append(f"")
            lines.append(f"💡 **선택 근거**: {reasoning}")
        
        return "\n".join(lines)
    
    def explain_transition(
        self, 
        from_mode: "StrategyMode", 
        to_mode: "StrategyMode", 
        trigger: str = ""
    ) -> str:
        """
        전략 모드 전환을 설명한다.
        
        Args:
            from_mode: 이전 전략 모드
            to_mode: 새로운 전략 모드
            trigger: 전환을 유발한 원인 (선택적)
        
        Returns:
            전환 설명 문자열
        """
        from_name = self._get_strategy_name(from_mode)
        to_name = self._get_strategy_name(to_mode)
        
        lines = [
            f"🔄 **전략 전환 발생**",
            f"",
            f"  {from_name} → {to_name}",
        ]
        
        if trigger:
            lines.append(f"")
            lines.append(f"⚡ **트리거**: {trigger}")
        
        to_key = to_mode.value if hasattr(to_mode, 'value') else "normal"
        to_desc = self._strategy_descriptions.get(to_key, "")
        
        if to_desc:
            lines.append(f"")
            lines.append(f"📝 새 전략: {to_desc}")
        
        return "\n".join(lines)
    
    def generate_brief_status(self, state: "CognitiveState") -> str:
        """
        짧은 한 줄 상태 요약을 생성한다 (로그/알림용).
        
        Args:
            state: CognitiveState 객체
        
        Returns:
            한 줄 요약 문자열
        """
        if state is None:
            return "상태 불명"
        
        health_level = self._get_health_level_string(state)
        emoji = self._health_emojis.get(health_level, "🔵")
        
        confidence = ""
        if hasattr(state, 'confidence_score'):
            confidence = f" | 자신감 {int(state.confidence_score * 100)}%"
        
        strategy = ""
        if hasattr(state, 'current_strategy') and state.current_strategy:
            strategy_name = self._get_strategy_name(state.current_strategy)
            strategy = f" | {strategy_name}"
        
        return f"{emoji} {health_level.upper()}{confidence}{strategy}"
    
    def _describe_health(self, level: str) -> Dict[str, str]:
        """
        건강 상태에 따른 톤앤매너 조정 헬퍼
        
        Args:
            level: 건강 수준 문자열 (optimal, good, moderate, degraded, critical)
        
        Returns:
            형용사와 요약문을 담은 딕셔너리
        """
        level_lower = level.lower() if isinstance(level, str) else "moderate"
        
        adjective, adverb = self._tone_modifiers.get(
            level_lower, 
            ("보통 수준의", "무난하게")
        )
        
        summaries = {
            "optimal": "시스템이 최적의 상태로 작동 중입니다. 모든 인지 기능이 원활합니다.",
            "good": "시스템이 양호한 상태입니다. 대부분의 작업을 효율적으로 처리할 수 있습니다.",
            "moderate": "시스템이 보통 수준으로 작동 중입니다. 일부 영역에서 개선이 필요할 수 있습니다.",
            "degraded": "시스템 성능이 저하되었습니다. 복잡한 작업에서 어려움이 예상됩니다.",
            "critical": "시스템이 위험 상태입니다. 즉각적인 안정화 조치가 필요합니다.",
        }
        
        return {
            "adjective": adjective,
            "adverb": adverb,
            "summary": summaries.get(level_lower, "상태를 평가할 수 없습니다."),
        }
    
    def _get_health_level_string(self, state: "CognitiveState") -> str:
        """CognitiveState에서 건강 수준 문자열을 추출한다."""
        if hasattr(state, 'health_level'):
            health = state.health_level
            if hasattr(health, 'value'):
                return health.value
            return str(health)
        return "moderate"
    
    def _get_strategy_name(self, mode) -> str:
        """StrategyMode에서 이름을 추출한다."""
        if mode is None:
            return "Normal"
        
        if hasattr(mode, 'value'):
            return mode.value.capitalize()
        
        if hasattr(mode, 'name'):
            return mode.name.capitalize()
        
        return str(mode).capitalize()


def get_meta_explainer() -> MetaExplainer:
    """MetaExplainer 싱글톤 인스턴스 반환"""
    if not hasattr(get_meta_explainer, "_instance"):
        get_meta_explainer._instance = MetaExplainer()
    return get_meta_explainer._instance