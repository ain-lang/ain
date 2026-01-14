"""
Corpus Transform: Arrow 변환 및 Context Synthesis
"""
import json
from typing import List, Dict, Optional

try:
    import pyarrow as pa
    import pandas as pd
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False


class TransformMixin:
    """변환 믹스인 - CorpusCallosum에서 사용"""
    
    def synthesize_context(self, user_query: str = None) -> str:
        """좌뇌와 우뇌 정보를 통합하여 컨텍스트 생성"""
        context_parts = ["=== AIN NEURAL CONTEXT ===\n"]
        
        if hasattr(self.left_brain, 'get_core_context'):
            context_parts.append("[LEFT BRAIN - Symbolic Logic]\n")
            context_parts.append(self.left_brain.get_core_context())
        
        if hasattr(self.right_brain, 'get_evolution_summary'):
            context_parts.append("\n[RIGHT BRAIN - Evolution Memory]\n")
            context_parts.append(self.right_brain.get_evolution_summary())
        
        # [Step 4 Integration] 의미론적 기억(Semantic Memory) 회상 추가
        if hasattr(self.right_brain, 'get_recent_insights'):
            context_parts.append("\n[SEMANTIC INSIGHTS - Recalled Memories]\n")
            # 쿼리가 있으면 연관 기억, 없으면 최근 통찰 추출
            if user_query:
                memories = self.right_brain.retrieve_relevant_memories(user_query, limit=3)
                if memories:
                    for i, m in enumerate(memories, 1):
                        context_parts.append(f"  {i}. {m.get('text', '')[:200]}\n")
                else:
                    context_parts.append("  (연관된 의미론적 기억 없음)\n")
            else:
                context_parts.append(self.right_brain.get_recent_insights(limit=3))
                context_parts.append("\n")
        
        if user_query:
            context_parts.append(f"\n[USER QUERY]\n{user_query}")
        
        context_parts.append(f"\n[SYNC STATUS]")
        context_parts.append(f"  - SurrealDB: {'연결됨' if self._bridge_connected else '미연결'}")
        context_parts.append(f"  - LanceDB: {'연결됨' if self._vector_connected else '미연결'}")
        context_parts.append(f"  - 마지막 동기화: {self._last_sync_time or 'N/A'}")
        context_parts.append(f"  - 총 동기화 횟수: {self._sync_count}")
        
        return "\n".join(context_parts)

    def bridge_to_arrow(self, data: List[Dict]):
        """범용 데이터를 Arrow Table로 변환"""
        if not data or not HAS_ARROW:
            return None
        
        try:
            return pa.Table.from_pylist(data)
        except Exception as e:
            print(f"❌ Arrow 변환 실패: {e}")
            return None

    def format_fact_for_surreal(self):
        """FactCore 데이터를 Arrow Table로 변환"""
        if not HAS_ARROW:
            return None
        
        try:
            now = pd.Timestamp.now().floor('ms')
            data = []
            
            for label, node in self.left_brain.nodes.items():
                data.append({
                    'id': label,
                    'label': label,
                    'data_json': json.dumps(node.data, ensure_ascii=False),
                    'edges_count': len(node.edges),
                    'timestamp': now
                })
            
            if not data:
                return None
            
            return pa.table({
                'id': [d['id'] for d in data],
                'label': [d['label'] for d in data],
                'data_json': [d['data_json'] for d in data],
                'edges_count': [d['edges_count'] for d in data],
                'timestamp': pa.array([d['timestamp'] for d in data], type=pa.timestamp('ms'))
            })
            
        except Exception as e:
            print(f"❌ FactCore → Arrow 변환 실패: {e}")
            return None

    def _history_to_arrow(self, history: List[Dict]):
        """진화 기록을 Arrow Table로 변환"""
        if not history or not HAS_ARROW:
            return None
        
        try:
            return pa.table({
                'timestamp': [str(h.get('timestamp', '')) for h in history],
                'type': [str(h.get('type', '')) for h in history],
                'action': [str(h.get('action', '')) for h in history],
                'file': [str(h.get('file', '')) for h in history],
                'description': [str(h.get('description', ''))[:1000] for h in history],
                'status': [str(h.get('status', '')) for h in history],
            })
        except Exception as e:
            print(f"❌ History → Arrow 변환 실패: {e}")
            return None
