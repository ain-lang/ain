"""
Corpus Sync: 주기적 상태 동기화
"""
import hashlib
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

try:
    from database.serializer import GraphSerializer
    HAS_SERIALIZER = True
except ImportError:
    HAS_SERIALIZER = False


class SyncMixin:
    """동기화 믹스인 - CorpusCallosum에서 사용"""
    
    async def sync_pulse(self) -> bool:
        """실행 주기마다 상태를 Arrow Batch로 직렬화하여 영구 저장"""
        sync_start = datetime.now()
        results = []
        
        try:
            # 좌뇌 동기화: FactCore → SurrealDB
            if self._bridge_connected and self.bridge:
                fact_result = await self._sync_fact_nodes()
                results.append(("FactCore→SurrealDB", fact_result))
            else:
                results.append(("FactCore→SurrealDB", False))
            
            # 좌뇌 동기화: Nexus → SurrealDB
            if self._bridge_connected and self.bridge:
                nexus_result = await self._sync_nexus_memory()
                results.append(("Nexus→SurrealDB", nexus_result))
            else:
                results.append(("Nexus→SurrealDB", False))
            
            # 우뇌 동기화: Evolution → LanceDB
            if self._vector_connected and self.vector_bridge:
                semantic_result = await self._sync_semantic_memory()
                results.append(("Evolution→LanceDB", semantic_result))
            else:
                results.append(("Evolution→LanceDB", False))
            
            self._last_sync_time = sync_start
            self._sync_count += 1
            
            success_count = sum(1 for _, r in results if r)
            result_summary = " | ".join([f"{name}: {'✓' if ok else '✗'}" for name, ok in results])
            print(f"🔄 Sync Pulse #{self._sync_count} 완료: {success_count}/{len(results)} 성공 [{result_summary}]")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Sync Pulse 실패: {e}")
            return False

    async def _sync_fact_nodes(self) -> bool:
        """FactCore 노드/엣지를 SurrealDB에 동기화"""
        try:
            if HAS_SERIALIZER:
                node_table = GraphSerializer.nodes_to_table(self.left_brain.nodes)
            else:
                node_table = self.format_fact_for_surreal()
                
            if node_table and node_table.num_rows > 0:
                await asyncio.to_thread(self.bridge.push_batch_sync, node_table, "node")
                print(f"  └─ FactCore Nodes: {node_table.num_rows}개 동기화됨")
            
            if HAS_SERIALIZER:
                edge_table = GraphSerializer.edges_to_table(self.left_brain.nodes)
                if edge_table and edge_table.num_rows > 0:
                    await asyncio.to_thread(self.bridge.push_batch_sync, edge_table, "relation")
                    print(f"  └─ FactCore Edges: {edge_table.num_rows}개 동기화됨")
            
            return True
            
        except Exception as e:
            print(f"❌ FactCore 동기화 실패: {e}")
            return False

    async def _sync_nexus_memory(self) -> bool:
        """Nexus 진화 기록을 SurrealDB에 동기화"""
        try:
            if hasattr(self.right_brain, '_evolution_history_cache'):
                history = self.right_brain._evolution_history_cache
            else:
                history = []
            
            if not history:
                return True
            
            history_table = self._history_to_arrow(history)
            if history_table and history_table.num_rows > 0:
                await asyncio.to_thread(self.bridge.push_batch_sync, history_table, "evolution_history")
                print(f"  └─ Nexus History: {history_table.num_rows}개 동기화됨")
            
            return True
            
        except Exception as e:
            print(f"❌ Nexus 메모리 동기화 실패: {e}")
            return False

    async def _sync_semantic_memory(self) -> bool:
        """진화 기록을 LanceDB에 벡터화하여 저장"""
        if not self.vector_bridge or not self._vector_connected:
            return False
        
        try:
            if hasattr(self.right_brain, '_evolution_history_cache'):
                full_history = self.right_brain._evolution_history_cache
            else:
                full_history = []
            
            if not full_history:
                return True
            
            new_records = full_history[self._last_synced_evolution_index:]
            
            if not new_records:
                return True
            
            success_count = 0
            for record in new_records:
                try:
                    description = record.get('description', '')
                    if not description:
                        continue
                    
                    metadata = {
                        "timestamp": record.get('timestamp', ''),
                        "type": record.get('type', 'EVOLUTION'),
                        "action": record.get('action', 'Unknown'),
                        "file": record.get('file', ''),
                        "status": record.get('status', 'unknown'),
                    }
                    
                    if hasattr(self.right_brain, '_generate_embedding'):
                        vector = self.right_brain._generate_embedding(description)
                    else:
                        vector = self._generate_placeholder_embedding(description)
                    
                    stored = self.vector_bridge.add_memory(
                        text=description,
                        vector=vector,
                        memory_type="evolution",
                        source="evolution_history",
                        metadata=metadata
                    )
                    
                    if stored:
                        success_count += 1
                        
                except Exception as e:
                    continue
            
            self._last_synced_evolution_index = len(full_history)
            print(f"  └─ Semantic Memory: {success_count}/{len(new_records)}개 벡터화 완료")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Semantic Memory 동기화 실패: {e}")
            return False

    def _generate_placeholder_embedding(self, text: str) -> List[float]:
        """Placeholder 임베딩 생성"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        vector = []
        for i in range(0, min(len(text_hash), self.EMBEDDING_DIM * 2), 2):
            byte_val = int(text_hash[i:i+2], 16)
            normalized = (byte_val - 128) / 128.0
            vector.append(normalized)
        
        while len(vector) < self.EMBEDDING_DIM:
            idx = len(vector) % len(vector) if vector else 0
            vector.append(vector[idx] * 0.9 if vector else 0.0)
        
        return vector[:self.EMBEDDING_DIM]

    def sync_facts_to_surreal(self) -> bool:
        """FactCore 동기화 (동기 버전)"""
        if not self.bridge or not self._bridge_connected:
            return False
        
        try:
            node_table = self.format_fact_for_surreal()
            if node_table:
                self.bridge.push_batch_sync(node_table, "node")
                self._sync_count += 1
                self._last_sync_time = datetime.now()
                return True
            return False
        except Exception as e:
            print(f"❌ sync_facts_to_surreal 실패: {e}")
            return False
