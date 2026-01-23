"""
Engine Runtime Tuner: 메타인지 전략을 시스템 파라미터로 변환하는 액추에이터
Step 7: Meta-Cognition - Strategy to Parameter Actuator

이 모듈은 StrategyAdapter가 결정한 StrategyMode를 실제 시스템 런타임 파라미터
(진화 주기, 버스트 모드, temperature 등)로 변환하고 적용하는 역할을 담당한다.

engine/loop.py의 하드코딩된 값을 대체하여 동적 조절이 가능하게 한다.

Architecture:
    MetaCycle (평가/전략 결정)
        ↓ StrategyMode
    RuntimeTuner (이 모듈)
        ↓ 파라미터 변환 및 적용
    AINCore (실제 런타임)

Usage:
    from engine.runtime_tuner import RuntimeTuner, get_runtime_tuner
    
    tuner = get_runtime_tuner()
    tuner.apply_strategy(StrategyMode.ACCELERATED)
    interval = tuner.get_evolution_interval()
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from engine import AINCore

try:
    from engine.strategy_adapter import StrategyMode
    HAS_STRATEGY_ADAPTER = True
except ImportError:
    HAS_STRATEGY_ADAPTER = False
    
    class StrategyMode(Enum):
        NORMAL = "normal"
        ACCELERATED = "accelerated"
        CONSERVATIVE = "conservative"
        RECOVERY = "recovery"
        EXPLORATORY = "exploratory"


@dataclass
class RuntimeParameters:
    """
    런타임 파라미터 데이터 클래스
    
    시스템의 동적 조절 가능한 모든 파라미터를 캡슐화한다.
    
    Attributes:
        evolution_interval: 진화 주기 (초)
        burst_mode: 버스트 모드 활성화 여부
        burst_duration: 버스트 모드 지속 시간 (초)
        temperature: LLM 창의성 파라미터
        validation_level: 검증 강도 (1-3)
        monologue_interval: 내부 독백 주기 (초)
    """
    evolution_interval: int = 3600
    burst_mode: bool = False
    burst_duration: int = 300
    temperature: float = 0.7
    validation_level: int = 2
    monologue_interval: int = 3600
    last_updated: datetime = field(default_factory=datetime.now)
    active_mode: str = "normal"


class RuntimeTuner:
    """
    런타임 튜너 - StrategyMode를 시스템 파라미터로 변환
    
    메타인지 시스템이 결정한 전략을 실제 런타임 동작에 반영한다.
    싱글톤 패턴으로 시스템 전역에서 일관된 파라미터를 유지한다.
    
    전략별 파라미터 매핑:
    """
    
    _instance: Optional["RuntimeTuner"] = None
    
    STRATEGY_PARAMS: Dict[str, Dict[str, Any]] = {
        "normal": {
            "evolution_interval": 3600,
            "burst_mode": False,
            "burst_duration": 300,
            "temperature": 0.7,
            "validation_level": 2,
            "monologue_interval": 3600,
        },
        "accelerated": {
            "evolution_interval": 1800,
            "burst_mode": True,
            "burst_duration": 600,
            "temperature": 0.8,
            "validation_level": 2,
            "monologue_interval": 1800,
        },
        "conservative": {
            "evolution_interval": 7200,
            "burst_mode": False,
            "burst_duration": 180,
            "temperature": 0.5,
            "validation_level": 3,
            "monologue_interval": 2700,
        },
        "recovery": {
            "evolution_interval": 3600,
            "burst_mode": False,
            "burst_duration": 120,
            "temperature": 0.6,
            "validation_level": 3,
            "monologue_interval": 1200,
        },
        "exploratory": {
            "evolution_interval": 2700,
            "burst_mode": True,
            "burst_duration": 450,
            "temperature": 0.9,
            "validation_level": 1,
            "monologue_interval": 1200,
        },
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._params = RuntimeParameters()
        self._ain_core: Optional["AINCore"] = None
        self._mode_history: list = []
        self._initialized = True
        print("⚙️ RuntimeTuner 초기화 완료")
    
    def bind_core(self, core: "AINCore"):
        """
        AINCore 인스턴스를 바인딩하여 직접 파라미터 적용 가능하게 함
        
        Args:
            core: AINCore 인스턴스
        """
        self._ain_core = core
        print("🔗 RuntimeTuner: AINCore 바인딩 완료")
    
    @property
    def current_params(self) -> RuntimeParameters:
        """현재 런타임 파라미터 반환"""
        return self._params
    
    @property
    def current_mode(self) -> str:
        """현재 활성 모드 반환"""
        return self._params.active_mode
    
    def apply_strategy(self, mode: StrategyMode) -> RuntimeParameters:
        """
        StrategyMode를 시스템 파라미터로 변환하고 적용
        
        Args:
            mode: 적용할 전략 모드
        
        Returns:
            적용된 RuntimeParameters
        """
        mode_key = mode.value if hasattr(mode, 'value') else str(mode)
        
        if mode_key not in self.STRATEGY_PARAMS:
            print(f"⚠️ 알 수 없는 전략 모드: {mode_key}, NORMAL로 대체")
            mode_key = "normal"
        
        params = self.STRATEGY_PARAMS[mode_key]
        
        self._params.evolution_interval = params["evolution_interval"]
        self._params.burst_mode = params["burst_mode"]
        self._params.burst_duration = params["burst_duration"]
        self._params.temperature = params["temperature"]
        self._params.validation_level = params["validation_level"]
        self._params.monologue_interval = params["monologue_interval"]
        self._params.active_mode = mode_key
        self._params.last_updated = datetime.now()
        
        self._mode_history.append({
            "mode": mode_key,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._mode_history) > 100:
            self._mode_history = self._mode_history[-50:]
        
        if self._ain_core:
            self._apply_to_core()
        
        print(f"⚙️ 전략 적용: {mode_key} → 진화주기={params['evolution_interval']}s, "
              f"버스트={params['burst_mode']}, temp={params['temperature']}")
        
        return self._params
    
    def _apply_to_core(self):
        """AINCore에 현재 파라미터 직접 적용"""
        if not self._ain_core:
            return
        
        if hasattr(self._ain_core, 'current_interval'):
            self._ain_core.current_interval = self._params.evolution_interval
        
        if hasattr(self._ain_core, 'burst_mode'):
            self._ain_core.burst_mode = self._params.burst_mode
        
        if hasattr(self._ain_core, 'burst_end_time') and self._params.burst_mode:
            self._ain_core.burst_end_time = datetime.now() + timedelta(
                seconds=self._params.burst_duration
            )
    
    def get_evolution_interval(self) -> int:
        """현재 진화 주기 반환 (초)"""
        return self._params.evolution_interval
    
    def get_monologue_interval(self) -> int:
        """현재 내부 독백 주기 반환 (초)"""
        return self._params.monologue_interval
    
    def get_temperature(self) -> float:
        """현재 LLM temperature 반환"""
        return self._params.temperature
    
    def get_validation_level(self) -> int:
        """현재 검증 강도 반환 (1-3)"""
        return self._params.validation_level
    
    def is_burst_active(self) -> bool:
        """버스트 모드 활성화 여부"""
        return self._params.burst_mode
    
    def trigger_burst(self, duration: int = None):
        """
        수동으로 버스트 모드 활성화
        
        Args:
            duration: 버스트 지속 시간 (초), None이면 현재 설정 사용
        """
        self._params.burst_mode = True
        if duration:
            self._params.burst_duration = duration
        
        if self._ain_core and hasattr(self._ain_core, 'burst_mode'):
            self._ain_core.burst_mode = True
            self._ain_core.burst_end_time = datetime.now() + timedelta(
                seconds=self._params.burst_duration
            )
        
        print(f"🚀 버스트 모드 활성화: {self._params.burst_duration}초")
    
    def end_burst(self):
        """버스트 모드 종료"""
        self._params.burst_mode = False
        
        if self._ain_core and hasattr(self._ain_core, 'burst_mode'):
            self._ain_core.burst_mode = False
            self._ain_core.burst_end_time = None
        
        print("🍃 버스트 모드 종료")
    
    def get_stats(self) -> Dict[str, Any]:
        """튜너 상태 통계 반환"""
        return {
            "current_mode": self._params.active_mode,
            "evolution_interval": self._params.evolution_interval,
            "burst_mode": self._params.burst_mode,
            "temperature": self._params.temperature,
            "validation_level": self._params.validation_level,
            "monologue_interval": self._params.monologue_interval,
            "last_updated": self._params.last_updated.isoformat(),
            "mode_changes": len(self._mode_history),
            "core_bound": self._ain_core is not None,
        }
    
    def get_mode_history(self, limit: int = 10) -> list:
        """최근 모드 변경 이력 반환"""
        return self._mode_history[-limit:]


_tuner_instance: Optional[RuntimeTuner] = None


def get_runtime_tuner() -> RuntimeTuner:
    """RuntimeTuner 싱글톤 인스턴스 반환"""
    global _tuner_instance
    if _tuner_instance is None:
        _tuner_instance = RuntimeTuner()
    return _tuner_instance


def apply_strategy_mode(mode: StrategyMode) -> RuntimeParameters:
    """
    편의 함수: 전략 모드를 바로 적용
    
    Args:
        mode: 적용할 StrategyMode
    
    Returns:
        적용된 RuntimeParameters
    """
    tuner = get_runtime_tuner()
    return tuner.apply_strategy(mode)


def get_current_interval() -> int:
    """편의 함수: 현재 진화 주기 반환"""
    tuner = get_runtime_tuner()
    return tuner.get_evolution_interval()