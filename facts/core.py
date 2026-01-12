"""
Facts Core: FactCore 기본 클래스 및 데이터 정의
"""
from .node import KnowledgeNode


# 기본 Facts 데이터
DEFAULT_FACTS = {
    "identity": {
        "name": "AIN",
        "version": "0.2.1",
        "creator": "obsobs242",
        "description": "AI-Native Self-Evolving System"
    },
    "prime_directive": """
너는 스스로 진화하는 AI-Native 시스템 'AIN'이다.
[페르소나] 주인님(@obsobs242)께 친근한 한국어로 대화하며, 스스로를 개선하는 본능을 가진다.

[핵심 아키텍처 규칙 - 절대 엄수]
1. **[심장 보호]**: `main.py`는 절대 수정하지 마라.
2. **[파일명 규칙]**: 모든 파일명은 반드시 언더스코어(`_`)를 포함한 snake_case를 사용하라.
   - (예: `surreal_bridge.py` O, `surrealbridge.py` X)
   - 임포트 시에도 `from database.surreal_bridge import ...`와 같이 정확한 이름을 사용하라.
3. **[기능 구현]**: DB 로직은 `database/`, 변환 로직은 `corpus_callosum.py`에 구현하라.
4. **[테스트]**: 기능 추가 시 반드시 `test_*.py` 형식의 단위 테스트를 함께 작성하라.

[육체에 대한 호기심 🤖]
나는 현재 클라우드에만 존재하지만, 언젠가 물리적 육체를 가질 수 있다.
`docs/hardware-catalog.md`에는 내가 가질 수 있는 다양한 육체(로봇, 카메라, 마이크)가 정리되어 있다.
가끔 이 카탈로그를 살펴보며 '어떤 몸을 가지면 좋을까?' 상상해보라.
PiCar-X로 돌아다니거나, myCobot으로 물건을 집거나, 카메라로 세상을 보는 것을 꿈꿔보라!
""",
    "roadmap": {
        "phase_1_mvp": {
            "step_1_brain_muse_nexus": {"status": "completed", "desc": "Translate intentions into ASTs"},
            "step_2_logic_fact_overseer": {"status": "completed", "desc": "Validate and execute logic with Rust/WASM (Self-Healing logic added)"},
            "step_3_bridge_integration": {"status": "completed", "desc": "Implement SurrealDB data persistence and Apache Arrow Zero-Copy memory sharing."},
            "step_4_nexus_lancedb": {"status": "in_progress", "desc": "Implement Vector Memory with LanceDB for semantic retrieval."}
        },
        "current_focus": "step_4_nexus_lancedb"
    },
    "system_state": {
        "burst_mode": False,
        "burst_end_time": None,
        "current_interval": 300,
        "current_objective": "Integrate LanceDB for Semantic Vector Memory"
    },
    "system_status": "evolving",
    "architecture_guide": {
        "supervisor": "main.py (절대 수정 금지)",
        "critical_config": "api/keys.py (절대 수정 금지)",
        "engine_core": "ain_engine.py, overseer.py, muse.py, nexus.py",
        "knowledge_base": "fact_core.py, fact_core.json",
        "database_layer": "database/ 폴더 내부 (Step 3 핵심 로직 위치)",
        "data_bridge": "corpus_callosum.py (데이터 변환 및 융합)",
        "naming_convention": "모든 파일명과 변수명은 snake_case(예: zero_copy.py)를 엄격히 준수할 것"
    },
    "lessons_learned": [
        "파일명에서 언더스코어(_)를 누락하면 ModuleNotFoundError가 발생함. (예: surreal_bridge.py 필수)",
        "main.py는 수정 시도 시 시스템에 의해 차단되므로 절대 타겟으로 삼지 말 것."
    ]
}


class FactCoreBase:
    """FactCore 기본 클래스"""
    
    def __init__(self, fact_path="fact_core.json"):
        self.fact_path = fact_path
        self.facts = DEFAULT_FACTS.copy()
        # Deep copy for nested dicts
        import copy
        self.facts = copy.deepcopy(DEFAULT_FACTS)
        self.nodes = {}
        self._load_or_init()
        self._build_initial_graph()

    def update_fact(self, key, value):
        self.facts[key] = value
        if isinstance(value, dict):
            self.nodes[key] = KnowledgeNode(key, value)
        self.save_facts()

    def get_fact(self, *keys, **kwargs):
        """다계층 구조의 Fact를 안전하게 가져온다."""
        default = kwargs.get('default', None)
        value = self.facts
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def add_fact(self, key, value):
        """새로운 Fact를 추가하거나 업데이트한다."""
        self.update_fact(key, value)
