"""
Facts Storage: 저장/로드 로직
"""
import os
import json
from typing import Dict, Any

try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

from .node import KnowledgeNode


class StorageMixin:
    """저장/로드 믹스인"""
    
    def _load_or_init(self):
        if os.path.exists(self.fact_path):
            try:
                with open(self.fact_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"⚠️ FactCore: {self.fact_path}가 비어있습니다.")
                        self.save_facts()
                        return
                    
                    try:
                        saved_facts = json.loads(content)
                    except json.JSONDecodeError:
                        last_brace = content.rfind("}")
                        if last_brace != -1:
                            saved_facts = json.loads(content[:last_brace+1])
                            print(f"⚠️ FactCore: {self.fact_path} 복구 후 로드 성공")
                        else:
                            raise
                    
                    for key, value in saved_facts.items():
                        if key in self.facts and isinstance(value, dict):
                            self.facts[key].update(value)
                        else:
                            self.facts[key] = value
            except Exception as e:
                print(f"❌ FactCore 데이터 로드 실패 (기본값 사용): {e}")
                self.save_facts()
        else:
            self.save_facts()

    def save_facts(self):
        try:
            with open(self.fact_path, 'w', encoding='utf-8') as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=4)
            
            self._generate_roadmap_md()
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

    def load_from_arrow(self, table):
        """Arrow Table로부터 지식 그래프를 복원"""
        if table is None or table.num_rows == 0:
            return False

        records = table.to_pylist()
        
        for record in records:
            label = record.get('label')
            data_json = record.get('data_json', '{}')
            
            try:
                data = json.loads(data_json)
                if label:
                    self.facts[label] = data
                    node = KnowledgeNode(label, data)
                    self.nodes[label] = node
            except Exception as e:
                print(f"❌ FactCore Hydration 에러 ({label}): {e}")
                continue
        
        print(f"✅ FactCore: {len(records)}개 노드 복원 완료")
        return True

    def load_edges_from_arrow(self, table):
        """Arrow Table로부터 노드 간의 관계(Edge)를 복원"""
        if table is None or table.num_rows == 0:
            return False

        records = table.to_pylist()
        edge_count = 0
        
        for record in records:
            out_label = record.get('out', '').replace('node:', '')
            in_label = record.get('in', '').replace('node:', '')
            relation = record.get('relation', 'related_to')
            
            if out_label in self.nodes and in_label:
                if (relation, in_label) not in self.nodes[out_label].edges:
                    self.nodes[out_label].add_edge(relation, in_label)
                    edge_count += 1
        
        print(f"✅ FactCore: {edge_count}개 관계(Edge) 복원 완료")
        return True

    def export_as_arrow(self):
        """현재의 모든 Fact를 Arrow Table로 내보내기"""
        if not HAS_ARROW:
            return None
        keys = list(self.facts.keys())
        values = [str(v) for v in self.facts.values()]
        return pa.Table.from_arrays([pa.array(keys), pa.array(values)], names=['key', 'value'])
