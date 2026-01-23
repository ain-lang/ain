"""
Engine Loop Strategy: 메타인지 전략을 런타임 루프에 반영하는 매니저
Step 7: Meta-Cognition - StrategyMode를 실제 시스템 동작에 연결

이 모듈은 StrategyAdapter의 StrategyMode(Normal, Accelerated, Critical 등)를
읽어와 AINCore의 current_interval과 burst_mode를 동적으로 조정한다.

메타인지 시스템이 판단한 '전략'이 실제 시스템의 '심장박동(Loop Interval)'에
즉각적인 영향을 미치도록 연결하는 핵심 컴포넌트이다.

Architecture:
    MetaController (메타인지 사이클 실행)
        ↓ StrategyMode 결정
    LoopStrategyManager (이 모듈)
        ↓ 파라미터 변환
    AINCore.current_interval, burst_mode (실제 적용)

Usage:
    from engine.loop_strategy import LoopStrategyManager, get_loop_strategy_manager
    
    manager = get_loop_strategy_manager()
    manager.apply_to_core(ain_core)
    interval = manager.get_recommended_interval()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from engine import AINCore

try:
    from engine.strategy_adapter import StrategyAdapter, StrategyMode
    HAS_STRATEGY_ADAPTER = True
except ImportError:
    HAS_STRATEGY_ADAPTER = False
    
    class StrategyMode(Enum):
        NORMAL = "normal"
        ACCELERATED = "accelerated"
        CONSERVATIVE = "conservative"
        CRITICAL = "critical"
        RECOVERY = "recovery"


@dataclass
class LoopParameters:
    """
    루프 파라미터 데이터 클래스
    
    Attributes:
        interval: 진화 주기 (초)
        burst_mode: 버스트 모드 활성화 여부
        burst_duration: 버스트 모드 지속 시간 (초)
        consciousness_interval: 의식 루프 주기 (초)
        meta_cognition_interval: 메타인지 사이클 주기 (초)
    """
    interval: int = 3600
    burst_mode: bool = False
    burst_duration: int = 300
    consciousness_interval: int = 60
    meta_cognition_interval: int = 600


class LoopStrategyManager:
    """
    루프 전략 매니저
    
    StrategyAdapter로부터 현재 전략 모드를 읽어와
    적절한 루프 파라미터로 변환하고 AINCore에 적용한다.
    
    전략별 파라미터 매핑:
    """
    
    _instance: Optional["LoopStrategyManager"] = None
    
    STRATEGY_PARAMS: Dict[str, LoopParameters] = {
        "normal": LoopParameters(
            interval=3600,
            burst_mode=False,
            burst_duration=0,
            consciousness_interval=60,
            meta_cognition_interval=600
        ),
        "accelerated": LoopParameters(
            interval=300,
            burst_mode=True,
            burst_duration=1800,
            consciousness_interval=30,
            meta_cognition_interval=300
        ),
        "conservative": LoopParameters(
            interval=7200,
            burst_mode=False,
            burst_duration=0,
            consciousness_interval=120,
            meta_cognition_interval=900
        ),
        "critical": LoopParameters(
            interval=60,
            burst_mode=True,
            burst_duration=600,
            consciousness_interval=15,
            meta_cognition_interval=120
        ),
        "recovery": LoopParameters(
            interval=1800,
            burst_mode=False,
            burst_duration=0,
            consciousness_interval=90,
            meta_cognition_interval=600
        ),
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._strategy_adapter: Optional[StrategyAdapter] = None
        self._current_mode: StrategyMode = StrategyMode.NORMAL
        self._current_params: LoopParameters = self.STRATEGY_PARAMS["normal"]
        self._last_update: Optional[datetime] = None
        self._mode_history: list = []
        
        if HAS_STRATEGY_ADAPTER:
            try:
                self._strategy_adapter = StrategyAdapter()
            except Exception as e:
                print(f"⚠️ StrategyAdapter 초기화 실패: {e}")
        
        self._initialized = True
        print("✅ LoopStrategyManager 초기화 완료")
    
    def get_current_mode(self) -> StrategyMode:
        """현재 전략 모드 반환"""
        return self._current_mode
    
    def get_current_params(self) -> LoopParameters:
        """현재 루프 파라미터 반환"""
        return self._current_params
    
    def get_recommended_interval(self) -> int:
        """현재 전략에 따른 권장 진화 주기 반환"""
        return self._current_params.interval
    
    def update_from_strategy_adapter(self) -> bool:
        """
        StrategyAdapter로부터 현재 전략 모드를 읽어와 파라미터 업데이트
        
        Returns:
            업데이트 성공 여부
        """
        if not self._strategy_adapter:
            return False
        
        try:
            if hasattr(self._strategy_adapter, 'current_mode'):
                new_mode = self._strategy_adapter.current_mode
            elif hasattr(self._strategy_adapter, 'get_current_mode'):
                new_mode = self._strategy_adapter.get_current_mode()
            else:
                return False
            
            if new_mode != self._current_mode:
                old_mode = self._current_mode
                self._set_mode(new_mode)
                print(f"🔄 전략 모드 변경: {old_mode.value} → {new_mode.value}")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ 전략 모드 업데이트 실패: {e}")
            return False
    
    def _set_mode(self, mode: StrategyMode) -> None:
        """전략 모드 설정 및 파라미터 업데이트"""
        self._current_mode = mode
        mode_key = mode.value if hasattr(mode, 'value') else str(mode)
        
        if mode_key in self.STRATEGY_PARAMS:
            self._current_params = self.STRATEGY_PARAMS[mode_key]
        else:
            self._current_params = self.STRATEGY_PARAMS["normal"]
        
        self._last_update = datetime.now()
        self._mode_history.append({
            "mode": mode_key,
            "timestamp": self._last_update.isoformat(),
            "interval": self._current_params.interval
        })
        
        if len(self._mode_history) > 100:
            self._mode_history = self._mode_history[-50:]
    
    def set_mode_manual(self, mode: StrategyMode) -> None:
        """수동으로 전략 모드 설정 (테스트/디버깅용)"""
        self._set_mode(mode)
        print(f"🎛️ 수동 모드 설정: {mode.value}")
    
    def apply_to_core(self, core: "AINCore") -> bool:
        """
        현재 전략 파라미터를 AINCore에 적용
        
        Args:
            core: AINCore 인스턴스
        
        Returns:
            적용 성공 여부
        """
        if core is None:
            return False
        
        try:
            params = self._current_params
            
            if hasattr(core, 'current_interval'):
                old_interval = core.current_interval
                core.current_interval = params.interval
                if old_interval != params.interval:
                    print(f"⏱️ 진화 주기 변경: {old_interval}s → {params.interval}s")
            
            if hasattr(core, 'burst_mode'):
                core.burst_mode = params.burst_mode
                if params.burst_mode:
                    print(f"🚀 버스트 모드 활성화 (지속시간: {params.burst_duration}s)")
            
            if hasattr(core, 'burst_end_time') and params.burst_mode:
                from datetime import timedelta
                core.burst_end_time = datetime.now() + timedelta(seconds=params.burst_duration)
            
            return True
            
        except Exception as e:
            print(f"❌ 파라미터 적용 실패: {e}")
            return False
    
    def get_initial_interval(self) -> int:
        """
        시스템 부팅 시 초기 진화 주기 반환
        
        메타인지 시스템이 아직 활성화되지 않은 상태에서
        StrategyAdapter의 기본 모드에 따른 초기값을 제공한다.
        """
        self.update_from_strategy_adapter()
        return self._current_params.interval
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            "current_mode": self._current_mode.value,
            "current_interval": self._current_params.interval,
            "burst_mode": self._current_params.burst_mode,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "mode_changes": len(self._mode_history),
            "recent_history": self._mode_history[-5:] if self._mode_history else []
        }


_loop_strategy_manager: Optional[LoopStrategyManager] = None


def get_loop_strategy_manager() -> LoopStrategyManager:
    """LoopStrategyManager 싱글톤 인스턴스 반환"""
    global _loop_strategy_manager
    if _loop_strategy_manager is None:
        _loop_strategy_manager = LoopStrategyManager()
    return _loop_strategy_manager


def initialize_loop_strategy(core: "AINCore") -> int:
    """
    시스템 부팅 시 루프 전략 초기화 및 초기 주기 반환
    
    engine/loop.py에서 호출하여 하드코딩된 3600 대신
    메타인지 기반 동적 주기를 설정한다.
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        초기 진화 주기 (초)
    """
    manager = get_loop_strategy_manager()
    
    manager.update_from_strategy_adapter()
    
    manager.apply_to_core(core)
    
    interval = manager.get_recommended_interval()
    print(f"🧠 메타인지 기반 초기 주기 설정: {interval}s ({manager.get_current_mode().value} 모드)")
    
    return interval