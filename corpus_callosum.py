"""
AIN의 뇌량 (Corpus Callosum):
좌뇌(Fact Core/Logic)와 우뇌(Nexus/Intuition) 사이의 정보 교환을 담당하는 브릿지.

Step 3 진화 - Runtime Level:
- hydrate_knowledge(): 부팅 시 SurrealDB에서 최신 상태 복원
- sync_pulse(): 주기적 상태 동기화 (Arrow Batch → SurrealDB)
- SurrealArrowBridge를 직접 제어하여 완전한 데이터 파이프라인 구현

Step 4 진화 - Bicameral Memory Integration:
- _sync_semantic_memory(): LanceDB로 진화 기록 벡터화 저장
- 좌뇌(SurrealDB/Logic)와 우뇌(LanceDB/Intuition) 동시 동기화
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

# LanceBridge 임포트 (Step 4: Vector Memory)
try:
    from database.lance_bridge import get_lance_bridge, LanceBridge, LANCE_AVAILABLE
    HAS_LANCE = LANCE_AVAILABLE
except ImportError:
    HAS_LANCE = False
    print("⚠️ LanceBridge 임포트 실패. Vector Memory 비활성화.")


class CorpusCallosum:
    """
    AIN의 뇌량 (Corpus Callosum):
    좌뇌(Fact Core/Logic)와 우뇌(Nexus/Intuition) 사이의 정보 교환을 담당하는 브릿지.
    
    Step 3 핵심 역할 (Runtime-Level):
    - hydrate_knowledge(): 부팅 시 DB에서 기억 복원 (Hydration)
    - sync_pulse(): 실행 주기마다 상태를 Arrow Batch로 직렬화하여 영구 저장
    - SurrealArrowBridge 인스턴스 관리
    
    Step 4 핵심 역할 (Bicameral Memory Integration):
    - 좌뇌(SurrealDB): 구조화된 지식 그래프 저장
    - 우뇌(LanceDB): 의미론적 벡터 기억 저장
    - 양원적 동기화: 두 저장소에 동시 데이터 흐름 제어
    """
    
    # 임베딩 벡터 차원 (Nexus와 동기화)
    EMBEDDING_DIM = 384
    
    def __init__(self, fact_core, nexus):
        self.left_brain = fact_core  # Fact Core (Symbolic Graph)
        self.right_brain = nexus     # Nexus (Embedding/Memory)
        
        # Step 3: SurrealArrowBridge 인스턴스화
        self.bridge: Optional[SurrealArrowBridge] = None
        if HAS_BRIDGE:
            self.bridge = SurrealArrowBridge()
            print("🔗 CorpusCallosum: SurrealArrowBridge 초기화 완료")
        
        # Step 4: LanceBridge 인스턴스화 (Vector Memory)
        self.vector_bridge: Optional[LanceBridge] = None
        self._vector_connected: bool = False
        if HAS_LANCE:
            try:
                self.vector_bridge = get_lance_bridge()
                self._vector_connected = self.vector_bridge.is_connected
                if self._vector_connected:
                    print(f"🧠 CorpusCallosum: LanceBridge 연결 성공 (기억 수: {self.vector_bridge.count_memories()})")
                else:
                    print("⚠️ CorpusCallosum: LanceBridge 연결 실패. 벡터 메모리 비활성화.")
            except Exception as e:
                print(f"❌ CorpusCallosum: LanceBridge 초기화 오류 - {e}")
                self.vector_bridge = None
                self._vector_connected = False
        
        # 연결 상태 추적
        self._bridge_connected: bool = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_count: int = 0
        
        # 마지막 동기화된 진화 기록 인덱스 (중복 저장 방지)
        self._last_synced_evolution_index: int = 0
        
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
        [Step 4 확장] 벡터 DB 연결 상태 확인 및 로깅.
        
        1. Nodes 복원 (그릇 만들기)
        2. Edges 복원 (신경망 잇기)
        3. Vector DB 상태 확인 (우뇌 점검)
        """
        hydration_results = {
            "surreal_nodes": False,
            "surreal_edges": False,
            "vector_db": False
        }
        
        # Step 3: SurrealDB Hydration
        if self._bridge_connected and self.bridge:
            try:
                # 1단계: 노드(Node) 복원
                node_table = await self._pull_nodes_from_db()
                if node_table and node_table.num_rows > 0:
                    self.left_brain.load_from_arrow(node_table)
                    hydration_results["surreal_nodes"] = True
                
                # 2단계: 관계(Edge) 복원
                edge_table = await self._pull_edges_from_db()
                if edge_table and edge_table.num_rows > 0:
                    if hasattr(self.left_brain, 'load_edges_from_arrow'):
                        self.left_brain.load_edges_from_arrow(edge_table)
                        hydration_results["surreal_edges"] = True
                
                print(f"✨ SurrealDB Hydration 완료: 지식 그래프 위상 재구축됨")
                    
            except Exception as e:
                print(f"⚠️ SurrealDB Hydration 실패: {e}")
        else:
            print("ℹ️ SurrealDB Hydration 건너뜀: 브릿지 미연결")
        
        # Step 4: Vector DB 상태 점검
        if self._vector_connected and self.vector_bridge:
            try:
                memory_count = self.vector_bridge.count_memories()
                print(f"🧠 LanceDB 상태: {memory_count}개 기억 보유 중")
                hydration_results["vector_db"] = True
            except Exception as e:
                print(f"⚠️ LanceDB 상태 확인 실패: {e}")
        else:
            print("ℹ️ LanceDB Hydration 건너뜀: 벡터 브릿지 미연결")
        
        # 결과 요약
        success_count = sum(1 for v in hydration_results.values() if v)
        print(f"📊 Hydration 결과: {success_count}/{len(hydration_results)} 성공")
        
        return success_count > 0

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
    # SYNC PULSE: 주기적 상태 동기화 (Bicameral Integration)
    # =========================================================================
    
    async def sync_pulse(self) -> bool:
        """
        [Step 3 핵심] 실행 주기마다 상태를 Arrow Batch로 직렬화하여 영구 저장
        [Step 4 확장] 좌뇌(SurrealDB)와 우뇌(LanceDB) 동시 동기화
        
        FactCore와 Nexus의 현재 상태를 스냅샷 떠서 양쪽 DB에 push
        
        Returns:
            bool: 동기화 성공 여부 (하나라도 성공하면 True)
        """
        sync_start = datetime.now()
        results = []
        
        try:
            # 1. 좌뇌 동기화: FactCore → SurrealDB
            if self._bridge_connected and self.bridge:
                fact_result = await self._sync_fact_nodes()
                results.append(("FactCore→SurrealDB", fact_result))
            else:
                results.append(("FactCore→SurrealDB", False))
                print("ℹ️ 좌뇌 동기화 건너뜀: SurrealDB 미연결")
            
            # 2. 좌뇌 동기화: Nexus 메모리 → SurrealDB (진화 히스토리)
            if self._bridge_connected and self.bridge:
                nexus_result = await self._sync_nexus_memory()
                results.append(("Nexus→SurrealDB", nexus_result))
            else:
                results.append(("Nexus→SurrealDB", False))
            
            # 3. 우뇌 동기화: 진화 기록 → LanceDB (벡터화)
            if self._vector_connected and self.vector_bridge:
                semantic_result = await self._sync_semantic_memory()
                results.append(("Evolution→LanceDB", semantic_result))
            else:
                results.append(("Evolution→LanceDB", False))
                print("ℹ️ 우뇌 동기화 건너뜀: LanceDB 미연결")
            
            # 4. 동기화 메타데이터 업데이트
            self._last_sync_time = sync_start
            self._sync_count += 1
            
            # 결과 로깅
            success_count = sum(1 for _, r in results if r)
            total_count = len(results)
            
            result_summary = " | ".join([f"{name}: {'✓' if ok else '✗'}" for name, ok in results])
            print(f"🔄 Sync Pulse #{self._sync_count} 완료: {success_count}/{total_count} 성공 [{result_summary}]")
            
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
                    await asyncio.to_thread(self.bridge.push_batch_sync, edge_table, "relation")
                    print(f"  └─ FactCore Edges: {edge_table.num_rows}개 동기화됨")
            
            return True
            
        except Exception as e:
            print(f"❌ FactCore 동기화 실패: {e}")
            return False

    async def _sync_nexus_memory(self) -> bool:
        """Nexus의 진화 기록을 SurrealDB에 동기화"""
        try:
            # Nexus에서 진화 기록 가져오기
            if hasattr(self.right_brain, '_evolution_history_cache'):
                history = self.right_brain._evolution_history_cache
            else:
                history = []
            
            if not history:
                return True  # 빈 히스토리는 성공으로 처리
            
            # Arrow Table로 변환
            history_table = self._history_to_arrow(history)
            if history_table and history_table.num_rows > 0:
                await asyncio.to_thread(self.bridge.push_batch_sync, history_table, "evolution_history")
                print(f"  └─ Nexus History: {history_table.num_rows}개 동기화됨")
            
            return True
            
        except Exception as e:
            print(f"❌ Nexus 메모리 동기화 실패: {e}")
            return False

    async def _sync_semantic_memory(self) -> bool:
        """
        [Step 4 핵심] Nexus의 진화 기록을 LanceDB에 벡터화하여 저장.
        
        이 메서드는 '의미론적 동기화(Semantic Synchronization)'를 수행한다:
        1. Nexus의 evolution_history에서 아직 벡터화되지 않은 기록을 가져온다.
        2. 각 기록의 description을 텍스트로 추출한다.
        3. 임베딩 벡터를 생성한다 (Nexus._generate_embedding 호출 또는 Placeholder).
        4. LanceBridge.add_memory()를 통해 벡터 DB에 저장한다.
        
        Returns:
            bool: 동기화 성공 여부
        """
        if not self.vector_bridge or not self._vector_connected:
            return False
        
        try:
            # 1. Nexus에서 진화 기록 가져오기
            if hasattr(self.right_brain, '_evolution_history_cache'):
                full_history = self.right_brain._evolution_history_cache
            else:
                full_history = []
            
            if not full_history:
                print("  └─ Semantic Memory: 동기화할 기록 없음")
                return True
            
            # 2. 아직 동기화되지 않은 기록 필터링
            new_records = full_history[self._last_synced_evolution_index:]
            
            if not new_records:
                print("  └─ Semantic Memory: 새로운 기록 없음 (이미 동기화됨)")
                return True
            
            # 3. 각 기록을 벡터화하여 저장
            success_count = 0
            for record in new_records:
                try:
                    # 텍스트 추출
                    description = record.get('description', '')
                    if not description:
                        continue
                    
                    # 메타데이터 구성
                    metadata = {
                        "timestamp": record.get('timestamp', ''),
                        "type": record.get('type', 'EVOLUTION'),
                        "action": record.get('action', 'Unknown'),
                        "file": record.get('file', ''),
                        "status": record.get('status', 'unknown'),
                    }
                    
                    # 임베딩 벡터 생성
                    # Nexus에 _generate_embedding 메서드가 있으면 사용, 없으면 Placeholder
                    if hasattr(self.right_brain, '_generate_embedding'):
                        vector = self.right_brain._generate_embedding(description)
                    else:
                        # Placeholder: 간단한 해시 기반 벡터 (실제 임베딩 모델 연동 전)
                        vector = self._generate_placeholder_embedding(description)
                    
                    # LanceDB에 저장
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
                    print(f"  ⚠️ 기록 벡터화 실패: {e}")
                    continue
            
            # 4. 동기화 인덱스 업데이트
            self._last_synced_evolution_index = len(full_history)
            
            print(f"  └─ Semantic Memory: {success_count}/{len(new_records)}개 벡터화 완료")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Semantic Memory 동기화 실패: {e}")
            return False

    def _generate_placeholder_embedding(self, text: str) -> List[float]:
        """
        Placeholder 임베딩 생성 (실제 임베딩 모델 연동 전 임시 사용).
        
        텍스트의 해시값을 기반으로 결정론적 벡터를 생성한다.
        이는 동일한 텍스트에 대해 항상 동일한 벡터를 반환한다.
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            384차원 float 벡터
        """
        import hashlib
        
        # 텍스트 해시 생성
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # 해시를 숫자 시퀀스로 변환
        vector = []
        for i in range(0, min(len(text_hash), self.EMBEDDING_DIM * 2), 2):
            # 16진수 2자리를 0~1 사이 float로 변환
            byte_val = int(text_hash[i:i+2], 16)
            normalized = (byte_val - 128) / 128.0  # -1 ~ 1 범위
            vector.append(normalized)
        
        # 벡터 길이가 부족하면 패딩
        while len(vector) < self.EMBEDDING_DIM:
            # 기존 벡터를 반복하여 패딩
            idx = len(vector) % len(vector) if vector else 0
            vector.append(vector[idx] * 0.9 if vector else 0.0)
        
        return vector[:self.EMBEDDING_DIM]

    def _history_to_arrow(self, history: List[Dict]) -> Optional[pa.Table]:
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

    def format_fact_for_surreal(self) -> Optional[pa.Table]:
        """FactCore 데이터를 Arrow Table로 변환 (Fallback)"""
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

    # =========================================================================
    # CONTEXT SYNTHESIS: 좌뇌와 우뇌 정보 통합
    # =========================================================================

    def synthesize_context(self, user_query: str = None) -> str:
        """
        좌뇌(Fact Core)와 우뇌(Nexus)의 정보를 통합하여 컨텍스트 생성
        """
        context_parts = ["=== AIN NEURAL CONTEXT ===\n"]
        
        # 좌뇌: FactCore 정보
        if hasattr(self.left_brain, 'get_core_context'):
            context_parts.append("[LEFT BRAIN - Symbolic Logic]\n")
            context_parts.append(self.left_brain.get_core_context())
        
        # 우뇌: Nexus 정보
        if hasattr(self.right_brain, 'get_evolution_summary'):
            context_parts.append("\n[RIGHT BRAIN - Evolution Memory]\n")
            context_parts.append(self.right_brain.get_evolution_summary())
        
        # 사용자 쿼리
        if user_query:
            context_parts.append(f"\n[USER QUERY]\n{user_query}")
        
        # 동기화 상태
        context_parts.append(f"\n[SYNC STATUS]")
        context_parts.append(f"  - SurrealDB: {'연결됨' if self._bridge_connected else '미연결'}")
        context_parts.append(f"  - LanceDB: {'연결됨' if self._vector_connected else '미연결'}")
        context_parts.append(f"  - 마지막 동기화: {self._last_sync_time or 'N/A'}")
        context_parts.append(f"  - 총 동기화 횟수: {self._sync_count}")
        
        return "\n".join(context_parts)

    def bridge_to_arrow(self, data: List[Dict]) -> Optional[pa.Table]:
        """범용 데이터를 Arrow Table로 변환"""
        if not data or not HAS_ARROW:
            return None
        
        try:
            return pa.Table.from_pylist(data)
        except Exception as e:
            print(f"❌ Arrow 변환 실패: {e}")
            return None

    def get_sync_stats(self) -> Dict[str, Any]:
        """동기화 통계 반환"""
        return {
            "surreal_connected": self._bridge_connected,
            "lance_connected": self._vector_connected,
            "last_sync_time": self._last_sync_time.isoformat() if self._last_sync_time else None,
            "sync_count": self._sync_count,
            "last_synced_evolution_index": self._last_synced_evolution_index,
        }