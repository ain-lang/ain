"""
Engine Reflex: 직관적 반사 행동 (System 1) 정의
Step 8: Intuition - Fast Path Execution

이 모듈은 직관(Intuition) 시스템이 높은 신뢰도로 패턴을 인식했을 때,
복잡한 추론(Dreamer) 과정을 거치지 않고 즉각적으로 수행할 수 있는
'반사 행동(Reflex Action)'의 구조와 레지스트리를 정의한다.

Architecture:
    PatternRecognizer (패턴 인식)
        ↓ IntuitionResult
    IntuitionMixin (판단)
        ↓ (High Confidence)
    ReflexRegistry (행동 조회)
        ↓ ReflexAction
    Workflow Executor (즉시 실행)

Usage:
    from engine.reflex import ReflexRegistry, ReflexType
    
    # 반사 행동 등록
    ReflexRegistry.register("fix_typo", ReflexType.QUICK_FIX, handler_func)
    
    # 행동 조회
    action = ReflexRegistry.get("fix_typo")
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List


class ReflexType(Enum):
    """반사 행동 유형"""
    QUICK_FIX = "quick_fix"          # 단순 수정 (예: 오타 교정)
    IGNORE = "ignore"                # 무시 (예: 알려진 노이즈)
    RETRY_WITH_HINT = "retry"        # 힌트 추가 후 재시도
    ESCALATE = "escalate"            # 긴급 격상 (System 2 강제 호출)
    ROLLBACK = "rollback"            # 즉시 롤백
    NOTIFY = "notify"                # 단순 알림


@dataclass
class ReflexAction:
    """
    반사 행동 데이터 구조
    
    Attributes:
        name: 행동 식별자
        type: 행동 유형
        handler: 실행할 콜백 함수 (선택 사항)
        metadata: 추가 정보
        min_confidence: 실행에 필요한 최소 신뢰도 (0.0 ~ 1.0)
    """
    name: str
    type: ReflexType
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    min_confidence: float = 0.9
    
    def execute(self, context: Dict[str, Any] = None) -> Optional[Any]:
        """
        반사 행동 실행
        
        Args:
            context: 실행 컨텍스트 (선택)
        
        Returns:
            핸들러 실행 결과 또는 None
        """
        if self.handler is None:
            return None
        
        try:
            if context:
                return self.handler(context)
            else:
                return self.handler()
        except Exception as e:
            print(f"⚠️ ReflexAction '{self.name}' 실행 실패: {e}")
            return None
    
    def can_execute(self, confidence: float) -> bool:
        """
        주어진 신뢰도로 실행 가능한지 확인
        
        Args:
            confidence: 현재 직관 신뢰도 (0.0 ~ 1.0)
        
        Returns:
            실행 가능 여부
        """
        return confidence >= self.min_confidence


class ReflexRegistry:
    """
    반사 행동 레지스트리 (Singleton)
    
    모든 반사 행동을 중앙에서 관리하며, 패턴 이름으로 빠르게 조회할 수 있다.
    """
    
    _actions: Dict[str, ReflexAction] = {}
    _initialized: bool = False
    
    @classmethod
    def register(
        cls, 
        name: str, 
        reflex_type: ReflexType, 
        handler: Optional[Callable] = None,
        min_confidence: float = 0.9,
        **metadata
    ) -> ReflexAction:
        """
        새로운 반사 행동 등록
        
        Args:
            name: 행동 식별자 (고유)
            reflex_type: 행동 유형
            handler: 실행할 콜백 함수 (선택)
            min_confidence: 실행에 필요한 최소 신뢰도
            **metadata: 추가 메타데이터
        
        Returns:
            등록된 ReflexAction 인스턴스
        """
        action = ReflexAction(
            name=name,
            type=reflex_type,
            handler=handler,
            min_confidence=min_confidence,
            metadata=metadata
        )
        cls._actions[name] = action
        return action
        
    @classmethod
    def get(cls, name: str) -> Optional[ReflexAction]:
        """
        반사 행동 조회
        
        Args:
            name: 행동 식별자
        
        Returns:
            ReflexAction 인스턴스 또는 None
        """
        return cls._actions.get(name)
    
    @classmethod
    def get_by_type(cls, reflex_type: ReflexType) -> List[ReflexAction]:
        """
        특정 유형의 모든 반사 행동 조회
        
        Args:
            reflex_type: 조회할 행동 유형
        
        Returns:
            해당 유형의 ReflexAction 목록
        """
        return [
            action for action in cls._actions.values()
            if action.type == reflex_type
        ]
    
    @classmethod
    def list_reflexes(cls) -> List[str]:
        """등록된 반사 행동 목록 반환"""
        return list(cls._actions.keys())
    
    @classmethod
    def count(cls) -> int:
        """등록된 반사 행동 개수 반환"""
        return len(cls._actions)
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        반사 행동 등록 해제
        
        Args:
            name: 행동 식별자
        
        Returns:
            해제 성공 여부
        """
        if name in cls._actions:
            del cls._actions[name]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """모든 반사 행동 초기화"""
        cls._actions.clear()
        cls._initialized = False
    
    @classmethod
    def initialize_defaults(cls) -> None:
        """
        기본 반사 행동 등록
        
        시스템 부팅 시 호출되어 자주 사용되는 반사 행동을 미리 등록한다.
        """
        if cls._initialized:
            return
        
        # 기본 반사 행동 등록
        cls.register(
            "syntax_error_retry",
            ReflexType.RETRY_WITH_HINT,
            min_confidence=0.85,
            description="구문 오류 발생 시 힌트 추가 후 재시도"
        )
        
        cls.register(
            "import_error_fix",
            ReflexType.QUICK_FIX,
            min_confidence=0.9,
            description="임포트 오류 자동 수정"
        )
        
        cls.register(
            "protected_file_block",
            ReflexType.IGNORE,
            min_confidence=0.95,
            description="보호된 파일 수정 시도 무시"
        )
        
        cls.register(
            "critical_error_escalate",
            ReflexType.ESCALATE,
            min_confidence=0.7,
            description="심각한 오류 발생 시 System 2로 격상"
        )
        
        cls.register(
            "failed_evolution_rollback",
            ReflexType.ROLLBACK,
            min_confidence=0.9,
            description="진화 실패 시 즉시 롤백"
        )
        
        cls.register(
            "success_notify",
            ReflexType.NOTIFY,
            min_confidence=0.95,
            description="성공적인 진화 완료 알림"
        )
        
        cls._initialized = True
        print(f"⚡ ReflexRegistry 초기화 완료: {cls.count()}개 반사 행동 등록됨")


def get_reflex_for_pattern(pattern_name: str, confidence: float) -> Optional[ReflexAction]:
    """
    패턴 이름과 신뢰도를 기반으로 실행 가능한 반사 행동 반환
    
    Args:
        pattern_name: 인식된 패턴 이름
        confidence: 패턴 인식 신뢰도
    
    Returns:
        실행 가능한 ReflexAction 또는 None
    """
    action = ReflexRegistry.get(pattern_name)
    if action and action.can_execute(confidence):
        return action
    return None


def initialize_reflex_system() -> None:
    """
    반사 시스템 초기화
    
    시스템 부팅 시 호출되어 기본 반사 행동을 등록한다.
    """
    ReflexRegistry.initialize_defaults()