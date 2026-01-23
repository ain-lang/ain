"""
Engine Reflex Executor: 반사 행동 실행기
Step 8: Intuition - System 1 Action Executor

이 모듈은 직관(Intuition) 시스템이 감지한 패턴에 대해
등록된 반사 행동(Reflex Action)을 안전하게 실행하는 역할을 담당한다.

`engine/reflex.py`에 정의된 레지스트리와 `engine/intuition.py`의 판단 결과를 연결하여,
높은 신뢰도의 직관이 발생했을 때 Dreamer를 거치지 않고 즉각적인 대응을 가능하게 한다.

Architecture:
    IntuitionMixin (판단)
        ↓ IntuitionResult (Confidence: STRONG)
    ReflexExecutor (이 모듈)
        ↓ Action Lookup (ReflexRegistry)
    Callback Execution (즉시 실행)

Usage:
    from engine.reflex_executor import ReflexExecutor
    
    executor = ReflexExecutor(ain_core)
    executed = executor.try_execute_reflex(intuition_result, context)
    if executed:
        print("⚡ Reflex executed! Skipping Dreamer.")
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from engine import AINCore
    from engine.intuition import IntuitionResult

try:
    from engine.reflex import ReflexRegistry, ReflexType
    HAS_REFLEX_REGISTRY = True
except ImportError:
    HAS_REFLEX_REGISTRY = False
    ReflexRegistry = None
    ReflexType = None

try:
    from engine.intuition import IntuitionResult, IntuitionStrength
    HAS_INTUITION_DEF = True
except ImportError:
    HAS_INTUITION_DEF = False
    IntuitionStrength = None


class ReflexExecutionResult:
    """
    반사 행동 실행 결과 데이터 클래스
    
    Attributes:
        executed: 실행 여부
        action_key: 실행된 행동 키
        success: 행동 성공 여부
        message: 결과 메시지
        should_skip_dreamer: Dreamer 과정 스킵 여부
    """
    
    def __init__(
        self,
        executed: bool = False,
        action_key: Optional[str] = None,
        success: bool = False,
        message: str = "",
        should_skip_dreamer: bool = False
    ):
        self.executed = executed
        self.action_key = action_key
        self.success = success
        self.message = message
        self.should_skip_dreamer = should_skip_dreamer
    
    def __bool__(self) -> bool:
        return self.executed and self.success


class ReflexExecutor:
    """
    반사 행동 실행기
    
    직관적 판단(System 1)의 결과가 '강함(STRONG)'일 때,
    사전에 정의된 반사 행동을 찾아 즉시 실행한다.
    
    Attributes:
        core: AINCore 인스턴스 참조
        _execution_count: 총 실행 횟수
        _success_count: 성공 횟수
        _failure_count: 실패 횟수
    """

    def __init__(self, core: "AINCore"):
        self.core = core
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._last_execution_time: Optional[str] = None
        
        if not HAS_REFLEX_REGISTRY:
            print("⚠️ ReflexRegistry 모듈을 찾을 수 없습니다. 반사 실행 비활성화.")
        if not HAS_INTUITION_DEF:
            print("⚠️ Intuition 정의 모듈을 찾을 수 없습니다. 반사 실행 비활성화.")

    @property
    def is_available(self) -> bool:
        """반사 실행기 사용 가능 여부"""
        return HAS_REFLEX_REGISTRY and HAS_INTUITION_DEF

    def try_execute_reflex(
        self, 
        result: "IntuitionResult", 
        context: Dict[str, Any]
    ) -> ReflexExecutionResult:
        """
        직관 결과를 바탕으로 반사 행동 실행을 시도한다.

        Args:
            result: IntuitionMixin에서 반환된 직관 결과
            context: 행동 실행에 필요한 컨텍스트 데이터

        Returns:
            ReflexExecutionResult: 실행 결과 객체
        """
        if not self.is_available:
            return ReflexExecutionResult(
                executed=False,
                message="반사 실행기가 비활성화 상태입니다."
            )
        
        if result is None:
            return ReflexExecutionResult(
                executed=False,
                message="직관 결과가 없습니다."
            )

        if result.strength != IntuitionStrength.STRONG:
            return ReflexExecutionResult(
                executed=False,
                message=f"직관 강도가 충분하지 않습니다: {result.strength.value}"
            )

        pattern_key = result.pattern_match
        if not pattern_key:
            return ReflexExecutionResult(
                executed=False,
                message="매칭된 패턴이 없습니다."
            )

        action_func = ReflexRegistry.get(pattern_key)
        if action_func is None:
            return ReflexExecutionResult(
                executed=False,
                message=f"패턴 '{pattern_key}'에 대한 등록된 행동이 없습니다."
            )

        return self._execute_action(pattern_key, action_func, context, result.confidence)

    def _execute_action(
        self,
        pattern_key: str,
        action_func: Any,
        context: Dict[str, Any],
        confidence: float
    ) -> ReflexExecutionResult:
        """
        실제 반사 행동을 실행한다.
        
        Args:
            pattern_key: 패턴 키
            action_func: 실행할 함수
            context: 컨텍스트 데이터
            confidence: 직관 신뢰도
            
        Returns:
            ReflexExecutionResult: 실행 결과
        """
        from datetime import datetime
        
        self._execution_count += 1
        self._last_execution_time = datetime.now().isoformat()
        
        try:
            print(f"⚡ [System 1] 반사 행동 실행: {pattern_key} (신뢰도: {confidence:.2f})")
            
            success = action_func(self.core, context)
            
            if success:
                self._success_count += 1
                print(f"✅ [System 1] 반사 행동 성공: {pattern_key}")
                return ReflexExecutionResult(
                    executed=True,
                    action_key=pattern_key,
                    success=True,
                    message=f"반사 행동 '{pattern_key}' 성공적으로 실행됨",
                    should_skip_dreamer=True
                )
            else:
                self._failure_count += 1
                print(f"⚠️ [System 1] 반사 행동 실패 (False 반환): {pattern_key}")
                return ReflexExecutionResult(
                    executed=True,
                    action_key=pattern_key,
                    success=False,
                    message=f"반사 행동 '{pattern_key}'이 False를 반환함",
                    should_skip_dreamer=False
                )
            
        except Exception as e:
            self._failure_count += 1
            error_msg = f"반사 행동 실행 중 오류 발생 ({pattern_key}): {e}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return ReflexExecutionResult(
                executed=True,
                action_key=pattern_key,
                success=False,
                message=error_msg,
                should_skip_dreamer=False
            )

    def execute_by_key(
        self,
        action_key: str,
        context: Dict[str, Any]
    ) -> ReflexExecutionResult:
        """
        패턴 키로 직접 반사 행동을 실행한다.
        
        직관 판단 없이 특정 행동을 강제로 실행할 때 사용.
        
        Args:
            action_key: 실행할 행동의 키
            context: 컨텍스트 데이터
            
        Returns:
            ReflexExecutionResult: 실행 결과
        """
        if not self.is_available:
            return ReflexExecutionResult(
                executed=False,
                message="반사 실행기가 비활성화 상태입니다."
            )
        
        action_func = ReflexRegistry.get(action_key)
        if action_func is None:
            return ReflexExecutionResult(
                executed=False,
                message=f"행동 키 '{action_key}'가 등록되어 있지 않습니다."
            )
        
        return self._execute_action(action_key, action_func, context, 1.0)

    @property
    def stats(self) -> Dict[str, Any]:
        """실행 통계 반환"""
        success_rate = 0.0
        if self._execution_count > 0:
            success_rate = self._success_count / self._execution_count
        
        return {
            "total_executions": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": success_rate,
            "last_execution_time": self._last_execution_time,
            "is_available": self.is_available
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._last_execution_time = None


_executor_instance: Optional[ReflexExecutor] = None


def get_reflex_executor(core: "AINCore") -> ReflexExecutor:
    """
    ReflexExecutor 싱글톤 인스턴스를 반환한다.
    
    Args:
        core: AINCore 인스턴스
        
    Returns:
        ReflexExecutor 인스턴스
    """
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ReflexExecutor(core)
    return _executor_instance