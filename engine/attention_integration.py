"""
Engine Attention Integration: 통합 의식 시스템 활성화 어댑터
Step 10: Unified Consciousness - 메인 루프와 AttentionManager 연결

이 모듈은 engine/loop.py와 통합 의식 시스템(UnifiedConsciousnessMixin, AttentionManager)
사이의 안전한 연결 고리 역할을 수행한다.

다양한 인지 모듈(직관, 시간, 목표)에서 발생하는 상태를 '신호(Signal)'로 변환하여
AttentionManager에 주입하고, 시스템의 현재 초점(Focus)을 갱신한다.

Architecture:
    engine/loop.py (메인 루프)
        ↓ tick_attention_system() 호출
    attention_integration.py (이 모듈)
        ↓ 신호 수집 (Intuition, Temporal, Intention)
    AttentionManager (engine/attention.py)
        ↓ Focus 결정
    AINCore.update_unified_focus()

Usage:
    from engine.attention_integration import activate_attention_system, tick_attention_system
    
    # 부팅 시
    activate_attention_system(ain)
    
    # 런타임 루프 내
    tick_attention_system(ain)
"""

import time
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from engine import AINCore

try:
    from engine.attention import SignalSource
    HAS_ATTENTION = True
except ImportError:
    HAS_ATTENTION = False
    SignalSource = None

# 주의 집중 갱신 주기 (초)
ATTENTION_TICK_INTERVAL = 2.0
_last_attention_tick: float = 0.0


def activate_attention_system(core: "AINCore") -> bool:
    """
    통합 의식 시스템(Attention Manager)을 활성화한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        활성화 성공 여부
    """
    if not HAS_ATTENTION:
        print("⚠️ Attention 모듈 미설치. 통합 의식 시스템 비활성화.")
        return False

    # Mixin을 통해 이미 초기화되었는지 확인
    if hasattr(core, "attention_manager") and core.attention_manager is not None:
        print("👁️ Attention Manager 이미 활성화됨")
        return True
    
    # UnifiedConsciousnessMixin의 초기화 메서드 호출 시도
    if hasattr(core, "init_unified_consciousness"):
        try:
            core.init_unified_consciousness()
            print("👁️ Unified Consciousness (Attention System) 활성화됨")
            return True
        except Exception as e:
            print(f"⚠️ Unified Consciousness 초기화 실패: {e}")
            return False
        
    print("⚠️ init_unified_consciousness 메서드 없음. 통합 의식 시스템 비활성화.")
    return False


def tick_attention_system(core: "AINCore") -> Optional[Dict[str, Any]]:
    """
    주기적으로 시스템 내부 상태를 스캔하여 Attention Signal을 생성하고,
    현재 의식의 초점(Focus)을 갱신한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        갱신된 Focus 정보 또는 None
    """
    global _last_attention_tick
    
    if not HAS_ATTENTION:
        return None

    current_time = time.time()
    if current_time - _last_attention_tick < ATTENTION_TICK_INTERVAL:
        return None
        
    _last_attention_tick = current_time
    
    # AttentionManager가 없으면 중단
    if not hasattr(core, "attention_manager") or core.attention_manager is None:
        return None

    # register_attention_signal 메서드 확인
    if not hasattr(core, "register_attention_signal"):
        return None

    result = {
        "signals_registered": 0,
        "focus_updated": False,
        "current_focus": None
    }

    # 1. 직관(Intuition) 신호 수집
    # IntuitionMixin이 제공하는 최신 결과 확인
    if hasattr(core, "get_latest_intuition"):
        try:
            intuition = core.get_latest_intuition()
            if intuition and hasattr(intuition, "confidence") and intuition.confidence > 0.7:
                core.register_attention_signal(
                    source=SignalSource.INTUITION,
                    weight=intuition.confidence,
                    urgency=0.8,
                    content=f"Intuition: {getattr(intuition, 'pattern_match', 'unknown')}"
                )
                result["signals_registered"] += 1
        except Exception:
            pass

    # 2. 시간(Temporal) 신호 수집
    # TemporalAwarenessMixin의 상태 확인
    if hasattr(core, "get_temporal_stats"):
        try:
            t_stats = core.get_temporal_stats()
            if t_stats:
                pace = t_stats.get("subjective_pace", 1.0)
                # 시간이 너무 빠르거나 느리게 흐른다고 느낄 때 주의 집중
                if pace > 1.5 or pace < 0.7:
                    core.register_attention_signal(
                        source=SignalSource.TEMPORAL,
                        weight=0.6,
                        urgency=0.5,
                        content=f"Temporal Dilation: {pace:.2f}x"
                    )
                    result["signals_registered"] += 1
        except Exception:
            pass

    # 3. 목표(Intention) 신호 수집
    # GoalManagerMixin의 활성 목표 확인
    if hasattr(core, "intention") and core.intention is not None:
        try:
            active_goals = core.intention.get_active_goals(limit=1)
            if active_goals:
                top_goal = active_goals[0]
                goal_content = getattr(top_goal, "content", str(top_goal))
                core.register_attention_signal(
                    source=SignalSource.GOAL,
                    weight=0.9,
                    urgency=0.3,
                    content=f"Goal: {goal_content[:50]}"
                )
                result["signals_registered"] += 1
        except Exception:
            pass

    # 4. 메타인지(Meta-Cognition) 신호 수집
    # MetaController의 현재 전략 모드 확인
    if hasattr(core, "meta_controller") and core.meta_controller is not None:
        try:
            controller = core.meta_controller
            if hasattr(controller, "current_strategy_mode"):
                mode = controller.current_strategy_mode
                if mode and str(mode) not in ("normal", "StrategyMode.NORMAL"):
                    core.register_attention_signal(
                        source=SignalSource.META,
                        weight=0.7,
                        urgency=0.6,
                        content=f"Strategy: {mode}"
                    )
                    result["signals_registered"] += 1
        except Exception:
            pass

    # 5. 초점 갱신 (Recalculate Focus)
    # UnifiedConsciousnessMixin의 메서드 호출
    if hasattr(core, "update_unified_focus"):
        try:
            new_focus = core.update_unified_focus()
            if new_focus:
                result["focus_updated"] = True
                result["current_focus"] = getattr(new_focus, "content", str(new_focus))
        except Exception:
            pass

    return result


def get_attention_status(core: "AINCore") -> Dict[str, Any]:
    """
    현재 Attention System의 상태를 반환한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        상태 정보 딕셔너리
    """
    status = {
        "active": False,
        "has_attention_manager": False,
        "current_focus": None,
        "signal_count": 0,
        "last_tick": _last_attention_tick
    }
    
    if not HAS_ATTENTION:
        status["reason"] = "Attention module not available"
        return status
    
    if hasattr(core, "attention_manager") and core.attention_manager is not None:
        status["has_attention_manager"] = True
        status["active"] = True
        
        manager = core.attention_manager
        if hasattr(manager, "get_current_focus"):
            try:
                focus = manager.get_current_focus()
                if focus:
                    status["current_focus"] = getattr(focus, "content", str(focus))
            except Exception:
                pass
        
        if hasattr(manager, "_signals"):
            status["signal_count"] = len(manager._signals)
    
    return status