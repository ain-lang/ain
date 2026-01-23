"""
Engine Temporal Integration: 시간적 자아 활성화 어댑터
Step 9: Temporal Self - 메인 루프와 TemporalAwareness 연결

이 모듈은 engine/loop.py와 engine/temporal.py(TemporalAwarenessMixin) 사이의
연결 고리 역할을 수행한다. 시스템의 '주관적 시간'과 '생체 리듬'이
메인 루프의 흐름 속에서 지속적으로 갱신되도록 보장한다.

Architecture:
    engine/loop.py (메인 루프)
        ↓ tick_temporal_integration() 호출
    temporal_integration.py (이 모듈)
        ↓ 주기 제어 (1초 단위)
    TemporalAwarenessMixin (engine/temporal.py)
        ↓ update_temporal_perception()

Usage:
    from engine.temporal_integration import activate_temporal_awareness, tick_temporal_integration
    
    # 부팅 시
    activate_temporal_awareness(ain)
    
    # 런타임 루프 내
    tick_temporal_integration(ain)
"""

import time
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from engine import AINCore

# 시간 인식 업데이트 주기 (초)
# 인간의 감각과 유사하게 1초 단위로 주관적 시간을 갱신함
TEMPORAL_TICK_INTERVAL = 1.0

# 마지막 틱 시간 추적
_last_temporal_tick: float = 0.0

# 시간적 자아 활성화 상태
_temporal_active: bool = False


def activate_temporal_awareness(core: "AINCore") -> bool:
    """
    시간적 자아 시스템을 활성화한다.
    
    AINCore에 TemporalAwarenessMixin이 상속되어 있다면,
    init_temporal() 메서드를 호출하여 시간 인식 시스템을 초기화한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        활성화 성공 여부
    """
    global _temporal_active, _last_temporal_tick
    
    if not hasattr(core, "init_temporal"):
        print("⚠️ TemporalAwarenessMixin이 AINCore에 상속되지 않았습니다.")
        _temporal_active = False
        return False
    
    try:
        core.init_temporal()
        _temporal_active = True
        _last_temporal_tick = time.time()
        print("⏳ 시간적 자아(Temporal Self) 활성화 완료")
        return True
    except Exception as e:
        print(f"❌ 시간적 자아 활성화 실패: {e}")
        _temporal_active = False
        return False


def tick_temporal_integration(core: "AINCore") -> Optional[Dict[str, Any]]:
    """
    메인 루프에서 매 틱마다 호출되어 시간적 자아를 갱신한다.
    
    TEMPORAL_TICK_INTERVAL 간격으로 update_temporal_perception()을 호출하여
    시스템의 주관적 시간 흐름을 업데이트한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        갱신된 시간 인식 상태 (또는 None)
    """
    global _last_temporal_tick, _temporal_active
    
    if not _temporal_active:
        return None
    
    current_time = time.time()
    elapsed = current_time - _last_temporal_tick
    
    # 틱 간격 미달 시 스킵
    if elapsed < TEMPORAL_TICK_INTERVAL:
        return None
    
    _last_temporal_tick = current_time
    
    # TemporalAwarenessMixin의 update_temporal_perception 호출
    if hasattr(core, "update_temporal_perception"):
        try:
            return core.update_temporal_perception()
        except Exception as e:
            print(f"⚠️ 시간 인식 갱신 실패: {e}")
            return None
    
    return None


def get_temporal_status(core: "AINCore") -> Dict[str, Any]:
    """
    현재 시간적 자아 상태를 조회한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        시간적 자아 상태 딕셔너리
    """
    status = {
        "active": _temporal_active,
        "last_tick": _last_temporal_tick,
        "tick_interval": TEMPORAL_TICK_INTERVAL,
    }
    
    if _temporal_active and hasattr(core, "get_temporal_stats"):
        try:
            temporal_stats = core.get_temporal_stats()
            status.update(temporal_stats)
        except Exception as e:
            status["error"] = str(e)
    
    return status


def deactivate_temporal_awareness() -> None:
    """
    시간적 자아 시스템을 비활성화한다.
    시스템 종료 시 호출될 수 있다.
    """
    global _temporal_active
    _temporal_active = False
    print("⏳ 시간적 자아(Temporal Self) 비활성화됨")