"""
Engine Meta Controller: 메타인지 주기 실행 및 전략 적용 컨트롤러
Step 7: Meta-Cognition - 메타인지 사이클 조율 및 시스템 파라미터 반영

이 모듈은 AINCore 인스턴스를 받아 메타인지 사이클을 실행하고,
그 결과를 시스템 설정(진화 주기, 버스트 모드 등)에 반영하며,
자아 성찰 내용을 벡터 메모리에 영구 저장하는 역할을 담당한다.

대형 파일인 meta_cognition.py, loop.py를 직접 수정하지 않고,
이 컨트롤러를 통해 메타인지 기능을 시스템에 연결한다.

Architecture:
    AINCore (engine/__init__.py)
        ↓ MetaController 인스턴스 생성
    MetaController (이 모듈)
        ↓ execute_cycle() 호출
    MetaCognitionMixin._reflect_on_thinking() (평가)
        ↓
    StrategyAdapter (전략 결정)
        ↓
    VectorMemory (성찰 저장)

Usage:
    from engine.meta_controller import MetaController
    
    controller = MetaController(ain_core)
    result = controller.execute_cycle()
    print(result["strategy_mode"])
"""

from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine import AINCore

try:
    from engine.strategy_adapter import StrategyAdapter, StrategyMode
    HAS_STRATEGY_ADAPTER = True
except ImportError:
    HAS_STRATEGY_ADAPTER = False
    StrategyMode = None


class MetaController:
    """
    메타인지 컨트롤러
    
    AINCore의 메타인지 기능을 조율하고, 평가 결과를 시스템에 반영한다.
    
    Responsibilities:
    1. 실행(Trigger): core._reflect_on_thinking() 호출
    2. 저장(Persist): 성찰 결과를 VectorMemory에 저장
    3. 적용(Enforce): StrategyMode에 따라 시스템 파라미터 조정
    
    Attributes:
        core: AINCore 인스턴스 참조
        strategy_adapter: 전략 결정 모듈
        last_cycle_time: 마지막 사이클 실행 시각
    """
    
    DEFAULT_INTERVAL = 3600  # 기본 진화 주기 (1시간)
    ACCELERATED_INTERVAL = 1800  # 가속 모드 주기 (30분)
    CONSERVATIVE_INTERVAL = 7200  # 보수 모드 주기 (2시간)
    
    def __init__(self, core: "AINCore"):
        """
        MetaController 초기화
        
        Args:
            core: AINCore 인스턴스 (MetaCognitionMixin 포함)
        """
        self.core = core
        self.strategy_adapter = StrategyAdapter() if HAS_STRATEGY_ADAPTER else None
        self.last_cycle_time: Optional[datetime] = None
        self._cycle_count = 0
        
        print("🧠 MetaController 초기화 완료")
    
    def execute_cycle(self) -> Dict[str, Any]:
        """
        메타인지 사이클 실행
        
        1. core._reflect_on_thinking() 호출하여 성찰 수행
        2. 성찰 결과를 VectorMemory에 저장
        3. StrategyMode에 따라 시스템 파라미터 조정
        
        Returns:
            사이클 실행 결과 딕셔너리:
            {
                "success": bool,
                "reflection": Dict (성찰 결과),
                "strategy_mode": str (적용된 전략 모드),
                "params_updated": Dict (변경된 파라미터),
                "persisted": bool (저장 성공 여부),
                "error": Optional[str]
            }
        """
        result = {
            "success": False,
            "reflection": {},
            "strategy_mode": "unknown",
            "params_updated": {},
            "persisted": False,
            "error": None,
            "cycle_number": self._cycle_count + 1
        }
        
        try:
            self._cycle_count += 1
            self.last_cycle_time = datetime.now()
            
            # 1. 메타인지 성찰 수행
            reflection = self._perform_reflection()
            result["reflection"] = reflection
            
            if not reflection:
                result["error"] = "성찰 결과가 비어있음"
                return result
            
            # 2. 전략 모드 결정 및 적용
            strategy_result = self._determine_and_apply_strategy(reflection)
            result["strategy_mode"] = strategy_result.get("mode", "unknown")
            result["params_updated"] = strategy_result.get("params", {})
            
            # 3. 성찰 내용 영구 저장
            persisted = self._persist_reflection(reflection)
            result["persisted"] = persisted
            
            result["success"] = True
            print(f"🧠 메타인지 사이클 #{self._cycle_count} 완료: {result['strategy_mode']}")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 메타인지 사이클 실패: {e}")
        
        return result
    
    def _perform_reflection(self) -> Dict[str, Any]:
        """
        core의 메타인지 기능을 호출하여 성찰 수행
        
        Returns:
            성찰 결과 딕셔너리
        """
        if not hasattr(self.core, '_reflect_on_thinking'):
            print("⚠️ core에 _reflect_on_thinking 메서드 없음")
            return {}
        
        try:
            reflection = self.core._reflect_on_thinking()
            return reflection if isinstance(reflection, dict) else {}
        except Exception as e:
            print(f"⚠️ 성찰 수행 중 오류: {e}")
            return {}
    
    def _determine_and_apply_strategy(self, reflection: Dict[str, Any]) -> Dict[str, Any]:
        """
        성찰 결과를 기반으로 전략 모드 결정 및 시스템 파라미터 적용
        
        Args:
            reflection: 성찰 결과 딕셔너리
        
        Returns:
            적용된 전략 정보 {"mode": str, "params": Dict}
        """
        result = {"mode": "normal", "params": {}}
        
        if not self.strategy_adapter:
            print("⚠️ StrategyAdapter 없음, 기본 모드 유지")
            return result
        
        try:
            # 성찰 결과에서 평가 지표 추출
            efficacy_score = reflection.get("efficacy_score", 0.5)
            error_count = reflection.get("error_count", 0)
            complexity = reflection.get("complexity", "medium")
            
            # StrategyAdapter를 통해 모드 결정
            mode = self.strategy_adapter.evaluate_mode(
                efficacy_score=efficacy_score,
                error_count=error_count,
                complexity=complexity
            )
            
            # 튜닝 파라미터 획득
            params = self.strategy_adapter.get_tuning_params(mode)
            
            # 시스템 파라미터 적용
            applied_params = self._apply_strategy(mode, params)
            
            result["mode"] = mode.value if hasattr(mode, 'value') else str(mode)
            result["params"] = applied_params
            
        except Exception as e:
            print(f"⚠️ 전략 결정 중 오류: {e}")
        
        return result
    
    def _apply_strategy(self, mode, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        StrategyMode에 따라 시스템 변수 조정
        
        Args:
            mode: StrategyMode 열거형 값
            params: 튜닝 파라미터 딕셔너리
        
        Returns:
            실제 적용된 파라미터
        """
        applied = {}
        
        try:
            mode_value = mode.value if hasattr(mode, 'value') else str(mode)
            
            # 진화 주기 조정
            if hasattr(self.core, 'current_interval'):
                if mode_value == "accelerated":
                    new_interval = self.ACCELERATED_INTERVAL
                elif mode_value == "conservative":
                    new_interval = self.CONSERVATIVE_INTERVAL
                else:
                    new_interval = self.DEFAULT_INTERVAL
                
                old_interval = getattr(self.core, 'current_interval', self.DEFAULT_INTERVAL)
                if old_interval != new_interval:
                    self.core.current_interval = new_interval
                    applied["interval"] = {"old": old_interval, "new": new_interval}
                    print(f"⏱️ 진화 주기 조정: {old_interval}s → {new_interval}s")
            
            # 버스트 모드 조정
            if hasattr(self.core, 'burst_mode'):
                should_burst = mode_value == "accelerated"
                if self.core.burst_mode != should_burst:
                    self.core.burst_mode = should_burst
                    applied["burst_mode"] = should_burst
                    print(f"🔥 버스트 모드: {should_burst}")
            
        except Exception as e:
            print(f"⚠️ 전략 적용 중 오류: {e}")
        
        return applied
    
    def _persist_reflection(self, reflection: Dict[str, Any]) -> bool:
        """
        성찰 내용을 Nexus VectorMemory에 영구 저장
        
        Args:
            reflection: 저장할 성찰 결과
        
        Returns:
            저장 성공 여부
        """
        try:
            # Nexus의 vector_memory 존재 여부 확인
            if not hasattr(self.core, 'nexus'):
                print("⚠️ core.nexus 없음, 저장 스킵")
                return False
            
            nexus = self.core.nexus
            
            if not hasattr(nexus, 'vector_memory'):
                print("⚠️ nexus.vector_memory 없음, 저장 스킵")
                return False
            
            vector_memory = nexus.vector_memory
            
            # 저장할 텍스트 구성
            reflection_text = self._format_reflection_for_storage(reflection)
            
            if not reflection_text:
                return False
            
            # 임베딩 생성 및 저장
            if hasattr(vector_memory, 'text_to_embedding') and hasattr(vector_memory, 'store'):
                embedding = vector_memory.text_to_embedding(reflection_text)
                success = vector_memory.store(
                    text=reflection_text,
                    vector=embedding,
                    memory_type="meta_reflection",
                    source="meta_controller",
                    metadata={
                        "cycle_number": self._cycle_count,
                        "timestamp": datetime.now().isoformat(),
                        "efficacy_score": reflection.get("efficacy_score"),
                        "strategy_mode": reflection.get("strategy_mode")
                    }
                )
                if success:
                    print(f"💾 메타인지 성찰 저장 완료 (cycle #{self._cycle_count})")
                return success
            
            # 대안: store_semantic_memory 메서드 사용
            if hasattr(nexus, 'store_semantic_memory'):
                success = nexus.store_semantic_memory(
                    text=reflection_text,
                    memory_type="meta_reflection",
                    source="meta_controller"
                )
                if success:
                    print(f"💾 메타인지 성찰 저장 완료 (cycle #{self._cycle_count})")
                return success
            
            print("⚠️ 적절한 저장 메서드 없음")
            return False
            
        except Exception as e:
            print(f"⚠️ 성찰 저장 중 오류: {e}")
            return False
    
    def _format_reflection_for_storage(self, reflection: Dict[str, Any]) -> str:
        """
        성찰 결과를 저장용 텍스트로 포맷팅
        
        Args:
            reflection: 성찰 결과 딕셔너리
        
        Returns:
            저장용 텍스트 문자열
        """
        parts = [f"[메타인지 성찰 #{self._cycle_count}]"]
        
        if "patterns" in reflection:
            parts.append(f"패턴: {reflection['patterns']}")
        
        if "biases" in reflection:
            parts.append(f"편향: {reflection['biases']}")
        
        if "improvements" in reflection:
            parts.append(f"개선점: {reflection['improvements']}")
        
        if "efficacy_score" in reflection:
            parts.append(f"효율성 점수: {reflection['efficacy_score']}")
        
        if "strategy_mode" in reflection:
            parts.append(f"전략 모드: {reflection['strategy_mode']}")
        
        if "reasoning" in reflection:
            parts.append(f"추론: {reflection['reasoning']}")
        
        return " | ".join(parts) if len(parts) > 1 else ""
    
    def get_status(self) -> Dict[str, Any]:
        """
        현재 컨트롤러 상태 반환
        
        Returns:
            상태 정보 딕셔너리
        """
        return {
            "cycle_count": self._cycle_count,
            "last_cycle_time": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "strategy_adapter_available": HAS_STRATEGY_ADAPTER,
            "core_has_reflect": hasattr(self.core, '_reflect_on_thinking') if self.core else False,
            "nexus_has_vector_memory": (
                hasattr(self.core, 'nexus') and 
                hasattr(self.core.nexus, 'vector_memory')
            ) if self.core else False
        }


def get_meta_controller(core: "AINCore") -> MetaController:
    """
    MetaController 인스턴스 팩토리 함수
    
    Args:
        core: AINCore 인스턴스
    
    Returns:
        MetaController 인스턴스
    """
    return MetaController(core)