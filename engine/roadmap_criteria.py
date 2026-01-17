"""
Roadmap Step 완료 조건 정의 (SSOT)
파일/클래스 존재 여부로 Step 완료 판단
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
            ("engine/goal_executor.py", "GoalExecutor"),
        ],
        "next_step": "step_7_meta_cognition"
    },
    "step_7_meta_cognition": {
        "name": "Meta-Cognition",
        "checks": [
            ("engine/meta_cognition.py", "MetaCognitionMixin"),
        ],
        "next_step": "step_8_intuition"
    },
}
