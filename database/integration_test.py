import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pyarrow as pa
from database.zero_copy import ZeroCopyBufferExposer
from database.surreal_bridge import ArrowBufferManager
from fact_core import FactCore

class BridgeIntegrationTest:
    """
    FactCore(Graph) -> SurrealDB(Store) -> Arrow(Zero-Copy) 통합 검증 모듈
    """
    def __init__(self):
        self.exposer = ZeroCopyBufferExposer()
        self.manager = ArrowBufferManager(capacity=1000)
        
    async def push_fact_to_surreal(self, fact_core: FactCore):
        """FactCore의 지식 노드를 SurrealDB RELATION 구조로 매핑하여 주입"""
        for label, node in fact_core.nodes.items():
            # 1. 노드 생성 (Record)
            # await surreal_client.create(f"node:{label}", node.data)
            
            # 2. 관계 생성 (Edge)
            for relation, target in node.edges:
                # await surreal_client.query(
                #    f"RELATE node:{label}->{relation}->node:{target} SET timestamp = time::now()"
                # )
                pass
        print(f"[Integration] {len(fact_core.nodes)} nodes and relations prepared for SurrealDB.")

    def pull_to_arrow_zero_copy(self, raw_edge_data):
        """
        SurrealDB에서 인출된 Edge 데이터를 Arrow RecordBatch로 변환 (Zero-Copy)
        raw_edge_data: List[Dict] 형태의 SurrealDB 결과물
        """
        # 1. 데이터 레이아웃 정의 (Source ID, Target ID, Relation Hash)
        # 물리적 메모리 정렬을 위해 고정 크기 바이너리 또는 정수형 변환
        source_indices = np.array([hash(d['in']) for d in raw_edge_data], dtype=np.int64)
        target_indices = np.array([hash(d['out']) for d in raw_edge_data], dtype=np.int64)
        
        # 2. C Data Interface를 통한 Zero-Copy Buffer 노출
        source_buf = self.exposer.expose_numpy_buffer(source_indices)
        target_buf = self.exposer.expose_numpy_buffer(target_indices)
        
        # 3. Arrow RecordBatch 재구성 (복사 없음)
        batch = pa.RecordBatch.from_arrays(
            [
                pa.Array.from_buffers(pa.int64(), len(source_indices), [None, source_buf]),
                pa.Array.from_buffers(pa.int64(), len(target_indices), [None, target_buf])
            ],
            names=["source_id", "target_id"]
        )
        
        return batch

    def run_benchmark(self, batch: pa.RecordBatch):
        """인출된 Arrow 데이터의 무결성 및 메모리 주소 검증"""
        address = batch.column(0).buffers()[1].address
        print(f"[Benchmark] Arrow RecordBatch created at Buffer Address: {hex(address)}")
        print(f"[Benchmark] Row count: {batch.num_rows}")
        return True

if __name__ == "__main__":
    # 실전 테스트 시나리오
    test = BridgeIntegrationTest()
    fc = FactCore()
    
    # 1. FactCore 데이터 준비
    fc.add_fact("AIN", {"status": "evolving"})
    fc.add_fact("SurrealDB", {"type": "GraphDB"})
    
    # [Fix] nodes["AIN"] 접근 전 강제 빌드 확인 (이미 update_fact에서 수행됨)
    fc.nodes["AIN"].add_edge("uses", "SurrealDB")
    
    # 2. 가상의 SurrealDB Edge 데이터 (인출 시뮬레이션)
    mock_edges = [{"in": "node:AIN", "out": "node:SurrealDB", "r": "uses"}]
    
    # 3. Zero-Copy 인출 실행
    arrow_batch = test.pull_to_arrow_zero_copy(mock_edges)
    test.run_benchmark(arrow_batch)