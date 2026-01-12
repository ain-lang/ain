import json
import pandas as pd
import pyarrow as pa
from typing import Dict, List, Optional, Any

class GraphSerializer:
    """
    AIN Step 3: Graph-to-Arrow Serialization Engine
    FactCore의 객체 그래프를 고성능 Arrow Table로 변환하거나 그 반대를 수행.
    """
    
    @staticmethod
    def nodes_to_table(nodes: Dict[str, Any]) -> pa.Table:
        """노드 딕셔너리를 Arrow Table로 변환"""
        data = []
        now = pd.Timestamp.now().floor('ms')
        
        for label, node in nodes.items():
            data.append({
                "id": label,
                "label": label,
                "data_json": json.dumps(node.data, ensure_ascii=False),
                "edges_count": len(node.edges),
                "timestamp": now
            })
            
        if not data:
            # 빈 테이블 스키마 정의
            return pa.table({
                'id': pa.array([], type=pa.string()),
                'label': pa.array([], type=pa.string()),
                'data_json': pa.array([], type=pa.string()),
                'edges_count': pa.array([], type=pa.int64()),
                'timestamp': pa.array([], type=pa.timestamp('ms'))
            })
            
        return pa.table({
            'id': [d['id'] for d in data],
            'label': [d['label'] for d in data],
            'data_json': [d['data_json'] for d in data],
            'edges_count': [d['edges_count'] for d in data],
            'timestamp': pa.array([d['timestamp'] for d in data], type=pa.timestamp('ms'))
        })

    @staticmethod
    def edges_to_table(nodes: Dict[str, Any]) -> pa.Table:
        """노드들 사이의 관계(Edge)를 Arrow Table로 변환"""
        edges = []
        
        for out_label, node in nodes.items():
            for relation, in_label in node.edges:
                edges.append({
                    "out": f"node:{out_label}",
                    "in": f"node:{in_label}",
                    "relation": relation,
                    "data_json": "{}" # 추가 관계 속성 필요 시 확장
                })
                
        if not edges:
            return pa.table({
                'out': pa.array([], type=pa.string()),
                'in': pa.array([], type=pa.string()),
                'relation': pa.array([], type=pa.string()),
                'data_json': pa.array([], type=pa.string())
            })
            
        return pa.table({
            'out': [e['out'] for e in edges],
            'in': [e['in'] for e in edges],
            'relation': [e['relation'] for e in edges],
            'data_json': [e['data_json'] for d in edges] # 오타 수정 d->e
        })
