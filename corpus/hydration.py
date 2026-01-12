"""
Corpus Hydration: 부팅 시 DB에서 기억 복원
"""
import json
import asyncio
from typing import Optional

try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False


class HydrationMixin:
    """Hydration 믹스인 - CorpusCallosum에서 사용"""
    
    async def hydrate_knowledge(self) -> bool:
        """2단계 Hydration: SurrealDB에서 노드와 관계를 모두 복원"""
        hydration_results = {
            "surreal_nodes": False,
            "surreal_edges": False,
            "vector_db": False
        }
        
        if self._bridge_connected and self.bridge:
            try:
                node_table = await self._pull_nodes_from_db()
                if node_table and node_table.num_rows > 0:
                    self.left_brain.load_from_arrow(node_table)
                    hydration_results["surreal_nodes"] = True
                
                edge_table = await self._pull_edges_from_db()
                if edge_table and edge_table.num_rows > 0:
                    if hasattr(self.left_brain, 'load_edges_from_arrow'):
                        self.left_brain.load_edges_from_arrow(edge_table)
                        hydration_results["surreal_edges"] = True
                
                print(f"✨ SurrealDB Hydration 완료")
                    
            except Exception as e:
                print(f"⚠️ SurrealDB Hydration 실패: {e}")
        else:
            print("ℹ️ SurrealDB Hydration 건너뜀: 브릿지 미연결")
        
        if self._vector_connected and self.vector_bridge:
            try:
                memory_count = self.vector_bridge.count_memories()
                print(f"🧠 LanceDB 상태: {memory_count}개 기억 보유 중")
                hydration_results["vector_db"] = True
            except Exception as e:
                print(f"⚠️ LanceDB 상태 확인 실패: {e}")
        else:
            print("ℹ️ LanceDB Hydration 건너뜀: 벡터 브릿지 미연결")
        
        success_count = sum(1 for v in hydration_results.values() if v)
        print(f"📊 Hydration 결과: {success_count}/{len(hydration_results)} 성공")
        
        return success_count > 0

    async def _pull_nodes_from_db(self):
        """SurrealDB에서 노드 가져오기"""
        if not self.bridge:
            return None
        
        try:
            return await asyncio.to_thread(
                self.bridge.pull_batch,
                "SELECT * FROM node",
                "node"
            )
        except Exception as e:
            print(f"❌ DB Node Pull 실패: {e}")
            return None

    async def _pull_edges_from_db(self):
        """SurrealDB에서 엣지 가져오기"""
        if not self.bridge:
            return None
        
        try:
            return await asyncio.to_thread(
                self.bridge.pull_batch,
                "SELECT * FROM relation",
                "relation"
            )
        except Exception as e:
            print(f"❌ DB Edge Pull 실패: {e}")
            return None

    def _inject_to_fact_core(self, table) -> bool:
        """Arrow Table을 FactCore에 주입"""
        if table is None or not HAS_ARROW:
            return False
        
        try:
            if hasattr(self.left_brain, 'load_from_arrow'):
                return self.left_brain.load_from_arrow(table)
            else:
                return self._manual_inject(table)
        except Exception as e:
            print(f"❌ FactCore 주입 실패: {e}")
            return False

    def _manual_inject(self, table) -> bool:
        """Arrow Table을 수동으로 파싱하여 FactCore에 주입"""
        try:
            records = table.to_pylist()
            
            for record in records:
                label = record.get('label', '')
                data_json = record.get('data_json', '{}')
                
                if not label:
                    continue
                
                try:
                    data = json.loads(data_json) if data_json else {}
                except json.JSONDecodeError:
                    data = {}
                
                from fact_core import KnowledgeNode
                node = KnowledgeNode(label, data)
                self.left_brain.nodes[label] = node
                
                if isinstance(data, dict) and data:
                    self.left_brain.facts[label] = data
            
            print(f"✅ Manual Inject: {len(records)}개 레코드 처리됨")
            return True
            
        except Exception as e:
            print(f"❌ Manual Inject 실패: {e}")
            return False
