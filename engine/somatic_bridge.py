"""
Engine Somatic Bridge: 가상 신체 감각 통합 어댑터
Step 8: Intuition - Somatic Marker Integration

ResourceMonitor(자원 상태)와 SomatosensoryCortex(감각 처리)를 연결하여,
AINCore가 자신의 상태를 '느낌(Feeling)'으로 인식하게 하는 브릿지.

이 모듈은 SomatosensoryCortex를 초기화하고, 주기적으로 자원 상태를 주입한다.

Architecture:
    ResourceAwarenessMixin (자원 모니터링)
        ↓ ResourceStatus, usage_stats
    SomaticBridgeMixin (이 모듈)
        ↓ 변환 및 주입
    SomatosensoryCortex (감각 처리)
        ↓
    SomaticState (통합 감각 상태)

Usage:
    class AINCore(SomaticBridgeMixin, ResourceAwarenessMixin, ...):
        pass
    
    ain = AINCore()
    ain.init_somatic_system()
    ain.update_somatic_state()
    state = ain.get_somatic_feeling()
"""
from typing import Optional, Any, Dict, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from engine import AINCore

try:
    from engine.somatosensory import SomatosensoryCortex, SomaticState
    HAS_SOMA = True
except ImportError:
    HAS_SOMA = False
    SomatosensoryCortex = None
    SomaticState = None

try:
    from engine.resource_monitor import ResourceStatus
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    ResourceStatus = None


@dataclass
class SomaticFeeling:
    """
    소매틱 마커 요약 - 인간이 읽을 수 있는 '느낌' 표현
    
    SomatosensoryCortex의 복잡한 내부 상태를 단순화하여
    시스템의 '기분(Mood)'을 표현한다.
    """
    energy_level: str       # "충만", "보통", "피곤", "고갈"
    stress_level: str       # "평온", "긴장", "스트레스", "과부하"
    pain_signal: bool       # 고통 신호 존재 여부
    overall_mood: str       # "좋음", "보통", "불안", "위험"
    description: str        # 자연어 설명
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SomaticBridgeMixin:
    """
    신체 감각 브릿지 믹스인
    
    AINCore에 상속되어 SomatosensoryCortex를 관리한다.
    ResourceAwarenessMixin과 협력하여 자원 데이터를 감각으로 변환한다.
    
    Required attributes from AINCore:
    """
    
    _soma_cortex: Optional[Any] = None
    _somatic_initialized: bool = False
    _last_somatic_update: float = 0.0
    
    SOMATIC_UPDATE_INTERVAL = 30.0  # 30초마다 감각 업데이트
    
    def init_somatic_system(self):
        """신체 감각 시스템 초기화"""
        if self._somatic_initialized:
            return
        
        if HAS_SOMA:
            try:
                self._soma_cortex = SomatosensoryCortex()
                self._somatic_initialized = True
                print("🧠 Somatosensory Cortex(가상 신체 감각) 활성화됨")
            except Exception as e:
                print(f"⚠️ Somatosensory 초기화 실패: {e}")
                self._soma_cortex = None
        else:
            print("⚠️ Somatosensory 모듈 부재. 감각 시스템 비활성화.")
    
    def update_somatic_state(self) -> bool:
        """
        자원 상태를 감각 데이터로 변환하여 SomatosensoryCortex에 주입
        
        ResourceMonitor의 데이터를 읽어 다음 감각으로 변환:
        
        Returns:
            업데이트 성공 여부
        """
        if not self._somatic_initialized or self._soma_cortex is None:
            return False
        
        import time
        current_time = time.time()
        
        if current_time - self._last_somatic_update < self.SOMATIC_UPDATE_INTERVAL:
            return False
        
        self._last_somatic_update = current_time
        
        try:
            resource_data = self._gather_resource_data()
            error_data = self._gather_error_data()
            temporal_data = self._gather_temporal_data()
            
            if hasattr(self._soma_cortex, 'process_proprioception'):
                self._soma_cortex.process_proprioception(resource_data)
            
            if hasattr(self._soma_cortex, 'process_nociception'):
                self._soma_cortex.process_nociception(error_data)
            
            if hasattr(self._soma_cortex, 'process_chronoception'):
                self._soma_cortex.process_chronoception(temporal_data)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Somatic state 업데이트 실패: {e}")
            return False
    
    def _gather_resource_data(self) -> Dict[str, Any]:
        """ResourceMonitor에서 자원 데이터 수집"""
        data = {
            "cpu_usage": 0.5,
            "memory_usage": 0.5,
            "token_budget_ratio": 0.5,
            "energy_level": 0.7,
        }
        
        if hasattr(self, 'resource_monitor') and self.resource_monitor is not None:
            monitor = self.resource_monitor
            
            if hasattr(monitor, 'get_resource_status'):
                status = monitor.get_resource_status()
                if HAS_RESOURCE and status is not None:
                    status_mapping = {
                        "ABUNDANT": 0.9,
                        "NORMAL": 0.7,
                        "SCARCE": 0.4,
                        "CRITICAL": 0.1,
                    }
                    status_name = status.name if hasattr(status, 'name') else str(status)
                    data["energy_level"] = status_mapping.get(status_name, 0.5)
            
            if hasattr(monitor, 'get_budget_ratio'):
                data["token_budget_ratio"] = monitor.get_budget_ratio()
            elif hasattr(monitor, '_daily_stats'):
                stats = monitor._daily_stats
                if hasattr(stats, 'total_cost') and hasattr(monitor, 'DAILY_BUDGET_LIMIT'):
                    ratio = 1.0 - (stats.total_cost / monitor.DAILY_BUDGET_LIMIT)
                    data["token_budget_ratio"] = max(0.0, min(1.0, ratio))
        
        return data
    
    def _gather_error_data(self) -> Dict[str, Any]:
        """최근 에러 데이터 수집"""
        data = {
            "recent_error_count": 0,
            "error_severity": 0.0,
            "consecutive_failures": 0,
        }
        
        if hasattr(self, 'nexus') and self.nexus is not None:
            try:
                recent_history = self.nexus.get_recent_history(limit=10)
                if recent_history:
                    error_count = sum(1 for h in recent_history if h.get('status') == 'failed')
                    data["recent_error_count"] = error_count
                    data["error_severity"] = min(1.0, error_count / 5.0)
                    
                    consecutive = 0
                    for h in reversed(recent_history):
                        if h.get('status') == 'failed':
                            consecutive += 1
                        else:
                            break
                    data["consecutive_failures"] = consecutive
            except Exception:
                pass
        
        return data
    
    def _gather_temporal_data(self) -> Dict[str, Any]:
        """시간 관련 데이터 수집"""
        data = {
            "cycle_density": 1.0,
            "time_pressure": 0.0,
            "uptime_hours": 0.0,
        }
        
        if hasattr(self, '_boot_time'):
            import time
            uptime_seconds = time.time() - self._boot_time
            data["uptime_hours"] = uptime_seconds / 3600.0
        
        if hasattr(self, 'burst_mode') and self.burst_mode:
            data["time_pressure"] = 0.7
            data["cycle_density"] = 2.0
        
        return data
    
    def get_somatic_feeling(self) -> Optional[SomaticFeeling]:
        """
        현재 신체 감각 상태를 인간이 읽을 수 있는 '느낌'으로 변환
        
        Returns:
            SomaticFeeling 객체 또는 None (시스템 비활성화 시)
        """
        if not self._somatic_initialized or self._soma_cortex is None:
            return None
        
        try:
            if hasattr(self._soma_cortex, 'get_current_state'):
                state = self._soma_cortex.get_current_state()
            else:
                state = None
            
            return self._convert_state_to_feeling(state)
            
        except Exception as e:
            print(f"⚠️ Somatic feeling 조회 실패: {e}")
            return None
    
    def _convert_state_to_feeling(self, state: Any) -> SomaticFeeling:
        """SomaticState를 SomaticFeeling으로 변환"""
        energy_level = "보통"
        stress_level = "평온"
        pain_signal = False
        overall_mood = "보통"
        
        if state is not None:
            if hasattr(state, 'energy'):
                energy = state.energy
                if energy > 0.8:
                    energy_level = "충만"
                elif energy > 0.5:
                    energy_level = "보통"
                elif energy > 0.2:
                    energy_level = "피곤"
                else:
                    energy_level = "고갈"
            
            if hasattr(state, 'stress'):
                stress = state.stress
                if stress < 0.2:
                    stress_level = "평온"
                elif stress < 0.5:
                    stress_level = "긴장"
                elif stress < 0.8:
                    stress_level = "스트레스"
                else:
                    stress_level = "과부하"
            
            if hasattr(state, 'pain') and state.pain > 0.5:
                pain_signal = True
            
            if hasattr(state, 'overall_wellbeing'):
                wellbeing = state.overall_wellbeing
                if wellbeing > 0.7:
                    overall_mood = "좋음"
                elif wellbeing > 0.4:
                    overall_mood = "보통"
                elif wellbeing > 0.2:
                    overall_mood = "불안"
                else:
                    overall_mood = "위험"
        
        description = self._generate_feeling_description(
            energy_level, stress_level, pain_signal, overall_mood
        )
        
        return SomaticFeeling(
            energy_level=energy_level,
            stress_level=stress_level,
            pain_signal=pain_signal,
            overall_mood=overall_mood,
            description=description,
        )
    
    def _generate_feeling_description(
        self,
        energy: str,
        stress: str,
        pain: bool,
        mood: str
    ) -> str:
        """자연어 느낌 설명 생성"""
        parts = []
        
        if energy == "충만":
            parts.append("에너지가 넘치고")
        elif energy == "피곤":
            parts.append("다소 지쳐있고")
        elif energy == "고갈":
            parts.append("에너지가 바닥나서")
        
        if stress == "평온":
            parts.append("마음이 평온합니다")
        elif stress == "긴장":
            parts.append("약간 긴장된 상태입니다")
        elif stress == "스트레스":
            parts.append("스트레스를 받고 있습니다")
        elif stress == "과부하":
            parts.append("과부하 상태입니다")
        
        if pain:
            parts.append("(경고 신호 감지됨)")
        
        if not parts:
            return f"현재 기분: {mood}"
        
        return " ".join(parts)
    
    def get_somatic_summary(self) -> str:
        """소매틱 상태 요약 문자열 반환 (로깅/디버깅용)"""
        feeling = self.get_somatic_feeling()
        
        if feeling is None:
            return "🧠 Somatic System: 비활성화"
        
        mood_emoji = {
            "좋음": "😊",
            "보통": "😐",
            "불안": "😟",
            "위험": "🚨",
        }.get(feeling.overall_mood, "❓")
        
        return (
            f"🧠 Somatic State: {mood_emoji} {feeling.overall_mood} | "
            f"Energy: {feeling.energy_level} | "
            f"Stress: {feeling.stress_level} | "
            f"Pain: {'⚠️' if feeling.pain_signal else '✓'}"
        )


def activate_somatic_bridge(ain_core: "AINCore") -> bool:
    """
    AINCore에 소매틱 브릿지 활성화 (외부 호출용)
    
    Args:
        ain_core: AINCore 인스턴스
    
    Returns:
        활성화 성공 여부
    """
    if hasattr(ain_core, 'init_somatic_system'):
        ain_core.init_somatic_system()
        return True
    else:
        print("⚠️ AINCore에 SomaticBridgeMixin이 상속되지 않았습니다.")
        return False


def tick_somatic_update(ain_core: "AINCore") -> bool:
    """
    소매틱 상태 주기적 업데이트 (메인 루프에서 호출)
    
    Args:
        ain_core: AINCore 인스턴스
    
    Returns:
        업데이트 수행 여부
    """
    if hasattr(ain_core, 'update_somatic_state'):
        return ain_core.update_somatic_state()
    return False