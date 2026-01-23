"""
AIN Step 3: Unified SurrealDB-Arrow Bridge (SSOT) - CLOSED LOOP IMPLEMENTATION
==============================================================================
[PROTECTED] 이 파일은 인간 주인이 직접 관리합니다. 절대 수정 금지!
[PROTECTED] This file is managed by human master only. DO NOT MODIFY!

The Single Source of Truth for ALL database operations.

Features: 
- connect(): 실제 SurrealDB 연결 (실패 시 memory_mode 활성화)
- push_batch(): Arrow Table → SurrealDB UPSERT (배치 처리)
- pull_batch(): SurrealQL Query → Arrow Table (실제 구현)
- Memory-Only Fallback으로 DB 장애 시에도 시스템 유지
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
import threading

import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
import numpy as np

# SurrealDB 클라이언트 - 동적 임포트 (SDK 1.0+ uses AsyncSurreal)
try:
    from surrealdb import AsyncSurreal as Surreal  # SDK 1.0 호환
    HAS_SURREAL = True
except ImportError:
    try:
        from surrealdb import Surreal  # 구버전 폴백
        HAS_SURREAL = True
    except ImportError:
        HAS_SURREAL = False
        print("⚠️ surrealdb 패키지 미설치. Memory-Only 모드로 작동합니다.")

# ArrowDiskSpiller 통합
try:
    from .arrow_spiller import ArrowDiskSpiller
    HAS_SPILLER = True
except ImportError:
    HAS_SPILLER = False


# =============================================================================
# Arrow Buffer Manager (Memory-Efficient Batch Processing)
# =============================================================================

class ArrowBufferManager:
    """
    Arrow 데이터의 메모리 효율적 관리자.
    배치 단위로 데이터를 축적하고 임계점 도달 시 플러시.
    """
    
    def __init__(self, capacity: int = 1000, flush_threshold: float = 0.8):
        self.capacity = capacity
        self.flush_threshold = flush_threshold
        self._buffers: Dict[str, List[pa.RecordBatch]] = {}
        self._row_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def add_batch(self, table_name: str, batch: pa.RecordBatch) -> bool:
        """배치 추가. 임계점 도달 시 True 반환 (플러시 필요 신호)"""
        with self._lock:
            if table_name not in self._buffers:
                self._buffers[table_name] = []
                self._row_counts[table_name] = 0
            
            self._buffers[table_name].append(batch)
            self._row_counts[table_name] += batch.num_rows
            
            return self._row_counts[table_name] >= self.capacity * self.flush_threshold
    
    def get_and_clear(self, table_name: str) -> Optional[pa.Table]:
        """축적된 배치를 Table로 병합 후 버퍼 클리어"""
        with self._lock:
            if table_name not in self._buffers or not self._buffers[table_name]:
                return None
            
            batches = self._buffers[table_name]
            self._buffers[table_name] = []
            self._row_counts[table_name] = 0
            
            return pa.Table.from_batches(batches)
    
    def get_stats(self) -> Dict[str, int]:
        """현재 버퍼 상태 반환"""
        with self._lock:
            return dict(self._row_counts)


# =============================================================================
# SurrealArrowBridge (Core SSOT Implementation)
# =============================================================================

class SurrealArrowBridge:
    """
    SurrealDB ↔ Apache Arrow 양방향 브릿지.
    
    핵심 기능:
    1. connect(): DB 연결 (실패 시 memory_mode 자동 전환)
    2. push_batch(): Arrow Table → SurrealDB CREATE/INSERT
    3. pull_batch(): SurrealQL → Arrow Table
    4. 모든 작업은 memory_mode에서도 동작 (Graceful Degradation)
    """
    
    # 기본 연결 설정
    DEFAULT_URL = os.getenv("SURREAL_URL", "ws://localhost:8000/rpc")
    DEFAULT_NS = os.getenv("SURREAL_NS", "ain")
    DEFAULT_DB = os.getenv("SURREAL_DB", "core")
    DEFAULT_USER = os.getenv("SURREAL_USER", "root")
    DEFAULT_PASS = os.getenv("SURREAL_PASS", "root")
    
    def __init__(self, url: str = None, namespace: str = None, database: str = None):
        self.url = url or self.DEFAULT_URL
        self.namespace = namespace or self.DEFAULT_NS
        self.database = database or self.DEFAULT_DB
        
        # 상태 플래그
        self.connected = False
        self.memory_mode = False  # DB 연결 실패 시 True
        
        # 클라이언트 인스턴스
        self._client: Optional[Surreal] = None
        self._lock = asyncio.Lock()
        
        # 메모리 모드용 인메모리 스토리지
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}
        
        # 버퍼 매니저
        self.buffer_manager = ArrowBufferManager()
        
        # 디스크 스필러 (대용량 처리용)
        self.spiller = ArrowDiskSpiller() if HAS_SPILLER else None
    
    async def connect(self) -> bool:
        """
        SurrealDB 연결 시도.
        실패 시 memory_mode를 활성화하여 시스템 붕괴 방지.
        """
        if not HAS_SURREAL:
            print("⚠️ SurrealDB 패키지 없음. Memory-Only 모드 활성화.")
            self.memory_mode = True
            return False
        
        async with self._lock:
            try:
                self._client = Surreal(self.url)
                await self._client.connect()
                await self._client.signin({
                    "username": self.DEFAULT_USER,
                    "password": self.DEFAULT_PASS
                })
                await self._client.use(self.namespace, self.database)
                
                self.connected = True
                self.memory_mode = False
                print(f"✅ SurrealDB 연결 성공: {self.url} ({self.namespace}/{self.database})")
                return True
                
            except Exception as e:
                print(f"⚠️ SurrealDB 연결 실패: {e}")
                print("   → Memory-Only 모드로 전환합니다.")
                self.connected = False
                self.memory_mode = True
                self._client = None
                return False
    
    async def close(self):
        """연결 종료"""
        if self._client:
            try:
                await self._client.close()
            except:
                pass
            self._client = None
        self.connected = False
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # =========================================================================
    # Core CRUD Operations
    # =========================================================================
    
    async def push_batch(self, arrow_table: pa.Table, table_name: str) -> bool:
        """
        Arrow Table을 SurrealDB에 배치 저장.
        
        Args:
            arrow_table: 저장할 Arrow Table
            table_name: SurrealDB 테이블명
        
        Returns:
            성공 여부
        """
        if arrow_table is None or arrow_table.num_rows == 0:
            print("⚠️ 저장할 데이터가 없습니다.")
            return False
        
        # Arrow Table → Python Dict 리스트 변환
        records = arrow_table.to_pylist()
        
        if self.memory_mode:
            return self._push_to_memory(records, table_name)
        
        return await self._push_to_surreal(records, table_name)
    
    async def _push_to_surreal(self, records: List[Dict], table_name: str) -> bool:
        """SurrealDB에 실제 저장"""
        if not self._client:
            print("⚠️ DB 클라이언트 없음. 메모리 저장으로 대체.")
            return self._push_to_memory(records, table_name)
        
        try:
            # 배치 처리: asyncio.gather로 병렬 실행
            batch_size = 100
            tasks = []
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                task = self._insert_batch(table_name, batch)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 에러 체크
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                print(f"⚠️ 일부 배치 저장 실패: {len(errors)}/{len(tasks)}")
                # 실패한 데이터는 메모리에 백업
                for err_idx, err in enumerate(errors):
                    if err_idx < len(records):
                        self._push_to_memory([records[err_idx]], f"{table_name}_failed")
            
            success_count = len(results) - len(errors)
            print(f"✅ SurrealDB 저장: {success_count * batch_size} rows → {table_name}")
            return len(errors) == 0
            
        except Exception as e:
            print(f"❌ SurrealDB 저장 실패: {e}")
            # 전체 실패 시 메모리 백업
            return self._push_to_memory(records, table_name)
    
    async def _insert_batch(self, table_name: str, batch: List[Dict]) -> bool:
        """단일 배치 UPSERT 실행 (존재하면 업데이트, 없으면 생성)"""
        success_count = 0
        error_count = 0
        
        for record in batch:
            record_id = record.get('id', 'unknown')
            try:
                # timestamp 필드 처리 (datetime → ISO string)
                processed = self._process_record_for_insert(record)
                
                # UPSERT 쿼리 실행 (CREATE or UPDATE)
                record_id = processed.pop('id', None)
                if record_id:
                    full_id = f"{table_name}:{record_id}"
                    # SurrealDB 2.x: Raw SQL UPSERT
                    import json as json_lib
                    content_json = json_lib.dumps(processed, ensure_ascii=False, default=str)
                    query = f"UPSERT {full_id} CONTENT {content_json};"
                    result = await self._client.query(query)
                    print(f"✅ Upserted: {full_id}")
                    success_count += 1
                else:
                    result = await self._client.create(table_name, processed)
                    print(f"✅ Created: {table_name} (auto-id)")
                    success_count += 1
            except Exception as e:
                error_count += 1
                print(f"❌ UPSERT 실패 ({table_name}:{record_id}): {e}")
                # 개별 실패는 무시하고 계속 진행
                continue
        
        print(f"📊 Batch 결과: {success_count} 성공, {error_count} 실패")
        return success_count > 0
    
    def _process_record_for_insert(self, record: Dict) -> Dict:
        """레코드를 SurrealDB INSERT용으로 전처리"""
        processed = {}
        for key, value in record.items():
            if isinstance(value, (datetime, pd.Timestamp)):
                processed[key] = value.isoformat()
            elif isinstance(value, np.integer):
                processed[key] = int(value)
            elif isinstance(value, np.floating):
                processed[key] = float(value)
            elif pd.isna(value):
                processed[key] = None
            else:
                processed[key] = value
        return processed
    
    def _push_to_memory(self, records: List[Dict], table_name: str) -> bool:
        """메모리 스토리지에 저장 (Fallback)"""
        if table_name not in self._memory_store:
            self._memory_store[table_name] = []
        
        self._memory_store[table_name].extend(records)
        print(f"📝 Memory 저장: {len(records)} rows → {table_name} (총 {len(self._memory_store[table_name])} rows)")
        return True
    
    async def pull_batch(self, query: str = None, table_name: str = None) -> Optional[pa.Table]:
        """
        SurrealDB에서 데이터를 Arrow Table로 인출.
        
        Args:
            query: SurrealQL 쿼리 (우선)
            table_name: 테이블명 (query 없을 시 SELECT * FROM table_name)
        
        Returns:
            Arrow Table 또는 None
        """
        if self.memory_mode:
            return self._pull_from_memory(table_name)
        
        return await self._pull_from_surreal(query, table_name)
    
    async def _pull_from_surreal(self, query: str = None, table_name: str = None) -> Optional[pa.Table]:
        """SurrealDB에서 실제 인출"""
        if not self._client:
            return self._pull_from_memory(table_name)
        
        try:
            # 쿼리 결정
            if query:
                sql = query
            elif table_name:
                sql = f"SELECT * FROM {table_name}"
            else:
                print("⚠️ 쿼리 또는 테이블명이 필요합니다.")
                return None
            
            # 쿼리 실행
            result = await self._client.query(sql)
            
            # 결과 파싱 (SurrealDB 응답 구조에 따라)
            if not result or len(result) == 0:
                return None
            
            # SurrealDB 결과는 보통 [{"result": [...], "status": "OK"}] 형태
            records = []
            for res in result:
                if isinstance(res, dict) and 'result' in res:
                    records.extend(res['result'])
                elif isinstance(res, list):
                    records.extend(res)
                elif isinstance(res, dict):
                    records.append(res)
            
            if not records:
                return None
            
            # Dict List → Arrow Table
            return self._records_to_arrow(records)
            
        except Exception as e:
            print(f"❌ SurrealDB 인출 실패: {e}")
            return self._pull_from_memory(table_name)
    
    def _pull_from_memory(self, table_name: str) -> Optional[pa.Table]:
        """메모리 스토리지에서 인출 (Fallback)"""
        if not table_name or table_name not in self._memory_store:
            return None
        
        records = self._memory_store.get(table_name, [])
        if not records:
            return None
        
        print(f"📖 Memory 인출: {len(records)} rows ← {table_name}")
        return self._records_to_arrow(records)
    
    def _records_to_arrow(self, records: List[Dict]) -> pa.Table:
        """Dict 리스트를 Arrow Table로 변환"""
        if not records:
            return None
        
        # Pandas DataFrame 경유 (타입 추론 활용)
        df = pd.DataFrame(records)
        return pa.Table.from_pandas(df, preserve_index=False)
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    async def query(self, sql: str) -> List[Dict]:
        """Raw SurrealQL 쿼리 실행"""
        if self.memory_mode or not self._client:
            print("⚠️ Memory 모드에서는 raw query를 지원하지 않습니다.")
            return []
        
        try:
            result = await self._client.query(sql)
            records = []
            for res in result:
                if isinstance(res, dict) and 'result' in res:
                    records.extend(res['result'])
                elif isinstance(res, list):
                    records.extend(res)
            return records
        except Exception as e:
            print(f"❌ 쿼리 실패: {e}")
            return []
    
    def query_sync(self, sql: str) -> List[Dict]:
        """동기 쿼리 래퍼"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 이벤트 루프가 실행 중인 경우
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.query(sql))
                    return future.result()
            else:
                return loop.run_until_complete(self.query(sql))
        except RuntimeError:
            return asyncio.run(self.query(sql))
    
    def push_batch_sync(self, arrow_table: pa.Table, table_name: str) -> bool:
        """동기 push_batch 래퍼"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.push_batch(arrow_table, table_name))
                    return future.result()
            else:
                return loop.run_until_complete(self.push_batch(arrow_table, table_name))
        except RuntimeError as e:
            print(f"⚠️ push_batch_sync RuntimeError: {e}")
            return asyncio.run(self.push_batch(arrow_table, table_name))
        except Exception as e:
            print(f"❌ push_batch_sync 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """브릿지 상태 정보"""
        return {
            "connected": self.connected,
            "memory_mode": self.memory_mode,
            "url": self.url,
            "namespace": self.namespace,
            "database": self.database,
            "memory_tables": list(self._memory_store.keys()),
            "memory_row_counts": {k: len(v) for k, v in self._memory_store.items()},
            "buffer_stats": self.buffer_manager.get_stats()
        }
    
    # =========================================================================
    # Evolution State Management (Step 3 특화)
    # =========================================================================
    
    async def save_evolution_state(self, state_id: str, batch: pa.RecordBatch) -> bool:
        """진화 상태를 SurrealDB에 저장"""
        table = pa.Table.from_batches([batch])
        return await self.push_batch(table, f"evolution_state_{state_id}")
    
    async def load_evolution_state(self, state_id: str) -> Optional[pa.RecordBatch]:
        """저장된 진화 상태 로드"""
        table = await self.pull_batch(table_name=f"evolution_state_{state_id}")
        if table and table.num_rows > 0:
            return table.to_batches()[0]
        return None


# =============================================================================
# Module-Level Singleton & Convenience Functions
# =============================================================================

_bridge_instance: Optional[SurrealArrowBridge] = None
_bridge_lock = threading.Lock()


def get_bridge() -> SurrealArrowBridge:
    """싱글톤 브릿지 인스턴스 반환"""
    global _bridge_instance
    with _bridge_lock:
        if _bridge_instance is None:
            _bridge_instance = SurrealArrowBridge()
        return _bridge_instance


async def get_connected_bridge() -> SurrealArrowBridge:
    """연결된 브릿지 인스턴스 반환"""
    bridge = get_bridge()
    if not bridge.connected and not bridge.memory_mode:
        await bridge.connect()
    return bridge


def quick_push(data: Union[pa.Table, List[Dict], pd.DataFrame], table_name: str) -> bool:
    """빠른 데이터 푸시 (동기)"""
    bridge = get_bridge()
    
    # 데이터 타입 변환
    if isinstance(data, list):
        table = pa.Table.from_pylist(data)
    elif isinstance(data, pd.DataFrame):
        table = pa.Table.from_pandas(data)
    elif isinstance(data, pa.Table):
        table = data
    else:
        print(f"⚠️ 지원하지 않는 데이터 타입: {type(data)}")
        return False
    
    return bridge.push_batch_sync(table, table_name)


def quick_pull(table_name: str) -> Optional[pa.Table]:
    """빠른 데이터 인출 (동기)"""
    bridge = get_bridge()
    try:
        return asyncio.run(bridge.pull_batch(table_name=table_name))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(bridge.pull_batch(table_name=table_name))