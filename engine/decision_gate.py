"""
Engine Decision Gate: 인지 경로 중재자 (System 1 vs System 2)
Step 8: Intuition - Fast/Slow Path Arbitration

이 모듈은 현재 입력이나 상황에 대해 직관(Intuition)을 사용할지,
심층 추론(Evolution/Reasoning)을 사용할지 결정하고 실행 경로를 분기한다.

Architecture:
    AIN Loop
      ↓
    DecisionGate
      ├─> (High Confidence) -> ReflexExecutor (System 1)
      └─> (Low Confidence)  -> EvolutionMixin (System 2)
"""

import asyncio
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from engine import AINCore
    from engine.intuition import IntuitionResult

try:
    from engine.intuition import IntuitionStrength
    from engine.reflex_executor import ReflexExecutor
    HAS_INTUITION_COMPONENTS = True
except ImportError:
    HAS_INTUITION_COMPONENTS = False
    IntuitionStrength = None
    ReflexExecutor = None


class ExecutionPath(Enum):
    """실행 경로 열거형"""
    SYSTEM_1_REFLEX = "system_1_reflex"      # Fast, Intuitive, Low Cost (직관/반사)
    SYSTEM_2_EVOLUTION = "system_2_evolution" # Slow, Deliberate, High Cost (추론/진화)


class DecisionGate:
    """
    인지 판단 게이트
    
    직관의 강도와 시스템의 시간적 여유(Temporal State)를 고려하여
    실행 전략을 결정한다.
    """

    # System 1 선택을 위한 신뢰도 임계값
    CONFIDENCE_THRESHOLD = 0.85

    def __init__(self, core: "AINCore"):
        self.core = core
        self.reflex_executor = None
        
        if HAS_INTUITION_COMPONENTS and ReflexExecutor is not None:
            self.reflex_executor = ReflexExecutor(core)

    def decide_path(self, context_text: str) -> Tuple[ExecutionPath, Optional["IntuitionResult"]]:
        """
        주어진 컨텍스트에 대해 실행 경로(System 1 vs System 2)를 결정한다.
        
        Args:
            context_text: 판단할 상황 텍스트 (에러 로그, 사용자 입력 등)
            
        Returns:
            (선택된 경로, 직관 결과 객체 또는 None)
        """
        # 1. 안전 장치: 필수 컴포넌트 부재 시 System 2(진화/추론)를 기본값으로 사용
        if not HAS_INTUITION_COMPONENTS:
            return ExecutionPath.SYSTEM_2_EVOLUTION, None
        
        if not hasattr(self.core, "get_intuition"):
            return ExecutionPath.SYSTEM_2_EVOLUTION, None

        # 2. 직관(Intuition) 발생 - System 1 호출
        # Nexus의 기억을 바탕으로 빠른 패턴 매칭 수행
        intuition = self.core.get_intuition(context_text)
        
        if intuition is None:
            return ExecutionPath.SYSTEM_2_EVOLUTION, None
        
        # 3. 판단 로직 (Thresholding)
        # 직관이 '강함(STRONG)'이고 신뢰도가 임계값 이상인 경우 System 1 선택
        is_strong = intuition.strength == IntuitionStrength.STRONG
        is_confident = intuition.confidence >= self.CONFIDENCE_THRESHOLD
        
        # TODO: Temporal State(시간적 여유)도 고려할 수 있음 
        # 예: 급할 때는 낮은 신뢰도여도 System 1 시도
        
        if is_strong and is_confident:
            print(f"⚡ DecisionGate: System 1 (Reflex) selected. Confidence: {intuition.confidence:.2f}")
            return ExecutionPath.SYSTEM_1_REFLEX, intuition
            
        # 기본값: System 2 (Evolution)
        # 직관이 약하거나 불확실하면 Dreamer를 통한 심층 추론 수행
        print(f"🧠 DecisionGate: System 2 (Evolution) selected. Confidence: {intuition.confidence:.2f}")
        return ExecutionPath.SYSTEM_2_EVOLUTION, intuition

    async def execute_reflex_if_possible(
        self, 
        intuition: "IntuitionResult", 
        context: Dict[str, Any]
    ) -> bool:
        """
        System 1 경로가 선택되었을 때, 반사 행동을 실행한다.
        
        Args:
            intuition: 직관 결과 객체
            context: 실행 컨텍스트 (query, metadata 등)
            
        Returns:
            실행 성공 여부 (True면 System 2 스킵 가능)
        """
        if self.reflex_executor is None:
            print("⚠️ DecisionGate: ReflexExecutor 없음. System 2로 전환.")
            return False
        
        try:
            success = await self.reflex_executor.try_execute_reflex(intuition, context)
            
            if success:
                print(f"✅ DecisionGate: 반사 행동 성공 - {intuition.pattern_match}")
                return True
            else:
                print("⚠️ DecisionGate: 반사 행동 실패 → System 2로 전환")
                return False
                
        except Exception as e:
            print(f"❌ DecisionGate: 반사 행동 예외 발생: {e}")
            return False

    async def process_decision(self, user_query: str = None) -> Dict[str, Any]:
        """
        상황을 판단하고 실행 경로를 결정/실행한다.
        
        기존 인터페이스와의 하위 호환성을 유지하면서
        decide_path()와 execute_reflex_if_possible()을 통합 호출한다.

        Args:
            user_query: 사용자 쿼리 또는 현재 상황 설명
            
        Returns:
            Dict: {
                "path": "reflex" | "reasoning",
                "executed": bool,
                "result": Any,
                "confidence": float
            }
        """
        context_key = user_query if user_query else "system_idle_state"
        
        # 1. 경로 결정
        path, intuition = self.decide_path(context_key)
        
        result = {
            "path": "reasoning",
            "executed": False,
            "result": None,
            "confidence": 0.0
        }
        
        if intuition is not None:
            result["confidence"] = intuition.confidence
        
        # 2. System 1 경로인 경우 반사 행동 시도
        if path == ExecutionPath.SYSTEM_1_REFLEX and intuition is not None:
            success = await self.execute_reflex_if_possible(
                intuition, 
                {"query": user_query}
            )
            
            if success:
                result["path"] = "reflex"
                result["executed"] = True
                result["result"] = f"Reflex Action Executed: {intuition.pattern_match}"
                return result
        
        # 3. System 2 경로 또는 System 1 실패 시
        result["path"] = "reasoning"
        return result