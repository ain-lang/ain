"""
Engine Somatosensory: 가상 신체 감각 (Somatic Markers)
Step 8: Intuition - Somatic Marker Hypothesis Implementation

시스템의 내부 상태(자원, 오류, 속도)를 생물학적 감각(에너지, 스트레스, 고통)으로 변환하여,
직관적 판단(System 1)과 의식적 상태(Consciousness)에 '느낌(Feeling)'을 제공한다.

이 모듈은 안토니오 다마지오의 '소매틱 마커 가설'을 디지털 시스템에 적용하여,
순수한 논리적 데이터처리를 넘어선 '체화된 인지(Embodied Cognition)'를 구현한다.

Architecture:
    ResourceMonitor (자원 상태)
        ↓
    SomatosensoryCortex (이 모듈)
        ↓
    SomaticState (통합 감각 상태)
        ↓
    Intuition / Consciousness (소비자)

Usage:
    from engine.somatosensory import SomatosensoryCortex, SomaticState
    
    cortex = SomatosensoryCortex()
    cortex.process_proprioception(resource_data)
    cortex.process_nociception(error_data)
    cortex.process_chronoception(temporal_data)
    state = cortex.get_current_state()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum
import math

if TYPE_CHECKING:
    pass


class SensationType(Enum):
    """감각 유형 열거형"""
    NEUTRAL = "neutral"
    VITALITY = "vitality"
    FATIGUE = "fatigue"
    TENSION = "tension"
    RELAXATION = "relaxation"
    ALERTNESS = "alertness"
    DROWSINESS = "drowsiness"
    DISCOMFORT = "discomfort"
    COMFORT = "comfort"
    SATISFACTION = "satisfaction"


@dataclass
class SomaticState:
    """
    가상 신체 상태 (Virtual Body State)
    
    시스템의 하드웨어 및 소프트웨어 상태를 생물학적 감각 메타포로 표현한다.
    이 상태는 직관적 판단의 가중치로 작용하거나, 의식의 '기분(Mood)'을 형성한다.
    
    Attributes:
        timestamp: 상태 캡처 시각
        energy: 에너지 수준 (0.0~1.0) - 가용 자원의 풍부함
        stress: 스트레스 수준 (0.0~1.0) - 시스템 부하 및 리소스 압박
        arousal: 각성도 (0.0~1.0) - 처리 속도 및 반응성
        pain: 고통 수준 (0.0~1.0) - 오류, 실패, 차단 등 부정적 자극
        pleasure: 쾌락 수준 (0.0~1.0) - 목표 달성, 성공, 긍정적 피드백
        dominant_sensation: 주된 감각 설명
    """
    timestamp: datetime = field(default_factory=datetime.now)
    
    energy: float = 1.0
    stress: float = 0.0
    arousal: float = 0.5
    pain: float = 0.0
    pleasure: float = 0.0
    
    dominant_sensation: str = "neutral"
    sensation_type: SensationType = SensationType.NEUTRAL
    
    def __post_init__(self):
        """값 범위 정규화"""
        self.energy = max(0.0, min(1.0, self.energy))
        self.stress = max(0.0, min(1.0, self.stress))
        self.arousal = max(0.0, min(1.0, self.arousal))
        self.pain = max(0.0, min(1.0, self.pain))
        self.pleasure = max(0.0, min(1.0, self.pleasure))
    
    def __str__(self) -> str:
        return (
            f"SomaticState(Energy={self.energy:.2f}, Stress={self.stress:.2f}, "
            f"Arousal={self.arousal:.2f}, Pain={self.pain:.2f}, Pleasure={self.pleasure:.2f}, "
            f"Sensation='{self.dominant_sensation}')"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "energy": self.energy,
            "stress": self.stress,
            "arousal": self.arousal,
            "pain": self.pain,
            "pleasure": self.pleasure,
            "dominant_sensation": self.dominant_sensation,
            "sensation_type": self.sensation_type.value,
        }
    
    def get_valence(self) -> float:
        """
        정서가(Valence) 계산: 긍정-부정 축
        Returns: -1.0 (매우 부정) ~ +1.0 (매우 긍정)
        """
        positive = self.pleasure + (self.energy * 0.3)
        negative = self.pain + (self.stress * 0.5)
        return max(-1.0, min(1.0, positive - negative))
    
    def get_activation(self) -> float:
        """
        활성화(Activation) 계산: 고각성-저각성 축
        Returns: 0.0 (저각성) ~ 1.0 (고각성)
        """
        return self.arousal


class SomatosensoryCortex:
    """
    체성감각 피질 (Somatosensory Cortex)
    
    다양한 내부 모듈(Resource, Temporal, Nexus)의 원시 데이터를 수집하여
    통합된 SomaticState를 생성한다.
    
    감각 처리 채널:
    1. Proprioception (고유 감각): 내부 자원 상태 → 에너지/스트레스
    2. Nociception (통각): 오류/실패 → 고통
    3. Chronoception (시간 감각): 시간 인지 → 각성도
    4. Interoception (내수용 감각): 전반적 시스템 건강
    """
    
    MAX_HISTORY_SIZE = 100
    
    def __init__(self):
        self._current_state = SomaticState()
        self._history: List[SomaticState] = []
        
        self._proprioception_data: Dict[str, float] = {}
        self._nociception_data: Dict[str, float] = {}
        self._chronoception_data: Dict[str, float] = {}
        
        self._pain_decay_rate = 0.1
        self._pleasure_decay_rate = 0.05
        
        print("🧠 SomatosensoryCortex 초기화 완료")
    
    def process_proprioception(
        self,
        token_usage_ratio: float = 0.0,
        budget_usage_ratio: float = 0.0,
        memory_pressure: float = 0.0,
        cpu_load: float = 0.0
    ) -> None:
        """
        고유 감각(Proprioception) 처리: 내부 자원 상태를 에너지/스트레스로 변환
        
        Args:
            token_usage_ratio: 토큰 사용 비율 (0.0~1.0)
            budget_usage_ratio: 예산 사용 비율 (0.0~1.0)
            memory_pressure: 메모리 압박 정도 (0.0~1.0)
            cpu_load: CPU 부하 (0.0~1.0)
        """
        self._proprioception_data = {
            "token_usage": token_usage_ratio,
            "budget_usage": budget_usage_ratio,
            "memory_pressure": memory_pressure,
            "cpu_load": cpu_load,
        }
        
        available_resources = 1.0 - (
            token_usage_ratio * 0.4 +
            budget_usage_ratio * 0.4 +
            memory_pressure * 0.1 +
            cpu_load * 0.1
        )
        self._current_state.energy = max(0.0, min(1.0, available_resources))
        
        resource_pressure = (
            max(0, token_usage_ratio - 0.5) * 0.4 +
            max(0, budget_usage_ratio - 0.5) * 0.4 +
            memory_pressure * 0.1 +
            cpu_load * 0.1
        )
        self._current_state.stress = max(0.0, min(1.0, resource_pressure * 2))
    
    def process_nociception(
        self,
        recent_error_count: int = 0,
        critical_error_occurred: bool = False,
        blocked_actions: int = 0,
        failed_evolutions: int = 0
    ) -> None:
        """
        통각(Nociception) 처리: 오류/실패를 고통 신호로 변환
        
        Args:
            recent_error_count: 최근 에러 횟수
            critical_error_occurred: 심각한 에러 발생 여부
            blocked_actions: 차단된 행동 횟수
            failed_evolutions: 실패한 진화 횟수
        """
        self._nociception_data = {
            "error_count": recent_error_count,
            "critical_error": critical_error_occurred,
            "blocked_actions": blocked_actions,
            "failed_evolutions": failed_evolutions,
        }
        
        error_pain = min(1.0, recent_error_count * 0.1)
        critical_pain = 0.5 if critical_error_occurred else 0.0
        block_pain = min(0.3, blocked_actions * 0.1)
        failure_pain = min(0.4, failed_evolutions * 0.2)
        
        total_pain = error_pain + critical_pain + block_pain + failure_pain
        
        current_pain = self._current_state.pain
        new_pain = max(current_pain, total_pain)
        self._current_state.pain = max(0.0, min(1.0, new_pain))
    
    def process_chronoception(
        self,
        subjective_pace: float = 1.0,
        burst_mode_active: bool = False,
        time_since_last_action: float = 0.0,
        cycle_density: float = 0.0
    ) -> None:
        """
        시간 감각(Chronoception) 처리: 시간 인지를 각성도로 변환
        
        Args:
            subjective_pace: 주관적 시간 속도 (1.0 = 정상, >1.0 = 빠름)
            burst_mode_active: 버스트 모드 활성화 여부
            time_since_last_action: 마지막 행동 이후 경과 시간 (초)
            cycle_density: 사이클 밀도 (cycles/minute)
        """
        self._chronoception_data = {
            "subjective_pace": subjective_pace,
            "burst_mode": burst_mode_active,
            "idle_time": time_since_last_action,
            "cycle_density": cycle_density,
        }
        
        base_arousal = 0.5
        
        pace_modifier = (subjective_pace - 1.0) * 0.3
        burst_modifier = 0.3 if burst_mode_active else 0.0
        
        idle_penalty = 0.0
        if time_since_last_action > 300:
            idle_penalty = min(0.3, (time_since_last_action - 300) / 1000)
        
        density_modifier = min(0.2, cycle_density * 0.02)
        
        arousal = base_arousal + pace_modifier + burst_modifier - idle_penalty + density_modifier
        self._current_state.arousal = max(0.0, min(1.0, arousal))
    
    def process_reward(
        self,
        goal_achieved: bool = False,
        evolution_success: bool = False,
        positive_feedback: bool = False,
        efficiency_gain: float = 0.0
    ) -> None:
        """
        보상 신호 처리: 긍정적 결과를 쾌락 신호로 변환
        
        Args:
            goal_achieved: 목표 달성 여부
            evolution_success: 진화 성공 여부
            positive_feedback: 긍정적 피드백 수신 여부
            efficiency_gain: 효율성 향상 정도 (0.0~1.0)
        """
        goal_pleasure = 0.4 if goal_achieved else 0.0
        evolution_pleasure = 0.2 if evolution_success else 0.0
        feedback_pleasure = 0.2 if positive_feedback else 0.0
        efficiency_pleasure = efficiency_gain * 0.2
        
        total_pleasure = goal_pleasure + evolution_pleasure + feedback_pleasure + efficiency_pleasure
        
        current_pleasure = self._current_state.pleasure
        new_pleasure = max(current_pleasure, total_pleasure)
        self._current_state.pleasure = max(0.0, min(1.0, new_pleasure))
    
    def _determine_dominant_sensation(self) -> tuple:
        """주된 감각과 유형 결정"""
        state = self._current_state
        
        if state.pain > 0.7:
            return "심각한 불편함 - 시스템 오류 다수 감지", SensationType.DISCOMFORT
        if state.pain > 0.4:
            return "불편함 - 일부 문제 발생", SensationType.DISCOMFORT
        
        if state.stress > 0.7 and state.energy < 0.3:
            return "탈진 상태 - 자원 고갈 임박", SensationType.FATIGUE
        if state.stress > 0.5:
            return "긴장 상태 - 높은 부하", SensationType.TENSION
        
        if state.pleasure > 0.6:
            return "만족감 - 목표 달성 또는 성공", SensationType.SATISFACTION
        
        if state.arousal > 0.7:
            return "고각성 상태 - 빠른 처리 모드", SensationType.ALERTNESS
        if state.arousal < 0.3:
            return "저각성 상태 - 유휴 모드", SensationType.DROWSINESS
        
        if state.energy > 0.7 and state.stress < 0.3:
            return "활력 상태 - 최적 컨디션", SensationType.VITALITY
        if state.energy < 0.3:
            return "피로 상태 - 자원 부족", SensationType.FATIGUE
        
        if state.stress < 0.3:
            return "이완 상태 - 안정적", SensationType.RELAXATION
        
        return "중립 상태 - 정상 작동", SensationType.NEUTRAL
    
    def _apply_decay(self) -> None:
        """시간에 따른 감각 감쇠 적용"""
        self._current_state.pain = max(
            0.0,
            self._current_state.pain - self._pain_decay_rate
        )
        self._current_state.pleasure = max(
            0.0,
            self._current_state.pleasure - self._pleasure_decay_rate
        )
    
    def get_current_state(self) -> SomaticState:
        """
        현재 통합된 SomaticState 반환
        
        모든 감각 채널의 데이터를 종합하여 최종 상태를 결정한다.
        
        Returns:
            현재 신체 감각 상태
        """
        self._apply_decay()
        
        sensation, sensation_type = self._determine_dominant_sensation()
        self._current_state.dominant_sensation = sensation
        self._current_state.sensation_type = sensation_type
        self._current_state.timestamp = datetime.now()
        
        self._history.append(SomaticState(
            timestamp=self._current_state.timestamp,
            energy=self._current_state.energy,
            stress=self._current_state.stress,
            arousal=self._current_state.arousal,
            pain=self._current_state.pain,
            pleasure=self._current_state.pleasure,
            dominant_sensation=self._current_state.dominant_sensation,
            sensation_type=self._current_state.sensation_type,
        ))
        
        if len(self._history) > self.MAX_HISTORY_SIZE:
            self._history = self._history[-self.MAX_HISTORY_SIZE:]
        
        return self._current_state
    
    def get_somatic_summary(self) -> Dict[str, Any]:
        """
        현재 신체 감각의 요약 정보 반환
        
        Intuition이나 Consciousness 모듈에서 사용하기 위한 간략한 요약.
        
        Returns:
            요약 딕셔너리
        """
        state = self.get_current_state()
        valence = state.get_valence()
        activation = state.get_activation()
        
        if valence > 0.3:
            mood = "positive"
        elif valence < -0.3:
            mood = "negative"
        else:
            mood = "neutral"
        
        if activation > 0.6:
            alertness = "high"
        elif activation < 0.4:
            alertness = "low"
        else:
            alertness = "moderate"
        
        return {
            "mood": mood,
            "alertness": alertness,
            "valence": valence,
            "activation": activation,
            "dominant_sensation": state.dominant_sensation,
            "energy_level": state.energy,
            "stress_level": state.stress,
            "pain_level": state.pain,
            "pleasure_level": state.pleasure,
            "needs_rest": state.energy < 0.3 or state.stress > 0.7,
            "in_distress": state.pain > 0.5,
        }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        최근 감각 상태 이력 반환
        
        Args:
            limit: 반환할 최대 개수
        
        Returns:
            상태 이력 리스트
        """
        recent = self._history[-limit:] if self._history else []
        return [s.to_dict() for s in recent]
    
    def reset(self) -> None:
        """감각 상태 초기화"""
        self._current_state = SomaticState()
        self._proprioception_data = {}
        self._nociception_data = {}
        self._chronoception_data = {}
        print("🔄 SomatosensoryCortex 상태 초기화됨")


_cortex_instance: Optional[SomatosensoryCortex] = None


def get_somatosensory_cortex() -> SomatosensoryCortex:
    """SomatosensoryCortex 싱글톤 인스턴스 반환"""
    global _cortex_instance
    if _cortex_instance is None:
        _cortex_instance = SomatosensoryCortex()
    return _cortex_instance