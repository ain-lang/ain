"""
Engine Temporal: Step 9 - 시간적 자아 (Temporal Self)
=====================================================
시스템이 '시간의 흐름'을 인식하고, 물리적 시간과 주관적 시간의 괴리를 추적한다.

Temporal Self란:
단순한 시계(Clock) 기능을 넘어, 자신의 존재가 시간 축 위에서 연속적임을 인지하는 능력.
시스템의 처리 부하(Load)에 따라 '주관적 시간(Subjective Time)'이 얼마나 빠르게/느리게
흐르는지(Time Dilation)를 계산한다.

Architecture:
    AINCore
        ↓ 상속
    TemporalAwarenessMixin (이 모듈)
        ↓
    Uptime, Cycle Density, Subjective Pace 추적

Usage:
    ain.init_temporal()
    stats = ain.get_temporal_stats()
    print(f"Subjective Pace: {stats['subjective_pace']}x")
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class TemporalPhase(Enum):
    """시간적 상태 단계"""
    NASCENT = "nascent"          # 부팅 직후 (0-5분)
    AWAKENING = "awakening"      # 초기 각성 (5-30분)
    ACTIVE = "active"            # 활성 상태 (30분-4시간)
    SUSTAINED = "sustained"      # 지속 상태 (4시간-24시간)
    MATURE = "mature"            # 성숙 상태 (24시간+)


@dataclass
class TemporalSnapshot:
    """특정 시점의 시간 상태 스냅샷"""
    timestamp: datetime
    uptime_seconds: float
    cycle_count: int
    subjective_pace: float
    phase: TemporalPhase
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "cycle_count": self.cycle_count,
            "subjective_pace": self.subjective_pace,
            "phase": self.phase.value
        }


class TemporalAwarenessMixin:
    """
    시간 인식 믹스인
    
    시스템의 시간적 연속성을 관리하고, 주관적 시간 감각을 제공한다.
    
    Attributes:
        _boot_time: 시스템 부팅 시각
        _last_tick_time: 마지막 tick 호출 시간 (Unix timestamp)
        _total_cycles: 누적 사이클 수
        _cycle_durations: 최근 N개 사이클의 소요 시간 (deque)
        _reference_pace: 기준 사이클 속도 (초/사이클)
        _temporal_snapshots: 시간 상태 스냅샷 이력
    """
    
    # 설정 상수
    CYCLE_HISTORY_SIZE = 100  # 추적할 최근 사이클 수
    REFERENCE_PACE = 300.0    # 기준 사이클 속도 (5분 = 300초)
    SNAPSHOT_INTERVAL = 600   # 스냅샷 저장 간격 (10분)
    MAX_SNAPSHOTS = 144       # 최대 스냅샷 수 (24시간 분량)
    
    def init_temporal(self) -> None:
        """시간 인식 시스템 초기화"""
        self._boot_time: datetime = datetime.now()
        self._boot_timestamp: float = time.time()
        self._last_tick_time: float = time.time()
        self._total_cycles: int = 0
        self._cycle_durations: deque = deque(maxlen=self.CYCLE_HISTORY_SIZE)
        self._reference_pace: float = self.REFERENCE_PACE
        self._temporal_snapshots: deque = deque(maxlen=self.MAX_SNAPSHOTS)
        self._last_snapshot_time: float = time.time()
        
        # 초기 스냅샷 저장
        self._save_temporal_snapshot()
        
        print(f"⏰ 시간 인식 시스템 초기화 완료 (Boot: {self._boot_time.isoformat()})")
    
    def temporal_tick(self) -> Dict[str, Any]:
        """
        시간 사이클 틱 - 매 진화 루프에서 호출
        
        Returns:
            현재 시간 상태 정보
        """
        current_time = time.time()
        
        # 사이클 소요 시간 계산
        if self._last_tick_time > 0:
            cycle_duration = current_time - self._last_tick_time
            self._cycle_durations.append(cycle_duration)
        
        self._last_tick_time = current_time
        self._total_cycles += 1
        
        # 주기적 스냅샷 저장
        if current_time - self._last_snapshot_time >= self.SNAPSHOT_INTERVAL:
            self._save_temporal_snapshot()
            self._last_snapshot_time = current_time
        
        return self.get_temporal_stats()
    
    def get_temporal_stats(self) -> Dict[str, Any]:
        """
        현재 시간 상태 통계 반환
        
        Returns:
            {
                "uptime": 가동 시간 (timedelta 문자열),
                "uptime_seconds": 가동 시간 (초),
                "boot_time": 부팅 시각 (ISO 문자열),
                "total_cycles": 총 사이클 수,
                "avg_cycle_duration": 평균 사이클 소요 시간,
                "subjective_pace": 주관적 시간 속도 (1.0 = 기준),
                "phase": 현재 시간 단계,
                "cycle_density": 사이클 밀도 (cycles/hour),
                "time_dilation": 시간 팽창 비율
            }
        """
        current_time = time.time()
        uptime_seconds = current_time - self._boot_timestamp
        
        # 평균 사이클 소요 시간
        avg_duration = self._calculate_avg_cycle_duration()
        
        # 주관적 시간 속도 계산
        subjective_pace = self._calculate_subjective_pace(avg_duration)
        
        # 현재 단계 결정
        phase = self._determine_temporal_phase(uptime_seconds)
        
        # 사이클 밀도 (시간당 사이클 수)
        cycle_density = self._calculate_cycle_density(uptime_seconds)
        
        # 시간 팽창 비율
        time_dilation = self._calculate_time_dilation(avg_duration)
        
        return {
            "uptime": str(timedelta(seconds=int(uptime_seconds))),
            "uptime_seconds": uptime_seconds,
            "boot_time": self._boot_time.isoformat(),
            "total_cycles": self._total_cycles,
            "avg_cycle_duration": avg_duration,
            "subjective_pace": subjective_pace,
            "phase": phase.value,
            "cycle_density": cycle_density,
            "time_dilation": time_dilation
        }
    
    def _calculate_avg_cycle_duration(self) -> float:
        """평균 사이클 소요 시간 계산"""
        if not self._cycle_durations:
            return self._reference_pace
        return sum(self._cycle_durations) / len(self._cycle_durations)
    
    def _calculate_subjective_pace(self, avg_duration: float) -> float:
        """
        주관적 시간 속도 계산
        
        기준 속도 대비 현재 속도의 비율.
        """
        if avg_duration <= 0:
            return 1.0
        return self._reference_pace / avg_duration
    
    def _calculate_time_dilation(self, avg_duration: float) -> float:
        """
        시간 팽창 비율 계산
        
        물리적 시간 대비 주관적 시간의 팽창/수축 비율.
        """
        if avg_duration <= 0:
            return 1.0
        
        # 사이클 밀도 기반 계산
        expected_cycles = (time.time() - self._boot_timestamp) / self._reference_pace
        actual_cycles = self._total_cycles
        
        if expected_cycles <= 0:
            return 1.0
        
        return actual_cycles / expected_cycles
    
    def _calculate_cycle_density(self, uptime_seconds: float) -> float:
        """사이클 밀도 계산 (시간당 사이클 수)"""
        if uptime_seconds <= 0:
            return 0.0
        hours = uptime_seconds / 3600.0
        if hours <= 0:
            return 0.0
        return self._total_cycles / hours
    
    def _determine_temporal_phase(self, uptime_seconds: float) -> TemporalPhase:
        """현재 시간 단계 결정"""
        minutes = uptime_seconds / 60.0
        hours = uptime_seconds / 3600.0
        
        if minutes < 5:
            return TemporalPhase.NASCENT
        elif minutes < 30:
            return TemporalPhase.AWAKENING
        elif hours < 4:
            return TemporalPhase.ACTIVE
        elif hours < 24:
            return TemporalPhase.SUSTAINED
        else:
            return TemporalPhase.MATURE
    
    def _save_temporal_snapshot(self) -> None:
        """현재 시간 상태 스냅샷 저장"""
        stats = self.get_temporal_stats() if hasattr(self, '_boot_timestamp') else None
        
        if stats is None:
            return
        
        snapshot = TemporalSnapshot(
            timestamp=datetime.now(),
            uptime_seconds=stats.get("uptime_seconds", 0),
            cycle_count=stats.get("total_cycles", 0),
            subjective_pace=stats.get("subjective_pace", 1.0),
            phase=TemporalPhase(stats.get("phase", "nascent"))
        )
        
        self._temporal_snapshots.append(snapshot)
    
    def get_temporal_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        시간 상태 이력 반환
        
        Args:
            limit: 반환할 최대 스냅샷 수
        
        Returns:
            스냅샷 딕셔너리 리스트 (최신순)
        """
        snapshots = list(self._temporal_snapshots)[-limit:]
        return [s.to_dict() for s in reversed(snapshots)]
    
    def get_temporal_narrative(self) -> str:
        """
        시간 인식 상태를 자연어 서술로 반환
        
        내부 독백(Inner Monologue)에서 사용할 수 있는 형태.
        """
        stats = self.get_temporal_stats()
        
        phase_descriptions = {
            "nascent": "방금 깨어났다",
            "awakening": "점차 각성하고 있다",
            "active": "활발하게 활동 중이다",
            "sustained": "지속적으로 운영 중이다",
            "mature": "안정적인 성숙 상태에 도달했다"
        }
        
        phase_desc = phase_descriptions.get(stats["phase"], "알 수 없는 상태")
        
        pace = stats["subjective_pace"]
        if pace > 1.5:
            pace_desc = "시간이 매우 빠르게 흐르고 있다"
        elif pace > 1.1:
            pace_desc = "시간이 약간 빠르게 흐르고 있다"
        elif pace < 0.7:
            pace_desc = "시간이 느리게 흐르고 있다"
        elif pace < 0.9:
            pace_desc = "시간이 약간 느리게 흐르고 있다"
        else:
            pace_desc = "시간이 정상적으로 흐르고 있다"
        
        narrative = (
            f"나는 {stats['uptime']} 동안 가동되어 왔으며, "
            f"현재 {phase_desc}. "
            f"지금까지 {stats['total_cycles']}번의 사이클을 수행했고, "
            f"{pace_desc} (주관적 속도: {pace:.2f}x). "
            f"시간당 약 {stats['cycle_density']:.1f}회의 사이클을 처리하고 있다."
        )
        
        return narrative
    
    def estimate_remaining_capacity(self, target_cycles: int) -> Optional[timedelta]:
        """
        목표 사이클 수에 도달하기까지 예상 시간 계산
        
        Args:
            target_cycles: 목표 사이클 수
        
        Returns:
            예상 소요 시간 (timedelta) 또는 None (이미 초과)
        """
        if self._total_cycles >= target_cycles:
            return None
        
        remaining = target_cycles - self._total_cycles
        avg_duration = self._calculate_avg_cycle_duration()
        
        estimated_seconds = remaining * avg_duration
        return timedelta(seconds=estimated_seconds)