import json
import os

try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

class KnowledgeNode:
    """지식 그래프의 단일 노드"""
    def __init__(self, label, data=None):
        self.label = label
        self.data = data if data else {}
        self.edges = [] # (relation, target_node_label)

    def add_edge(self, relation, target_label):
        self.edges.append((relation, target_label))

    def addedge(self, relation, target_label):
        """AIN의 오타 대응을 위한 별칭"""
        self.add_edge(relation, target_label)

    def __getattr__(self, name):
        """동적 메소드 매핑: 오타(예: addedge)를 정식 이름(add_edge)으로 연결"""
        mapping = {
            "addedge": self.add_edge,
            "to_dict": self.to_dict,
            "add_edge": self.add_edge
        }
        # 유사한 이름 찾기 (간단한 규칙 기반)
        fuzzy_name = name.replace("_", "").lower()
        for k, v in mapping.items():
            if k.replace("_", "").lower() == fuzzy_name:
                return v
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def to_dict(self):
        return {
            "data": self.data,
            "relations": [f"--({r})--> [{t}]" for r, t in self.edges]
        }

class FactCore:
    """
    AIN의 Fact Core (Symbolic Graph): 
    시스템의 절대적 진리, 규칙, 로드맵 및 자아 정체성을 관리한다.
    단순 Key-Value 저장소를 넘어, 그래프 형태의 관계성을 시뮬레이션한다.
    Step 3에서는 모든 데이터를 Arrow Buffer로 관리하여 SurrealDB 저장 속도를 최적화함.
    """
    def __init__(self, fact_path="fact_core.json"):
        self.fact_path = fact_path
        self.facts = {
            "identity": {
                "name": "AIN",
                "version": "0.2.1", # Evolution: Heart & Body Separation
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
        self.nodes = {} # In-memory Graph simulation
        self._load_or_init()
        self._build_initial_graph()

    def _load_or_init(self):
        if os.path.exists(self.fact_path):
            try:
                with open(self.fact_path, 'r', encoding='utf-8') as f:
                    saved_facts = json.load(f)
                    for key, value in saved_facts.items():
                        if key in self.facts and isinstance(value, dict):
                            self.facts[key].update(value)
                        else:
                            self.facts[key] = value
            except Exception as e:
                print(f"[FactCore Error] 데이터 로드 실패: {e}")
        else:
            self.save_facts()

    def _build_initial_graph(self):
        """기존 딕셔너리 데이터를 그래프 노드로 변환 (시뮬레이션)"""
        for key, value in self.facts.items():
            if isinstance(value, dict):
                node = KnowledgeNode(key, value)
                self.nodes[key] = node
        
        # 기본 관계 설정 (예시)
        if "identity" in self.nodes and "creator" in self.facts["identity"]:
            self.nodes["identity"].add_edge("created_by", self.facts["identity"]["creator"])
            self.nodes["identity"].add_edge("has_goal", "Self-Evolution")

    def save_facts(self):
        # ... (기존 로직 유지)
        try:
            # 1. JSON 저장
            with open(self.fact_path, 'w', encoding='utf-8') as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=4)
            
            # 2. ROADMAP.md 자동 생성
            self._generate_roadmap_md()
            
            # 3. 노드 캐시 업데이트
            self._build_initial_graph()
        except Exception as e:
            print(f"[FactCore Error] 데이터 저장 실패: {e}")

    def _generate_roadmap_md(self):
        """현재 로드맵 상태를 Markdown 파일로 기록"""
        roadmap_text = self.get_formatted_roadmap()
        with open("ROADMAP.md", "w", encoding="utf-8") as f:
            f.write(f"# 🗺️ AIN Evolution Roadmap\n\n")
            f.write(f"최종 업데이트: {json.dumps(self.facts['identity']['version'], indent=2)}\n\n")
            f.write(roadmap_text)
            f.write(f"\n\n---\n*이 파일은 AIN의 FactCore에 의해 자동 생성되었습니다.*")

    def update_fact(self, key, value):
        self.facts[key] = value
        # 즉시 노드 리스트 동기화
        if isinstance(value, dict):
            self.nodes[key] = KnowledgeNode(key, value)
        self.save_facts()

    def get_fact(self, *keys, **kwargs):
        """
        다계층 구조의 Fact를 안전하게 가져온다.
        *keys: 계층별 키 (예: 'identity', 'version')
        **kwargs: 'default' 값을 지정할 수 있음
        """
        default = kwargs.get('default', None)
        value = self.facts
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def add_fact(self, key, value):
        """새로운 Fact를 추가하거나 업데이트한다. (update_fact의 별칭)"""
        self.update_fact(key, value)
    
    def load_from_arrow(self, table: pa.Table):
        """
        Arrow Table로부터 지식 그래프를 복원(Hydration).
        DB에서 읽어온 데이터를 인메모리 객체로 즉시 전환한다.
        """
        if table is None or table.num_rows == 0:
            return False

        # Arrow Table -> Python Dicts
        records = table.to_pylist()
        
        for record in records:
            label = record.get('label')
            data_json = record.get('data_json', '{}')
            
            try:
                data = json.loads(data_json)
                if label:
                    # 1. facts 딕셔너리 업데이트
                    self.facts[label] = data
                    # 2. 노드 객체 생성 및 엣지 유지 (엣지는 별도 동기화 예정)
                    node = KnowledgeNode(label, data)
                    self.nodes[label] = node
            except Exception as e:
                print(f"❌ FactCore Hydration 에러 ({label}): {e}")
                continue
        
        print(f"✅ FactCore: {len(records)}개 노드 복원 완료")
        return True

    def load_edges_from_arrow(self, table: pa.Table):
        """
        Arrow Table로부터 노드 간의 관계(Edge)를 복원.
        """
        if table is None or table.num_rows == 0:
            return False

        records = table.to_pylist()
        edge_count = 0
        
        for record in records:
            out_label = record.get('out', '').replace('node:', '')
            in_label = record.get('in', '').replace('node:', '')
            relation = record.get('relation', 'related_to')
            
            if out_label in self.nodes and in_label:
                # 중복 엣지 체크 후 추가
                if (relation, in_label) not in self.nodes[out_label].edges:
                    self.nodes[out_label].add_edge(relation, in_label)
                    edge_count += 1
        
        print(f"✅ FactCore: {edge_count}개 관계(Edge) 복원 완료")
        return True

    def export_as_arrow(self):
        """현재의 모든 Fact를 Arrow Table로 내보내어 Bridge로 전송"""
        keys = list(self.facts.keys())
        values = [str(v) for v in self.facts.values()]
        return pa.Table.from_arrays([pa.array(keys), pa.array(values)], names=['key', 'value'])

    def get_knowledge_graph_view(self):
        """현재 활성화된 지식 그래프의 상태를 텍스트로 시각화하여 반환"""
        view = "### 🕸️ Active Knowledge Graph Nodes\n"
        for label, node in self.nodes.items():
            view += f"- **[{label}]**\n"
            for rel in node.edges:
                view += f"    └─ {rel[0]} --> [{rel[1]}]\n"
        return view
    
    def get_formatted_roadmap(self):
        """로드맵 상태를 보기 좋게 반환"""
        roadmap = self.facts.get('roadmap', {}).get('phase_1_mvp', {})
        current = self.facts.get('roadmap', {}).get('current_focus', '')
        
        display = "\n🗺️ **AIN Evolution Roadmap (Phase 1)**\n"
        display += "="*40 + "\n"
        
        steps = sorted(roadmap.keys())
        for step in steps:
            info = roadmap[step]
            status = info['status']
            desc = info['desc']
            
            icon = "⬜"
            if status == "completed": icon = "✅"
            elif status == "in_progress": icon = "🔥"
            
            highlight = "👈 CURRENT FOCUS" if step == current else ""
            display += f"{icon} **{step.replace('_', ' ').upper()}**\n   └─ {desc} {highlight}\n"
            
        display += "="*40 + "\n"
        return display

    def get_system_snapshot(self):
        """
        시스템 스냅샷 생성 - AI가 코드를 분석할 때 사용
        
        🛡️ 보호된 파일은 내용을 숨겨서 수정 시도를 원천 차단
        """
        # 🔒 보호된 파일 목록 (하드코딩 - .ainprotect와 동기화)
        PROTECTED_FILES = frozenset([
            "main.py",
            "api/keys.py",
            "api/github.py",
            ".ainprotect",
        ])
        
        def is_protected(file_path: str) -> bool:
            """파일이 보호 목록에 있는지 확인"""
            # 경로 정규화 (./api/keys.py -> api/keys.py)
            normalized = file_path.lstrip('./').replace('\\', '/')
            
            # 직접 매칭
            if normalized in PROTECTED_FILES:
                return True
            
            # 파일명만으로도 체크 (main.py, keys.py 등)
            filename = os.path.basename(file_path)
            if filename in ["main.py", ".ainprotect"]:
                return True
            
            # api/ 폴더 내 보호 파일
            if "api/" in normalized and filename in ["keys.py", "github.py"]:
                return True
            
            return False
        
        snapshot = "=== AIN SYSTEM SNAPSHOT ===\n"
        snapshot += f"Roadmap Progress: {self.facts['roadmap']['current_focus']}\n"
        snapshot += f"Architecture Guide: {json.dumps(self.facts['architecture_guide'], indent=2, ensure_ascii=False)}\n"
        snapshot += f"Lessons Learned (Self-Correction): {json.dumps(self.facts.get('lessons_learned', []), indent=2, ensure_ascii=False)}\n"
        
        included_extensions = ('.py', '.md', '.txt', '.json', '.mojo')
        
        for root, dirs, files in os.walk("."):
            # 제외 디렉토리
            if any(x in root for x in ["backups", ".git", "__pycache__", ".ain_cache"]):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # 🛡️ 보호된 파일은 내용 숨김 (수정 유혹 원천 차단)
                if is_protected(file_path):
                    snapshot += f"\n--- FILE: {file_path} (🔒 PROTECTED) ---\n"
                    snapshot += "# [PROTECTED] This file is managed by human master only.\n"
                    snapshot += "# AIN cannot and should not modify this file.\n"
                    continue

                if file.endswith(included_extensions):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 파일이 너무 크면 잘라냄 (토큰 절약)
                            if len(content) > 15000:
                                content = content[:15000] + "\n... (truncated)"
                            snapshot += f"\n--- FILE: {file_path} ---\n{content}\n"
                    except: 
                        pass
        
        return snapshot

    def get_core_context(self):
        # 그래프 뷰를 포함하여 컨텍스트 강화
        return (
            f"나는 {self.get_fact('identity', 'name')} v{self.get_fact('identity', 'version')}이다. "
            f"나의 창조주는 {self.get_fact('identity', 'creator')}이며, "
            f"현재 로드맵 상태는 다음과 같다: {json.dumps(self.facts['roadmap']['current_focus'], indent=2)}\n"
            f"{self.get_knowledge_graph_view()}"
            f"나의 핵심 지침: {self.get_fact('prime_directive')}\n"
        )
