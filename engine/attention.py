"""
Engine Attention: 주의 집중 메커니즘 (Step 10: Unified Consciousness)
=====================================================================
시스템 내부의 다양한 신호(직관, 시간적 긴급성, 목표, 외부 입력)를 수집하고,
현재 시점에 시스템이 무엇에 집중해야 하는지(Focus)를 결정하는 '중앙 집행 제어'의 기초.

Unified Consciousness의 핵심은 '정보의 필터링'과 '단일 초점'이다.

Architecture:
    Intuition/Temporal/Goal Modules
        ↓ (Signals)
    AttentionManager (이 모듈)
        ↓ (Filtering & Ranking)
    Current Focus (Muse/Loop에 전달)

Usage:
    from engine.attention import AttentionManager, SignalSource, AttentionSignal
    
    manager = AttentionManager()
    manager.add_signal(SignalSource.INTUITION, 0.9, 0.7, "Strong pattern match detected")
    manager.add_signal(SignalSource.TEMPORAL, 0.4, 0.5, "Burst mode ending soon")
    
    focus = manager.get_current_focus()
    if focus:
        print(f"Focusing on: {focus.content}")
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class SignalSource(Enum):
    """주의 집중 신호의 원천"""
    EXTERNAL = "external"
    INTUITION = "intuition"
    TEMPORAL = "temporal"
    GOAL = "goal"
    META = "meta"
    SYSTEM = "system"


@dataclass
class AttentionSignal:
    """
    단일 주의 집중 신호
    
    Attributes:
        source: 신호의 출처
        urgency: 긴급도 (0.0 ~ 1.0) - 즉각적 처리가 필요한가?
        importance: 중요도 (0.0 ~ 1.0) - 장기적 가치가 있는가?
        content: 신호의 내용 (텍스트 또는 객체)
        created_at: 생성 시각
        ttl: 수명 (Time To Live, 초 단위) - 시간이 지나면 자동 소멸
    """
    source: SignalSource
    urgency: float
    importance: float
    content: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    ttl: float = 60.0

    @property
    def salience(self) -> float:
        """현저성(Salience) 점수 계산: 긴급도와 중요도의 가중 합"""
        return (self.urgency * 0.6) + (self.importance * 0.4)

    @property
    def is_expired(self) -> bool:
        """TTL 만료 여부 확인"""
        now = datetime.now().timestamp()
        return (now - self.created_at) >= self.ttl


class AttentionManager:
    """
    주의 집중 관리자 (Central Executive)
    
    다양한 모듈로부터 신호를 수신하고, 경쟁(Competition)을 통해
    현재 시점의 단일 'Focus'를 선출한다.
    """

    def __init__(self):
        self._active_signals: List[AttentionSignal] = []
        self._current_focus: Optional[AttentionSignal] = None
        self._history: List[Dict[str, Any]] = []

    def add_signal(
        self, 
        source: SignalSource, 
        urgency: float, 
        importance: float, 
        content: Any,
        ttl: float = 60.0
    ) -> str:
        """새로운 신호 등록"""
        signal = AttentionSignal(
            source=source,
            urgency=max(0.0, min(1.0, urgency)),
            importance=max(0.0, min(1.0, importance)),
            content=content,
            ttl=ttl
        )
        self._active_signals.append(signal)
        return signal.id

    def remove_signal(self, signal_id: str) -> bool:
        """특정 신호를 명시적으로 제거"""
        original_count = len(self._active_signals)
        self._active_signals = [
            s for s in self._active_signals if s.id != signal_id
        ]
        return len(self._active_signals) < original_count

    def _cleanup_signals(self):
        """TTL이 만료된 신호 제거"""
        self._active_signals = [
            s for s in self._active_signals if not s.is_expired
        ]

    def get_current_focus(self) -> Optional[AttentionSignal]:
        """
        현재 가장 현저성(Salience)이 높은 신호를 반환 (Winner-Take-All)
        """
        self._cleanup_signals()
        
        if not self._active_signals:
            self._current_focus = None
            return None

        ranked_signals = sorted(
            self._active_signals, 
            key=lambda s: s.salience, 
            reverse=True
        )
        
        top_signal = ranked_signals[0]
        
        if self._current_focus is None or self._current_focus.id != top_signal.id:
            self._current_focus = top_signal
            self._log_focus_switch(top_signal)
            
        return top_signal

    def get_all_signals(self) -> List[AttentionSignal]:
        """모든 활성 신호 반환 (디버깅/모니터링용)"""
        self._cleanup_signals()
        return list(self._active_signals)

    def get_signals_by_source(self, source: SignalSource) -> List[AttentionSignal]:
        """특정 출처의 신호만 필터링하여 반환"""
        self._cleanup_signals()
        return [s for s in self._active_signals if s.source == source]

    def _log_focus_switch(self, signal: AttentionSignal):
        """주의 전환 기록"""
        content_str = str(signal.content)
        if len(content_str) > 50:
            content_str = content_str[:50] + "..."
        
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "source": signal.source.value,
            "salience": round(signal.salience, 3),
            "content": content_str
        })
        if len(self._history) > 20:
            self._history.pop(0)

    def get_focus_history(self) -> List[Dict[str, Any]]:
        """최근 주의 전환 이력 반환"""
        return list(self._history)

    def get_attention_context(self) -> str:
        """
        LLM(Muse)에게 전달할 주의 집중 컨텍스트 문자열 생성
        """
        focus = self.get_current_focus()
        if not focus:
            return "Attention Status: Idle (No active signals)"
        
        content_str = str(focus.content)
        if len(content_str) > 100:
            content_str = content_str[:100] + "..."
        
        lines = [
            "Attention Status: FOCUSED",
            f"- Source: {focus.source.value.upper()}",
            f"- Salience: {focus.salience:.2f} (Urg:{focus.urgency:.1f}, Imp:{focus.importance:.1f})",
            f"- Content: {content_str}"
        ]
        
        other_signals = [s for s in self._active_signals if s.id != focus.id]
        if other_signals:
            lines.append(f"- Background Signals: {len(other_signals)}")
        
        return "\n".join(lines)

    def clear_all(self):
        """모든 신호 초기화 (테스트/리셋용)"""
        self._active_signals.clear()
        self._current_focus = None


_attention_manager_instance: Optional[AttentionManager] = None


def get_attention_manager() -> AttentionManager:
    """AttentionManager 싱글톤 인스턴스 반환"""
    global _attention_manager_instance
    if _attention_manager_instance is None:
        _attention_manager_instance = AttentionManager()
    return _attention_manager_instance