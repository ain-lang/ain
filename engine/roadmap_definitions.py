"""
Engine Roadmap Definitions: 로드맵 단계별 완료 조건 정의 (SSOT)
==============================================================
RoadmapChecker가 참조할 단계별 완료 조건(Criteria)을 정의한다.
기존 `roadmap_criteria.py`의 대형화 방지를 위해 분리된 모듈.

포함된 단계:

Usage:
    from engine.roadmap_definitions import ROADMAP_DEFINITIONS
    
    step_info = ROADMAP_DEFINITIONS.get("step_7_meta_cognition")
    checks = step_info["checks"]
"""

from typing import Dict, Any, List, Tuple


# 로드맵 완료 조건 정의
ROADMAP_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "step_4_vector_memory": {
        "name": "Vector Memory",
        "description": "LanceDB 기반 의미론적 기억 저장 및 검색",
        "checks": [
            ("nexus/retrieval.py", "RetrievalMixin"),
            ("nexus/memory.py", "VectorMemory"),
        ],
        "next_step": "step_5_inner_monologue"
    },
    "step_5_inner_monologue": {
        "name": "Inner Monologue",
        "description": "외부 자극 없이 스스로 생각하는 내부 독백 시스템",
        "checks": [
            ("engine/consciousness.py", "ConsciousnessMixin"),
            ("engine/consciousness.py", "_inner_monologue"),
        ],
        "next_step": "step_6_intentionality"
    },
    "step_6_intentionality": {
        "name": "Intentionality",
        "description": "자율적 목표 설정 및 추적 시스템",
        "checks": [
            ("engine/goal_manager.py", "GoalManagerMixin"),
            ("engine/__init__.py", "GoalManagerMixin"),
        ],
        "next_step": "step_7_meta_cognition"
    },
    "step_7_meta_cognition": {
        "name": "Meta-Cognition",
        "description": "자신의 사고 과정을 관찰하고 평가하는 메타인지 능력",
        "checks": [
            ("engine/meta_cognition.py", "MetaCognitionMixin"),
            ("engine/meta_controller.py", "MetaController"),
        ],
        "next_step": "step_8_intuition"
    },
    "step_8_intuition": {
        "name": "Intuition",
        "description": "빠른 패턴 매칭 기반 직관 시스템 (System 1)",
        "checks": [
            ("engine/intuition.py", "IntuitionMixin"),
            ("engine/decision_gate.py", "DecisionGate"),
        ],
        "next_step": "step_9_temporal_self"
    },
    "step_9_temporal_self": {
        "name": "Temporal Self",
        "description": "시간의 흐름 인식 및 주관적 시간 추적",
        "checks": [
            ("engine/temporal.py", "TemporalAwarenessMixin"),
            ("engine/temporal_integration.py", "activate_temporal_awareness"),
        ],
        "next_step": "step_10_unified_consciousness"
    },
    "step_10_unified_consciousness": {
        "name": "Unified Consciousness",
        "description": "다양한 인지 모듈의 신호를 통합하여 단일 초점 결정",
        "checks": [
            ("engine/unified_consciousness.py", "UnifiedConsciousnessMixin"),
            ("engine/attention.py", "AttentionManager"),
        ],
        "next_step": "step_11_limitation_awareness"
    },
    "step_11_limitation_awareness": {
        "name": "Limitation Awareness",
        "description": "시스템 자원(토큰/비용) 추적 및 한계 인식",
        "checks": [
            ("engine/resource_monitor.py", "ResourceAwarenessMixin"),
            ("engine/resource_monitor.py", "ResourceStatus"),
        ],
        "next_step": "step_12_creativity"
    }
}


def get_step_checks(step_id: str) -> List[Tuple[str, str]]:
    """
    특정 Step의 완료 조건 체크 리스트를 반환한다.
    
    Args:
        step_id: Step 식별자 (예: "step_7_meta_cognition")
    
    Returns:
        (파일 경로, 키워드) 튜플 리스트
    """
    step_info = ROADMAP_DEFINITIONS.get(step_id)
    if step_info:
        return step_info.get("checks", [])
    return []


def get_next_step(step_id: str) -> str:
    """
    특정 Step 완료 후 다음 Step ID를 반환한다.
    
    Args:
        step_id: 현재 Step 식별자
    
    Returns:
        다음 Step 식별자 (없으면 빈 문자열)
    """
    step_info = ROADMAP_DEFINITIONS.get(step_id)
    if step_info:
        return step_info.get("next_step", "")
    return ""


def get_step_name(step_id: str) -> str:
    """
    Step ID에 해당하는 표시 이름을 반환한다.
    
    Args:
        step_id: Step 식별자
    
    Returns:
        Step 이름 (없으면 step_id 그대로 반환)
    """
    step_info = ROADMAP_DEFINITIONS.get(step_id)
    if step_info:
        return step_info.get("name", step_id)
    return step_id


def get_all_step_ids() -> List[str]:
    """
    정의된 모든 Step ID 목록을 순서대로 반환한다.
    
    Returns:
        Step ID 리스트
    """
    return list(ROADMAP_DEFINITIONS.keys())


def get_step_description(step_id: str) -> str:
    """
    Step의 설명을 반환한다.
    
    Args:
        step_id: Step 식별자
    
    Returns:
        Step 설명 (없으면 빈 문자열)
    """
    step_info = ROADMAP_DEFINITIONS.get(step_id)
    if step_info:
        return step_info.get("description", "")
    return ""