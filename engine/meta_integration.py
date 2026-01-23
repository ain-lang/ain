"""
Engine Meta Integration: 메타인지 시스템 활성화 어댑터
Step 7: Meta-Cognition - 메인 루프와 MetaController 연결

이 모듈은 engine/loop.py와 거대한 메타인지 시스템(MetaController, MetaEvaluator 등)
사이의 안전한 연결 고리 역할을 수행한다.

대형 파일(meta_controller.py 371줄)을 직접 수정하지 않고,
이 소형 어댑터를 통해 메타인지 시스템을 런타임에 연결한다.

Architecture:
    engine/loop.py (메인 루프)
        ↓ activate_meta_cognition() 호출
    meta_integration.py (이 모듈)
        ↓ MetaController 초기화
    MetaController (메타인지 오케스트레이터)
        ↓
    AINCore.meta_controller 속성에 할당

Usage:
    from engine.meta_integration import activate_meta_cognition, tick_meta_cognition
    
    # 부팅 시 활성화
    activate_meta_cognition(ain_core)
    
    # 루프 내 주기적 호출
    tick_meta_cognition(ain_core)
"""

import time
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from engine import AINCore


# 메타인지 사이클 주기 (초)
META_COGNITION_INTERVAL = 600  # 10분마다 메타인지 사이클 실행

# 마지막 메타인지 실행 시간 추적
_last_meta_tick_time: float = 0.0


def activate_meta_cognition(ain_core: "AINCore") -> bool:
    """
    메타인지 시스템을 안전하게 초기화하고 AINCore에 연결한다.
    
    이 함수는 engine/loop.py의 run_engine()에서 시스템 부팅 시 호출된다.
    MetaController가 이미 core.py에서 초기화되어 있으므로,
    여기서는 활성화 상태를 확인하고 로그를 출력한다.
    
    Args:
        ain_core: AINCore 인스턴스
    
    Returns:
        활성화 성공 여부
    """
    global _last_meta_tick_time
    
    try:
        # MetaController 존재 여부 확인 (core.py에서 이미 초기화됨)
        if hasattr(ain_core, 'meta_controller') and ain_core.meta_controller is not None:
            print("🧠 메타인지 시스템 활성화 확인 완료")
            print("   └─ MetaController 연결됨")
            print(f"   └─ 메타인지 주기: {META_COGNITION_INTERVAL}초 (10분)")
            
            # 초기 시간 설정
            _last_meta_tick_time = time.time()
            
            return True
        else:
            # MetaController가 없으면 동적으로 생성 시도
            print("⚠️ MetaController 미발견. 동적 초기화 시도...")
            
            try:
                from engine.meta_controller import MetaController
                ain_core.meta_controller = MetaController(ain_core)
                print("✅ MetaController 동적 초기화 성공")
                
                # Nexus에 등록
                if hasattr(ain_core, 'nexus'):
                    ain_core.nexus.register_module("MetaController", ain_core.meta_controller)
                
                _last_meta_tick_time = time.time()
                return True
                
            except ImportError as e:
                print(f"❌ MetaController 임포트 실패: {e}")
                return False
            except Exception as e:
                print(f"❌ MetaController 초기화 실패: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 메타인지 시스템 활성화 실패: {e}")
        return False


def tick_meta_cognition(ain_core: "AINCore") -> Optional[Dict[str, Any]]:
    """
    메타인지 사이클을 주기적으로 실행한다.
    
    이 함수는 engine/loop.py의 while 루프 내에서 매 틱마다 호출된다.
    내부적으로 시간을 체크하여 META_COGNITION_INTERVAL 간격으로만 실제 사이클을 실행한다.
    
    Args:
        ain_core: AINCore 인스턴스
    
    Returns:
        메타인지 사이클 결과 (실행되지 않았으면 None)
    """
    global _last_meta_tick_time
    
    try:
        # 시간 체크: 주기가 되지 않았으면 스킵
        current_time = time.time()
        elapsed = current_time - _last_meta_tick_time
        
        if elapsed < META_COGNITION_INTERVAL:
            return None
        
        # MetaController 존재 확인
        if not hasattr(ain_core, 'meta_controller') or ain_core.meta_controller is None:
            return None
        
        # 메타인지 사이클 실행
        print("🧠 메타인지 사이클 시작...")
        
        result = _execute_meta_cycle(ain_core)
        
        # 시간 갱신
        _last_meta_tick_time = current_time
        
        if result:
            _log_meta_result(result)
        
        return result
        
    except Exception as e:
        print(f"⚠️ 메타인지 틱 오류 (무시됨): {e}")
        return None


def _execute_meta_cycle(ain_core: "AINCore") -> Optional[Dict[str, Any]]:
    """
    실제 메타인지 사이클을 실행한다.
    
    MetaController.execute_cycle()을 호출하고 결과를 반환한다.
    """
    try:
        controller = ain_core.meta_controller
        
        # execute_cycle 메서드 존재 확인
        if hasattr(controller, 'execute_cycle'):
            result = controller.execute_cycle()
            return result
        else:
            # 대체: _reflect_on_thinking 직접 호출
            if hasattr(ain_core, '_reflect_on_thinking'):
                reflection = ain_core._reflect_on_thinking()
                return {
                    "source": "direct_reflection",
                    "reflection": reflection
                }
            return None
            
    except Exception as e:
        print(f"⚠️ 메타인지 사이클 실행 오류: {e}")
        return {"error": str(e)}


def _log_meta_result(result: Dict[str, Any]) -> None:
    """
    메타인지 결과를 간결하게 로깅한다.
    """
    if "error" in result:
        print(f"   └─ ⚠️ 오류 발생: {result['error']}")
        return
    
    strategy_mode = result.get("strategy_mode", "unknown")
    confidence = result.get("confidence_score", 0.0)
    
    print(f"   └─ 전략 모드: {strategy_mode}")
    print(f"   └─ 자신감 점수: {confidence:.2f}")
    
    # 전략 조정이 있었으면 로그
    if result.get("strategy_adjusted"):
        print(f"   └─ 🔄 전략 조정됨: {result.get('adjustment_reason', 'N/A')}")


def get_meta_status(ain_core: "AINCore") -> Dict[str, Any]:
    """
    현재 메타인지 시스템 상태를 반환한다.
    
    디버깅 및 상태 보고용.
    """
    global _last_meta_tick_time
    
    status = {
        "active": False,
        "last_tick": None,
        "next_tick_in": None,
        "controller_present": False
    }
    
    try:
        if hasattr(ain_core, 'meta_controller') and ain_core.meta_controller is not None:
            status["active"] = True
            status["controller_present"] = True
        
        if _last_meta_tick_time > 0:
            status["last_tick"] = _last_meta_tick_time
            elapsed = time.time() - _last_meta_tick_time
            remaining = max(0, META_COGNITION_INTERVAL - elapsed)
            status["next_tick_in"] = remaining
            
    except Exception:
        pass
    
    return status