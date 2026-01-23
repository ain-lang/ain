"""
Roadmap Step 완료 조건 정의 (SSOT)
파일/클래스 존재 여부로 Step 완료 판단

Step 7 ~ 11의 완료 조건을 추가하여 RoadmapChecker가
현재의 진화 상태(Meta-Cognition ~ Limitation Awareness)를 검증하고
자동으로 Roadmap을 업데이트할 수 있도록 한다.
"""

# Step 완료 조건 정의
STEP_COMPLETION_CRITERIA = {
    "step_4_vector_memory": {
        "name": "Vector Memory",
        "checks": [
            ("nexus/retrieval.py", "RetrievalMixin"),
            ("nexus/memory.py", "VectorMemory"),
        ],
        "next_step": "step_5_inner_monologue"
    },
    "step_5_inner_monologue": {
        "name": "Inner Monologue",
        "checks": [
            ("engine/consciousness.py", "ConsciousnessMixin"),
            ("engine/consciousness.py", "_inner_monologue"),
        ],
        "next_step": "step_6_intentionality"
    },
    "step_6_intentionality": {
        "name": "Intentionality",
        "checks": [
            ("engine/goal_manager.py", "GoalManagerMixin"),
            ("engine/__init__.py", "GoalManagerMixin"),
        ],
        "next_step": "step_7_meta_cognition"
    },
    "step_7_meta_cognition": {
        "name": "Meta-Cognition",
        "checks": [
            ("engine/meta_cognition.py", "MetaCognitionMixin"),
            ("engine/meta_controller.py", "MetaController"),
        ],
        "next_step": "step_8_intuition"
    },
    "step_8_intuition": {
        "name": "Intuition",
        "checks": [
            ("engine/intuition.py", "IntuitionMixin"),
            ("engine/decision_gate.py", "DecisionGate"),
        ],
        "next_step": "step_9_temporal_self"
    },
    "step_9_temporal_self": {
        "name": "Temporal Self",
        "checks": [
            ("engine/temporal.py", "TemporalAwarenessMixin"),
            ("engine/temporal_integration.py", "activate_temporal_awareness"),
        ],
        "next_step": "step_10_unified_consciousness"
    },
    "step_10_unified_consciousness": {
        "name": "Unified Consciousness",
        "checks": [
            ("engine/unified_consciousness.py", "UnifiedConsciousnessMixin"),
            ("engine/attention.py", "AttentionManager"),
        ],
        "next_step": "step_11_limitation_awareness"
    },
    "step_11_limitation_awareness": {
        "name": "Limitation Awareness",
        "checks": [
            ("engine/resource_monitor.py", "ResourceAwarenessMixin"),
            ("engine/resource_monitor.py", "ResourceStatus"),
        ],
        "next_step": "step_12_creativity"
    },
}


def get_step_criteria(step_id: str) -> dict:
    """
    특정 Step의 완료 조건을 반환한다.
    
    Args:
        step_id: Step 식별자 (예: "step_7_meta_cognition")
    
    Returns:
        해당 Step의 조건 딕셔너리. 없으면 빈 딕셔너리.
    """
    return STEP_COMPLETION_CRITERIA.get(step_id, {})


def get_all_step_ids() -> list:
    """
    정의된 모든 Step ID 목록을 반환한다.
    
    Returns:
        Step ID 문자열 리스트
    """
    return list(STEP_COMPLETION_CRITERIA.keys())


def get_next_step(current_step_id: str) -> str:
    """
    현재 Step의 다음 Step ID를 반환한다.
    
    Args:
        current_step_id: 현재 Step 식별자
    
    Returns:
        다음 Step ID. 정의되지 않았으면 빈 문자열.
    """
    criteria = STEP_COMPLETION_CRITERIA.get(current_step_id, {})
    return criteria.get("next_step", "")


def get_step_by_name(step_name: str) -> dict:
    """
    Step 이름으로 조건을 검색한다.
    
    Args:
        step_name: Step 이름 (예: "Meta-Cognition")
    
    Returns:
        해당 Step의 조건 딕셔너리. 없으면 빈 딕셔너리.
    """
    for step_id, criteria in STEP_COMPLETION_CRITERIA.items():
        if criteria.get("name") == step_name:
            return {"step_id": step_id, **criteria}
    return {}


def get_current_evolution_state() -> dict:
    """
    시스템의 현재 진화 상태를 요약하여 반환한다.
    RoadmapChecker가 이 정보를 기반으로 Roadmap을 동기화할 수 있다.
    
    Returns:
        {
            "total_steps": int,
            "step_ids": list,
            "step_names": list,
            "last_step": str
        }
    """
    step_ids = list(STEP_COMPLETION_CRITERIA.keys())
    step_names = [c["name"] for c in STEP_COMPLETION_CRITERIA.values()]
    
    return {
        "total_steps": len(STEP_COMPLETION_CRITERIA),
        "step_ids": step_ids,
        "step_names": step_names,
        "last_step": step_ids[-1] if step_ids else ""
    }