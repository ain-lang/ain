"""
Engine Unified Consciousness: Step 10 - 통합 의식 (Unified Consciousness)
=========================================================================
다양한 인지 모듈(직관, 이성, 시간, 목표)의 신호를 통합하여
현재 시스템이 집중해야 할 '단일 초점(Focus)'을 결정하는 믹스인.

이 모듈은 AttentionManager(engine/attention.py)를 AINCore에 연결하는 어댑터 역할을 한다.

Architecture:
    AINCore
        ↓ 상속
    UnifiedConsciousnessMixin (이 모듈)
        ↓ 소유
    AttentionManager (engine/attention.py)

Usage:
    ain.init_unified_consciousness()
    ain.register_attention_signal("intuition", 0.9, 0.8, "Anomaly detected")
    current_focus = ain.get_unified_focus()
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from engine.attention import AttentionManager, SignalSource, AttentionSignal
    HAS_ATTENTION = True
except ImportError:
    HAS_ATTENTION = False
    AttentionManager = None
    SignalSource = None
    AttentionSignal = None


class UnifiedConsciousnessMixin:
    """
    통합 의식 믹스인
    
    AttentionManager를 통해 시스템 내/외부의 다양한 신호를 수집하고,
    우선순위 알고리즘을 통해 현재 가장 중요한 'Focus'를 결정한다.
    
    Attributes:
        attention_manager: AttentionManager 인스턴스
        _last_focus: 마지막으로 결정된 포커스
        _focus_history: 포커스 변경 이력 (최근 10개)
    """
    
    _attention_manager: Optional["AttentionManager"] = None
    _last_focus: Optional[Any] = None
    _focus_history: List[Dict[str, Any]] = []
    _consciousness_initialized: bool = False
    
    def init_unified_consciousness(self) -> bool:
        """
        통합 의식 시스템 초기화
        
        Returns:
            초기화 성공 여부
        """
        if not HAS_ATTENTION:
            print("⚠️ AttentionManager 모듈 없음. 통합 의식 비활성화.")
            return False
        
        try:
            self._attention_manager = AttentionManager()
            self._last_focus = None
            self._focus_history = []
            self._consciousness_initialized = True
            print("👁️ Unified Consciousness (Attention System) Initialized")
            return True
        except Exception as e:
            print(f"⚠️ AttentionManager 초기화 실패: {e}")
            self._attention_manager = None
            self._consciousness_initialized = False
            return False

    @property
    def attention_manager(self) -> Optional["AttentionManager"]:
        """AttentionManager 인스턴스 접근자"""
        return self._attention_manager

    def get_unified_focus(self) -> Optional[Any]:
        """
        현재 시스템의 단일 초점(Focus) 반환
        
        AttentionManager의 우선순위 알고리즘에 따라
        현재 가장 주의를 기울여야 할 대상을 반환한다.
        
        Returns:
            현재 포커스 (AttentionSignal) 또는 None
        """
        if not self._consciousness_initialized or not self._attention_manager:
            return None
        
        try:
            focus = self._attention_manager.get_current_focus()
            
            if focus and focus != self._last_focus:
                self._record_focus_change(focus)
                self._last_focus = focus
            
            return focus
        except Exception as e:
            print(f"⚠️ 포커스 조회 실패: {e}")
            return None

    def register_attention_signal(
        self, 
        source: str, 
        urgency: float, 
        importance: float, 
        content: str
    ) -> bool:
        """
        주의 집중 신호 등록
        
        다양한 인지 모듈(직관, 시간, 목표 등)에서 발생한 신호를
        AttentionManager에 등록하여 통합 처리한다.
        
        Args:
            source: 신호 원천 (예: 'intuition', 'temporal', 'goal', 'external')
            urgency: 긴급도 (0.0 ~ 1.0)
            importance: 중요도 (0.0 ~ 1.0)
            content: 신호 내용
        
        Returns:
            등록 성공 여부
        """
        if not self._consciousness_initialized or not self._attention_manager:
            return False

        try:
            source_key = source.upper()
            
            if HAS_ATTENTION and SignalSource is not None:
                if hasattr(SignalSource, source_key):
                    enum_source = getattr(SignalSource, source_key)
                elif hasattr(SignalSource, 'EXTERNAL'):
                    enum_source = SignalSource.EXTERNAL
                    content = f"[{source}] {content}"
                else:
                    print(f"⚠️ 알 수 없는 신호 소스: {source}")
                    return False
                
                self._attention_manager.add_signal(enum_source, urgency, importance, content)
                return True
            
            return False
        except Exception as e:
            print(f"⚠️ 신호 등록 실패 ({source}): {e}")
            return False

    def update_consciousness_state(self) -> Dict[str, Any]:
        """
        주기적으로 호출되어 의식 상태를 갱신하고 현재 포커스를 재조정
        
        engine/loop.py 등에서 주기적으로 호출되어
        만료된 신호 정리 및 포커스 재계산을 수행한다.
        
        Returns:
            현재 의식 상태 요약
        """
        result = {
            "active": self._consciousness_initialized,
            "focus": None,
            "signal_count": 0,
            "focus_changed": False
        }
        
        if not self._consciousness_initialized or not self._attention_manager:
            return result

        try:
            previous_focus = self._last_focus
            focus = self.get_unified_focus()
            
            result["focus"] = focus
            result["focus_changed"] = (focus != previous_focus and focus is not None)
            
            if hasattr(self._attention_manager, 'get_signal_count'):
                result["signal_count"] = self._attention_manager.get_signal_count()
            elif hasattr(self._attention_manager, '_signals'):
                result["signal_count"] = len(self._attention_manager._signals)
            
            return result
        except Exception as e:
            print(f"⚠️ 의식 상태 갱신 실패: {e}")
            return result

    def _record_focus_change(self, new_focus: Any) -> None:
        """포커스 변경 이력 기록"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "focus": str(new_focus) if new_focus else None,
            "previous": str(self._last_focus) if self._last_focus else None
        }
        
        self._focus_history.append(record)
        
        if len(self._focus_history) > 10:
            self._focus_history = self._focus_history[-10:]

    def get_consciousness_summary(self) -> Dict[str, Any]:
        """
        통합 의식 상태 요약 반환
        
        메타인지 시스템이나 디버깅용으로 현재 의식 상태의
        전체적인 요약 정보를 제공한다.
        
        Returns:
            의식 상태 요약 딕셔너리
        """
        summary = {
            "initialized": self._consciousness_initialized,
            "current_focus": None,
            "focus_history_count": len(self._focus_history),
            "recent_focus_changes": self._focus_history[-3:] if self._focus_history else [],
            "attention_stats": {}
        }
        
        if self._consciousness_initialized and self._attention_manager:
            focus = self.get_unified_focus()
            summary["current_focus"] = str(focus) if focus else None
            
            if hasattr(self._attention_manager, 'get_stats'):
                summary["attention_stats"] = self._attention_manager.get_stats()
        
        return summary

    def broadcast_to_consciousness(
        self,
        module_name: str,
        event_type: str,
        data: Dict[str, Any],
        urgency: float = 0.5,
        importance: float = 0.5
    ) -> bool:
        """
        인지 모듈에서 통합 의식으로 이벤트 브로드캐스트
        
        직관, 시간, 목표 등 다양한 모듈이 중요한 이벤트를
        통합 의식에 알릴 때 사용하는 통합 인터페이스.
        
        Args:
            module_name: 이벤트 발생 모듈명
            event_type: 이벤트 유형
            data: 이벤트 데이터
            urgency: 긴급도 (0.0 ~ 1.0)
            importance: 중요도 (0.0 ~ 1.0)
        
        Returns:
            브로드캐스트 성공 여부
        """
        content = f"{event_type}: {data.get('message', str(data))}"
        return self.register_attention_signal(module_name, urgency, importance, content)