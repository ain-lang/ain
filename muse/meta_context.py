"""
Muse Meta Context: 메타인지 상태를 Dreamer 프롬프트용으로 변환
Step 7: Meta-Cognition - Dreamer Awareness

이 모듈은 FactCore에 저장된 'cognitive_state'를 읽어와
Dreamer(Muse)가 이해할 수 있는 텍스트 형식으로 변환한다.

Muse(Dreamer)는 이 컨텍스트를 통해 시스템의 현재 심리 상태(자신감, 전략 모드 등)를
인식하고, 그에 맞는 진화 전략을 수립할 수 있다.

Architecture:
    FactCore (cognitive_state)
        ↓
    MetaContextFormatter (이 모듈)
        ↓
    Dreamer Prompt (텍스트 주입)

Usage:
    from muse.meta_context import format_meta_cognitive_state, get_active_goal_context
    
    facts = fact_core.facts
    meta_text = format_meta_cognitive_state(facts)
    goal_text = get_active_goal_context(facts)
"""

from typing import Dict, Any, Optional
from datetime import datetime


def format_meta_cognitive_state(facts: Dict[str, Any]) -> str:
    """
    FactCore의 cognitive_state를 Dreamer용 프롬프트 텍스트로 변환한다.
    
    Args:
        facts: FactCore의 전체 팩트 딕셔너리
        
    Returns:
        포맷팅된 메타인지 상태 문자열
    """
    if not facts:
        return "[META-COGNITION] State: No facts available"
    
    state = facts.get("cognitive_state", {})
    if not state:
        return "[META-COGNITION] State: Initializing (No data yet)"
    
    strategy = state.get("strategy_mode", "NORMAL").upper()
    confidence = state.get("confidence_score", 0.5)
    health = state.get("cognitive_health", "UNKNOWN").upper()
    
    journal = state.get("meta_journal", [])
    latest_entry = journal[-1] if journal else {}
    latest_insight = latest_entry.get("insight", "None")
    
    if confidence >= 0.8:
        conf_level = "HIGH"
    elif confidence <= 0.3:
        conf_level = "LOW"
    else:
        conf_level = "MODERATE"
        
    last_update = state.get("last_update", "Unknown")
    if isinstance(last_update, (int, float)):
        try:
            last_update = datetime.fromtimestamp(last_update).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            last_update = "Invalid timestamp"

    lines = [
        "=== [META-COGNITIVE STATE] ===",
        f"Strategy Mode : {strategy}",
        f"Cognitive Health: {health}",
        f"Confidence     : {confidence:.2f} ({conf_level})",
        f"Latest Insight : {latest_insight}",
        f"Last Update    : {last_update}",
        "==============================",
        ""
    ]
    
    if strategy == "ACCELERATED":
        lines.append(">> TIP: Momentum is high. Propose bold and rapid evolutions.")
    elif strategy == "CAUTIOUS":
        lines.append(">> TIP: Confidence is low. Focus on stability, testing, and bug fixes.")
    elif strategy == "RECOVERY":
        lines.append(">> TIP: System is recovering. Prioritize self-healing and error resolution.")
    elif strategy == "CRITICAL":
        lines.append(">> TIP: System in critical state. Make minimal, safe changes only.")
        
    return "\n".join(lines)


def get_active_goal_context(facts: Dict[str, Any]) -> str:
    """
    현재 활성화된 목표(Goal) 정보를 간략히 추출한다.
    (Step 6: Intentionality 연동)
    
    Args:
        facts: FactCore의 전체 팩트 딕셔너리
        
    Returns:
        현재 목표 컨텍스트 문자열
    """
    if not facts:
        return "Current Focus: Unknown (No facts)"
    
    current_focus = facts.get("roadmap", {}).get("current_focus", "Unknown")
    
    goals_data = facts.get("active_goals", [])
    top_goal = goals_data[0] if goals_data else None
    
    lines = [
        f"Current Focus: {current_focus}"
    ]
    
    if top_goal:
        content = top_goal.get("content", "No active goal")
        priority = top_goal.get("priority", 0)
        lines.append(f"Top Priority Goal (P{priority}): {content}")
    else:
        lines.append("Top Priority Goal: None defined")
        
    return "\n".join(lines)


def get_full_meta_context(facts: Dict[str, Any]) -> str:
    """
    메타인지 상태와 목표 컨텍스트를 통합하여 반환한다.
    Dreamer 프롬프트에 주입하기 위한 완전한 메타 컨텍스트.
    
    Args:
        facts: FactCore의 전체 팩트 딕셔너리
        
    Returns:
        통합된 메타 컨텍스트 문자열
    """
    meta_state = format_meta_cognitive_state(facts)
    goal_context = get_active_goal_context(facts)
    
    return f"{meta_state}\n\n[ACTIVE GOALS]\n{goal_context}"