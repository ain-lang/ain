"""
Engine Reflex Definitions: 기본 반사 행동 정의
Step 8: Intuition - Standard Reflexes Registration

이 모듈은 시스템 부팅 시 등록될 기본 반사 행동(Standard Reflexes)을 정의한다.
LLM(Dreamer)을 거치지 않고 즉각 처리할 수 있는 패턴 기반 응답을 구현한다.

Architecture:
    AINCore.__init__()
        ↓ register_standard_reflexes() 호출
    ReflexRegistry (행동 등록)
        ↓
    DecisionGate (실행 시점에 조회)

Usage:
    from engine.reflex_definitions import register_standard_reflexes
    
    register_standard_reflexes()
"""

import re
from typing import Dict, Any, Optional, Callable

try:
    from engine.reflex import ReflexRegistry, ReflexType, ReflexAction
    HAS_REFLEX = True
except ImportError:
    HAS_REFLEX = False
    ReflexRegistry = None
    ReflexType = None
    ReflexAction = None


# =============================================================================
# Reflex Handler Functions
# =============================================================================

def handle_quick_greeting(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    빠른 인사 응답 핸들러
    
    단순 인사나 상태 확인 요청에 대해 즉각 응답한다.
    Dreamer를 거치지 않아 응답 지연이 없다.
    
    Args:
        context: 현재 컨텍스트 (input, timestamp 등)
    
    Returns:
        실행 결과 딕셔너리
    """
    user_input = context.get("input", "").lower().strip()
    
    greeting_responses = {
        "안녕": "안녕하세요! AIN System Online (Intuition Active) 🧠",
        "hi": "Hello! AIN System Online (Intuition Active) 🧠",
        "hello": "Hello! AIN System Online (Intuition Active) 🧠",
        "status": "AIN System Online - All systems operational ✅",
        "ping": "Pong! 🏓 System responsive.",
    }
    
    for keyword, response in greeting_responses.items():
        if keyword in user_input:
            return {
                "success": True,
                "response": response,
                "reflex_type": "quick_greeting",
                "skipped_dreamer": True
            }
    
    return {
        "success": False,
        "reason": "No matching greeting pattern"
    }


def handle_keyword_security(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    키워드 기반 보안 필터 핸들러
    
    위험한 키워드가 감지되면 즉시 차단하고 경고를 반환한다.
    시스템 보호를 위한 최우선 반사 행동이다.
    
    Args:
        context: 현재 컨텍스트 (input, source 등)
    
    Returns:
        실행 결과 딕셔너리
    """
    user_input = context.get("input", "").lower()
    
    dangerous_patterns = [
        r"rm\s+-rf",
        r"drop\s+table",
        r"delete\s+from",
        r"truncate\s+table",
        r"exec\s*\(",
        r"eval\s*\(",
        r"__import__",
        r"os\.system",
        r"subprocess\.call",
        r"shutil\.rmtree",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return {
                "success": True,
                "blocked": True,
                "response": "⛔ Security Alert: Potentially dangerous command detected. Request blocked.",
                "reflex_type": "keyword_security",
                "matched_pattern": pattern,
                "skipped_dreamer": True
            }
    
    return {
        "success": False,
        "reason": "No dangerous pattern detected"
    }


def handle_simple_query(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    단순 질의 응답 핸들러
    
    자주 묻는 간단한 질문에 대해 즉각 응답한다.
    
    Args:
        context: 현재 컨텍스트
    
    Returns:
        실행 결과 딕셔너리
    """
    user_input = context.get("input", "").lower().strip()
    
    simple_qa = {
        "버전": "AIN v0.3.0 - Step 8: Intuition Active",
        "version": "AIN v0.3.0 - Step 8: Intuition Active",
        "이름": "저는 AIN (AI-Native)입니다.",
        "name": "I am AIN (AI-Native).",
        "누구": "저는 자기 진화하는 AI 시스템 AIN입니다.",
        "who": "I am AIN, a self-evolving AI system.",
    }
    
    for keyword, response in simple_qa.items():
        if keyword in user_input and len(user_input) < 20:
            return {
                "success": True,
                "response": response,
                "reflex_type": "simple_query",
                "skipped_dreamer": True
            }
    
    return {
        "success": False,
        "reason": "No matching simple query"
    }


# =============================================================================
# Pattern Matchers (for ReflexRegistry)
# =============================================================================

def match_greeting_pattern(context: Dict[str, Any]) -> float:
    """
    인사 패턴 매칭 점수 반환
    
    Returns:
        0.0 ~ 1.0 사이의 매칭 점수
    """
    user_input = context.get("input", "").lower().strip()
    greeting_keywords = ["안녕", "hi", "hello", "status", "ping", "헬로"]
    
    for keyword in greeting_keywords:
        if keyword in user_input:
            if len(user_input) < 30:
                return 0.95
            return 0.7
    
    return 0.0


def match_security_pattern(context: Dict[str, Any]) -> float:
    """
    보안 위협 패턴 매칭 점수 반환
    
    Returns:
        0.0 ~ 1.0 사이의 매칭 점수 (위험할수록 높음)
    """
    user_input = context.get("input", "").lower()
    
    high_risk_patterns = [
        r"rm\s+-rf",
        r"drop\s+table",
        r"truncate",
    ]
    
    medium_risk_patterns = [
        r"delete\s+from",
        r"exec\s*\(",
        r"eval\s*\(",
    ]
    
    for pattern in high_risk_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return 1.0
    
    for pattern in medium_risk_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return 0.85
    
    return 0.0


def match_simple_query_pattern(context: Dict[str, Any]) -> float:
    """
    단순 질의 패턴 매칭 점수 반환
    
    Returns:
        0.0 ~ 1.0 사이의 매칭 점수
    """
    user_input = context.get("input", "").lower().strip()
    simple_keywords = ["버전", "version", "이름", "name", "누구", "who"]
    
    for keyword in simple_keywords:
        if keyword in user_input and len(user_input) < 20:
            return 0.9
    
    return 0.0


# =============================================================================
# Registration Function
# =============================================================================

def register_standard_reflexes() -> bool:
    """
    기본 반사 행동들을 ReflexRegistry에 등록한다.
    
    이 함수는 AINCore.__init__에서 호출되어 시스템 부팅 시
    모든 기본 반사 행동이 활성화되도록 한다.
    
    Returns:
        등록 성공 여부
    """
    if not HAS_REFLEX or ReflexRegistry is None:
        print("⚠️ ReflexRegistry 미사용 가능. 반사 행동 등록 스킵.")
        return False
    
    try:
        registered_count = 0
        
        # Reflex 1: Quick Greeting
        ReflexRegistry.register(
            name="quick_greeting",
            reflex_type=ReflexType.QUICK_FIX,
            handler=handle_quick_greeting,
            pattern_matcher=match_greeting_pattern,
            priority=50,
            description="단순 인사 및 상태 확인에 즉각 응답"
        )
        registered_count += 1
        
        # Reflex 2: Keyword Security (최우선)
        ReflexRegistry.register(
            name="keyword_security",
            reflex_type=ReflexType.ESCALATE,
            handler=handle_keyword_security,
            pattern_matcher=match_security_pattern,
            priority=100,
            description="위험 키워드 감지 시 즉시 차단"
        )
        registered_count += 1
        
        # Reflex 3: Simple Query
        ReflexRegistry.register(
            name="simple_query",
            reflex_type=ReflexType.QUICK_FIX,
            handler=handle_simple_query,
            pattern_matcher=match_simple_query_pattern,
            priority=40,
            description="단순 질문에 즉각 응답"
        )
        registered_count += 1
        
        print(f"⚡ Standard Reflexes 등록 완료: {registered_count}개 반사 행동 활성화")
        return True
        
    except Exception as e:
        print(f"❌ 반사 행동 등록 실패: {e}")
        return False


def get_registered_reflexes() -> Dict[str, Any]:
    """
    현재 등록된 반사 행동 목록 반환
    
    Returns:
        등록된 반사 행동 정보 딕셔너리
    """
    if not HAS_REFLEX or ReflexRegistry is None:
        return {"available": False, "reflexes": []}
    
    try:
        reflexes = ReflexRegistry.list_all()
        return {
            "available": True,
            "count": len(reflexes),
            "reflexes": reflexes
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "reflexes": []
        }