"""
AIN의 뇌량 (Corpus Callosum):
좌뇌(Fact Core/Logic)와 우뇌(Nexus/Intuition) 사이의 정보 교환을 담당하는 브릿지.

Step 3 진화 - Runtime Level:
- hydrate_knowledge(): 부팅 시 SurrealDB에서 최신 상태 복원
- sync_pulse(): 주기적 상태 동기화 (Arrow Batch → SurrealDB)
- SurrealArrowBridge를 직접 제어하여 완전한 데이터 파이프라인 구현
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
    import pandas as pd
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False

try:
    from database.serializer import GraphSerializer
    HAS_SERIALIZER = True
except ImportError:
    HAS_SERIALIZER = False

# SurrealArrowBridge 임포트
try:
    from database.surreal_bridge import SurrealArrowBridge, ArrowBufferManager
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False
    print("⚠️ SurrealArrowBridge 임포트 실패. 브릿지 기능 비활성화.")

# Arrow Schema 임포트 (SSOT)
try:
    from database.arrow_schema import get_node_schema
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False
    print("⚠️ Arrow Schema 임포트 실패. 기본 스키마 사용.")


class CorpusCallosum:
    """
    AIN의 뇌량 (Corpus Callosum):
    좌뇌(Fact Core/Logic)와 우뇌(Nexus/Intuition) 사이의 정보 교환을 담당하는 브릿지.
    
    Step 3 핵심 역할 (Runtime-Level):
    - hydrate_knowledge(): 부팅 시 DB에서 기억 복원 (Hydration)
    - sync_pulse(): 실행 주기마다 상태를 Arrow Batch로 직렬화하여 영구 저장
    - SurrealArrowBridge 인스턴스 관리
    """
    
    def __init__(self, fact_core, nexus):
        self.left_brain = fact_core  # Fact Core (Symbolic Graph)
        self.right_brain = nexus     # Nexus (Embedding/Memory)
        
        # Step 3: SurrealArrowBridge 인스턴스화
        self.bridge: Optional[SurrealArrowBridge] = None
        if HAS_BRIDGE:
            self.bridge = SurrealArrowBridge()
            print("🔗 CorpusCallosum: SurrealArrowBridge 초기화 완료")
        
        # 연결 상태 추적
        self._bridge_connected: bool = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_count: int = 0
        
        # 마지막 생성된 배치 캐시
        self._last_batch: Optional[pa.RecordBatch] = None
        self._last_table: Optional[pa.Table] = None
        
        if HAS_ARROW:
            # Step 3 핵심: 데이터 스키마 정의 (Zero-Copy를 위한 메모리 레이아웃)
            self.context_schema = pa.schema([
                ('source', pa.string()),
                ('key', pa.string()),
                ('value', pa.string()),
                ('timestamp', pa.timestamp('ms'))
            ])
            
            # Fact 저장용 스키마 (arrow_schema.py와 호환)
            if HAS_SCHEMA:
                self.fact_schema = get_node_schema()
            else:
                self.fact_schema = pa.schema([
                    ('id', pa.string()),
                    ('label', pa.string()),
                    ('data_json', pa.string()),
                    ('edges_count', pa.int32()),
                    ('timestamp', pa.timestamp('ms'))
                ])

    async def initialize_bridge(self) -> bool:
        """브릿지 연결 초기화 (비동기)"""
        if self.bridge:
            try:
                self._bridge_connected = await self.bridge.connect()
                if self._bridge_connected:
                    print("✅ CorpusCallosum: SurrealDB 브릿지 연결 성공")
                else:
                    print("⚠️ CorpusCallosum: 브릿지 연결 실패, Memory-Only 모드")
                return self._bridge_connected
            except Exception as e:
                print(f"❌ CorpusCallosum: 브릿지 초기화 오류 - {e}")
                self._bridge_connected = False
                return False
        return False

    # =========================================================================
    # HYDRATION: 부팅 시 DB에서 기억 복원
    # =========================================================================
    
    async def hydrate_knowledge(self) -> bool:
        """
        [Step 3 핵심] 2단계 Hydration: SurrealDB에서 노드와 관계를 모두 복원.
        1. Nodes 복원 (그릇 만들기)
        2. Edges 복원 (신경망 잇기)
        """
        if not self._bridge_connected or not self.bridge:
            print("ℹ️ Hydration 건너뜀: 브릿지 미연결")
            return False
        
        try:
            # 1단계: 노드(Node) 복원
            node_table = await self._pull_nodes_from_db()
            if node_table and node_table.num_rows > 0:
                self.left_brain.load_from_arrow(node_table)
            
            # 2단계: 관계(Edge) 복원
            edge_table = await self._pull_edges_from_db()
            if edge_table and edge_table.num_rows > 0:
                if hasattr(self.left_brain, 'load_edges_from_arrow'):
                    self.left_brain.load_edges_from_arrow(edge_table)
            
            print(f"✨ Hydration 완료: 지식 그래프 위상 재구축됨")
            return True
                
        except Exception as e:
            print(f"⚠️ Hydration 실패: {e}")
            return False

    async def _pull_nodes_from_db(self) -> Optional[pa.Table]:
        """SurrealDB의 node 테이블에서 데이터를 Arrow Table로 가져옴"""
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

    async def _pull_edges_from_db(self) -> Optional[pa.Table]:
        """SurrealDB의 relation 테이블에서 엣지 데이터를 Arrow Table로 가져옴"""
        if not self.bridge:
            return None
        
        try:
            # 엣지 정보가 저장된 relation 테이블 조회
            return await asyncio.to_thread(
                self.bridge.pull_batch,
                "SELECT * FROM relation",
                "relation"
            )
        except Exception as e:
            print(f"❌ DB Edge Pull 실패: {e}")
            return None

    def _inject_to_fact_core(self, table: pa.Table) -> bool:
        """
        Arrow Table을 파싱하여 FactCore의 nodes 딕셔너리를 갱신
        
        FactCore.load_from_arrow()를 호출하여 데이터 주입
        """
        if table is None or not HAS_ARROW:
            return False
        
        try:
            # FactCore에 load_from_arrow 메서드가 있는지 확인
            if hasattr(self.left_brain, 'load_from_arrow'):
                return self.left_brain.load_from_arrow(table)
            else:
                # Fallback: 직접 파싱하여 주입
                return self._manual_inject(table)
        except Exception as e:
            print(f"❌ FactCore 주입 실패: {e}")
            return False

    def _manual_inject(self, table: pa.Table) -> bool:
        """Arrow Table을 수동으로 파싱하여 FactCore에 주입 (Fallback)"""
        try:
            # Arrow Table → Python List[Dict]
            records = table.to_pylist()
            
            for record in records:
                node_id = record.get('id', record.get('node_id', ''))
                label = record.get('label', '')
                data_json = record.get('data_json', '{}')
                
                if not label:
                    continue
                
                # JSON 파싱
                try:
                    data = json.loads(data_json) if data_json else {}
                except json.JSONDecodeError:
                    data = {}
                
                # FactCore에 노드 추가/갱신
                from fact_core import KnowledgeNode
                node = KnowledgeNode(label, data)
                self.left_brain.nodes[label] = node
                
                # facts 딕셔너리도 동기화
                if isinstance(data, dict) and data:
                    self.left_brain.facts[label] = data
            
            print(f"✅ Manual Inject: {len(records)}개 레코드 처리됨")
            return True
            
        except Exception as e:
            print(f"❌ Manual Inject 실패: {e}")
            return False

    # =========================================================================
    # SYNC PULSE: 주기적 상태 동기화
    # =========================================================================
    
    async def sync_pulse(self) -> bool:
        """
        [Step 3 핵심] 실행 주기마다 상태를 Arrow Batch로 직렬화하여 영구 저장
        
        FactCore와 Nexus의 현재 상태를 스냅샷 떠서 SurrealDB에 push
        
        Returns:
            bool: 동기화 성공 여부
        """
        if not self._bridge_connected or not self.bridge:
            print("ℹ️ Sync Pulse 건너뜀: 브릿지 미연결")
            return False
        
        try:
            sync_start = datetime.now()
            results = []
            
            # 1. FactCore 노드 동기화
            fact_result = await self._sync_fact_nodes()
            results.append(("FactCore", fact_result))
            
            # 2. Nexus 메모리 동기화 (진화 히스토리)
            nexus_result = await self._sync_nexus_memory()
            results.append(("Nexus", nexus_result))
            
            # 3. 동기화 메타데이터 업데이트
            self._last_sync_time = sync_start
            self._sync_count += 1
            
            # 결과 로깅
            success_count = sum(1 for _, r in results if r)
            print(f"🔄 Sync Pulse #{self._sync_count} 완료: {success_count}/{len(results)} 성공")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Sync Pulse 실패: {e}")
            return False

    async def _sync_fact_nodes(self) -> bool:
        """FactCore의 모든 노드와 엣지를 SurrealDB에 동기화"""
        try:
            # 1. 노드 동기화
            if HAS_SERIALIZER:
                node_table = GraphSerializer.nodes_to_table(self.left_brain.nodes)
            else:
                node_table = self.format_fact_for_surreal()
                
            if node_table and node_table.num_rows > 0:
                await asyncio.to_thread(self.bridge.push_batch_sync, node_table, "node")
                print(f"  └─ FactCore Nodes: {node_table.num_rows}개 동기화됨")
            
            # 2. 엣지 동기화 (RELATE)
            if HAS_SERIALIZER:
                edge_table = GraphSerializer.edges_to_table(self.left_brain.nodes)
                if edge_table and edge_table.num_rows > 0:
                    # 엣지는 'relation' 테이블에 저장하여 RELATE 쿼리 효과 시뮬레이션
                    await asyncio.to_thread(self.bridge.push_batch_sync, edge_table, "relation")
                    print(f"  └─ FactCore Edges: {edge_table.num_rows}개 동기화됨")
            
            return True
            
        except Exception as e:
            print(f"  └─ FactCore 동기화 실패: {e}")
            return False

    async def _sync_nexus_memory(self) -> bool:
        """Nexus의 진화 히스토리를 SurrealDB에 동기화"""
        try:
            # Nexus에서 최근 진화 기록 가져오기
            history = self.right_brain.load_data(self.right_brain.memory_file)
            
            if not history:
                return True  # 동기화할 데이터 없음
            
            # 최근 10개만 동기화 (전체 히스토리는 부담)
            recent_history = history[-10:] if len(history) > 10 else history
            
            # Arrow Table로 변환
            if HAS_ARROW:
                now_ms = pd.Timestamp.now().floor('ms')
                
                table = pa.table({
                    'id': [f"evolution:{i}" for i in range(len(recent_history))],
                    'timestamp': [h.get('timestamp', str(now_ms)) for h in recent_history],
                    'type': [h.get('type', 'UNKNOWN') for h in recent_history],
                    'file': [h.get('file', '') for h in recent_history],
                    'status': [h.get('status', 'unknown') for h in recent_history],
                    'description': [h.get('description', '')[:500] for h in recent_history]
                })
                
                result = await asyncio.to_thread(
                    self.bridge.push_batch,
                    table,
                    "evolution_log"
                )
                
                if result:
                    print(f"  └─ Nexus: {len(recent_history)}개 진화 기록 동기화됨")
                return result
            
            return False
            
        except Exception as e:
            print(f"  └─ Nexus 동기화 실패: {e}")
            return False

    # =========================================================================
    # 기존 메서드 (호환성 유지)
    # =========================================================================

    def _to_arrow_batch(self, raw_data: Dict[str, Any]) -> Optional[pa.RecordBatch]:
        """데이터를 Arrow RecordBatch로 변환하여 메모리 효율 극대화"""
        if not HAS_ARROW:
            return None
            
        # timestamp 형식 맞춤 (ms)
        now_ms = pd.Timestamp.now().floor('ms')
        
        arrays = [
            pa.array([raw_data.get('source', 'unknown')]),
            pa.array([raw_data.get('key', 'none')]),
            pa.array([raw_data.get('value', '')]),
            pa.array([now_ms], type=pa.timestamp('ms'))
        ]
        return pa.RecordBatch.from_arrays(arrays, schema=self.context_schema)

    def synthesize_context(self, user_query: str = None) -> str:
        """
        [Step 3 진화] 단순 텍스트 융합에서 Arrow Table 기반의 구조화된 데이터로 진화.
        이 데이터는 이후 SurrealDB의 Record로 직접 매핑됨.
        """
        identity = self.left_brain.get_fact("identity")
        roadmap = self.left_brain.get_fact("roadmap", "current_focus")
        prime_directive = self.left_brain.get_fact("prime_directive")
        history_summary = self.right_brain.get_evolution_summary()
        
        # 텍스트 컨텍스트 생성 (Muse용)
        context = f"""
=== AIN NEURAL CONTEXT ===
[Identity Matrix]
Name: {identity['name']} (v{identity['version']})
Creator: {identity['creator']}
Focus: {roadmap}

[Prime Directive]
{prime_directive}

[Evolutionary Memory (Right Brain)]
{history_summary}

[Current Stimulus]
Query: {user_query if user_query else "Autonomous Self-Reflection"}

[Sync Status]
Last Sync: {self._last_sync_time or 'Never'}
Sync Count: {self._sync_count}
Bridge Connected: {self._bridge_connected}
==========================
"""
        
        # [Step 3] 내부적으로 Arrow Batch 생성
        if HAS_ARROW:
            integrated_data = {
                "source": "corpus_callosum",
                "key": "synthesis_v1",
                "value": context.strip()
            }
            self._last_batch = self._to_arrow_batch(integrated_data)
            
        return context.strip()

    def bridge_to_arrow(self, data_list: List[Dict[str, Any]]) -> Optional[pa.Table]:
        """
        입력된 딕셔너리 리스트를 Apache Arrow Table로 변환한다. (Zero-Copy 기반 마련)
        """
        if not HAS_ARROW or not data_list:
            return None
        
        df = pd.DataFrame(data_list)
        table = pa.Table.from_pandas(df)
        self._last_table = table
        return table

    def format_fact_for_surreal(self) -> Optional[pa.Table]:
        """
        FactCore의 데이터를 SurrealDB에 고속 적재하기 위한 Arrow Table 형식으로 추출한다.
        """
        if not HAS_ARROW:
            print("⚠️ Arrow 미설치")
            return None
        
        # 디버그: FactCore 노드 상태 확인
        node_count = len(self.left_brain.nodes) if hasattr(self.left_brain, 'nodes') else 0
        print(f"📊 FactCore 노드 수: {node_count}")
        
        if node_count == 0:
            print(f"⚠️ nodes 속성 존재: {hasattr(self.left_brain, 'nodes')}")
            print(f"⚠️ facts 키: {list(self.left_brain.facts.keys()) if hasattr(self.left_brain, 'facts') else 'N/A'}")
            
        facts = []
        now_ms = pd.Timestamp.now().floor('ms')
        
        for label, node in self.left_brain.nodes.items():
            fact_entry = {
                "id": label,  # ID만 전달 (테이블명은 bridge에서 추가)
                "label": label,
                "data_json": json.dumps(node.data, ensure_ascii=False),
                "edges_count": len(node.edges),
                "timestamp": now_ms
            }
            facts.append(fact_entry)
        
        if not facts:
            return None
            
        # 스키마에 맞게 Arrow Table 생성
        table = pa.table({
            'id': [f['id'] for f in facts],
            'label': [f['label'] for f in facts],
            'data_json': [f['data_json'] for f in facts],
            'edges_count': [f['edges_count'] for f in facts],
            'timestamp': pa.array([f['timestamp'] for f in facts], type=pa.timestamp('ms'))
        })
        
        return table

    def push_to_surreal(self, batch: pa.RecordBatch = None, table: pa.Table = None) -> bool:
        """
        [Step 3 핵심 구현] Arrow 데이터를 SurrealDB에 영구 저장.
        RecordBatch 또는 Table을 받아 브릿지를 통해 저장.
        """
        if not HAS_ARROW or not self.bridge:
            print("⚠️ Arrow 또는 Bridge 미활성화. 저장 건너뜀.")
            return False
        
        try:
            # RecordBatch를 Table로 변환
            if batch is not None and table is None:
                table = pa.Table.from_batches([batch])
            
            if table is None:
                # 캐시된 테이블 사용
                table = self._last_table
                
            if table is None:
                print("⚠️ 저장할 데이터 없음.")
                return False
            
            # 브릿지를 통해 저장 (동기 인터페이스 사용)
            result = self.bridge.push_batch(table, "context_synthesis")
            print(f"✅ SurrealDB 저장 완료: {table.num_rows} rows")
            return result
            
        except Exception as e:
            print(f"❌ SurrealDB 저장 실패: {e}")
            return False

    def pull_from_surreal(self, query: str = None) -> Optional[pa.Table]:
        """
        [Step 3 핵심 구현] SurrealDB에서 Arrow Table로 데이터 인출.
        Zero-Copy 방식으로 메모리 효율 극대화.
        """
        if not self.bridge:
            print("⚠️ Bridge 미활성화. 인출 불가.")
            return None
        
        try:
            table = self.bridge.pull_batch(query, "context_synthesis")
            if table:
                print(f"✅ SurrealDB 인출 완료: {table.num_rows} rows")
            return table
        except Exception as e:
            print(f"❌ SurrealDB 인출 실패: {e}")
            return None

    def sync_facts_to_surreal(self) -> bool:
        """
        FactCore의 모든 노드와 엣지를 SurrealDB에 동기화.
        """
        if not self.bridge:
            print("⚠️ Bridge 없음 - 동기화 스킵")
            return False
            
        # 1. 노드 동기화
        node_table = GraphSerializer.nodes_to_table(self.left_brain.nodes) if HAS_SERIALIZER else self.format_fact_for_surreal()
        if node_table:
            self._last_table = node_table
            self._sync_count += 1
            self._last_sync_time = datetime.now()
            self.bridge.push_batch_sync(node_table, "node")
        
        # 2. 엣지(관계) 동기화
        if HAS_SERIALIZER:
            edge_table = GraphSerializer.edges_to_table(self.left_brain.nodes)
            if edge_table and edge_table.num_rows > 0:
                self.bridge.push_batch_sync(edge_table, "relation")
                print(f"💾 Sync: Nodes({node_table.num_rows if node_table else 0}), Edges({edge_table.num_rows}) 완료")
                return True
        
        return node_table is not None

    def get_bridge_status(self) -> Dict[str, Any]:
        """브릿지 상태 정보 반환"""
        return {
            "bridge_active": self.bridge is not None,
            "bridge_connected": self._bridge_connected,
            "arrow_available": HAS_ARROW,
            "schema_available": HAS_SCHEMA,
            "last_sync_time": str(self._last_sync_time) if self._last_sync_time else None,
            "sync_count": self._sync_count,
            "last_batch_rows": self._last_batch.num_rows if self._last_batch else 0,
            "last_table_rows": self._last_table.num_rows if self._last_table else 0
        }

    async def close_bridge(self):
        """브릿지 연결 종료"""
        if self.bridge and self._bridge_connected:
            try:
                await self.bridge.close()
                self._bridge_connected = False
                print("🔌 CorpusCallosum: 브릿지 연결 종료")
            except Exception as e:
                print(f"⚠️ 브릿지 종료 중 오류: {e}")