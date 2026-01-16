"""
LanceDB Vector Bridge - Step 4: Semantic Memory Store
=====================================================
AIN의 의미론적 기억을 위한 벡터 데이터베이스 브릿지.
LanceDB를 통해 텍스트를 벡터로 저장하고, 유사도 기반 검색(ANN)을 수행한다.

Architecture:
    Nexus (Application) -> LanceBridge (Driver) -> LanceDB (Storage)
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# LanceDB & Arrow imports with graceful fallback
try:
    import lancedb
    import pyarrow as pa
    LANCE_AVAILABLE = True
except ImportError:
    LANCE_AVAILABLE = False
    print("⚠️ LanceDB 또는 PyArrow 미설치. Vector Memory 비활성화.")


class LanceBridge:
    """
    LanceDB Vector Store 싱글톤 브릿지.
    
    Nexus가 기억을 벡터화하여 저장하고, 의미 기반으로 검색할 수 있게 한다.
    Step 3에서 확립된 Arrow 기반 Zero-Copy 원칙을 준수한다.
    """
    
    _instance: Optional["LanceBridge"] = None
    
    # 벡터 차원 (Gemini text-embedding-004 기준)
    VECTOR_DIM = 768
    
    # 기본 저장 경로
    DEFAULT_DB_PATH = os.environ.get("LANCEDB_PATH", "/data/lancedb")
    
    def __new__(cls, db_path: str = None):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        
        self._db_path = db_path or self.DEFAULT_DB_PATH
        self._db = None
        self._table = None
        self._connected = False
        
        if LANCE_AVAILABLE:
            self._connect()
        
        self._initialized = True
    
    def _connect(self) -> bool:
        """LanceDB 연결 및 테이블 초기화"""
        try:
            # 디렉토리 생성
            os.makedirs(self._db_path, exist_ok=True)

            # 영속성 마커 확인 (Railway 재배포 감지)
            marker = os.path.join(self._db_path, ".persistence_marker")
            if not os.path.exists(marker):
                print("⚠️ 새 LanceDB 인스턴스 감지 (재배포 후?)")
                with open(marker, 'w') as f:
                    f.write(datetime.now().isoformat())
            else:
                with open(marker, 'r') as f:
                    created = f.read().strip()
                print(f"✅ LanceDB 영속성 확인: {created} 이후 유지됨")

            # LanceDB 연결
            self._db = lancedb.connect(self._db_path)
            
            # 테이블 존재 여부 확인 및 생성
            existing_tables = self._db.table_names()
            if "memory_bank" not in existing_tables:
                self._create_memory_table()
            else:
                self._table = self._db.open_table("memory_bank")
            
            self._connected = True
            print(f"✅ LanceDB 연결 성공: {self._db_path}")
            return True
            
        except Exception as e:
            print(f"❌ LanceDB 연결 실패: {e}")
            self._connected = False
            return False
    
    def _create_memory_table(self):
        """메모리 테이블 스키마 정의 및 생성"""
        # PyArrow 스키마 정의
        schema = pa.schema([
            ("id", pa.string()),
            ("text", pa.string()),
            ("vector", pa.list_(pa.float32(), self.VECTOR_DIM)),
            ("memory_type", pa.string()),  # episodic, semantic, procedural
            ("source", pa.string()),
            ("timestamp", pa.string()),
            ("metadata", pa.string()),  # JSON 직렬화된 추가 정보
        ])
        
        # 초기 더미 데이터로 테이블 생성 (LanceDB 요구사항)
        initial_data = pa.table({
            "id": ["init_0"],
            "text": ["AIN Memory System Initialized"],
            "vector": [[0.0] * self.VECTOR_DIM],
            "memory_type": ["system"],
            "source": ["lance_bridge"],
            "timestamp": [datetime.now().isoformat()],
            "metadata": ["{}"],
        })
        
        self._table = self._db.create_table("memory_bank", initial_data)
        print("📦 memory_bank 테이블 생성 완료")
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self._db is not None
    
    def add_memory(
        self,
        text: str,
        vector: List[float],
        memory_type: str = "episodic",
        source: str = "unknown",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        새로운 기억을 벡터 DB에 저장한다.
        
        Args:
            text: 기억할 텍스트
            vector: 텍스트의 임베딩 벡터 (VECTOR_DIM 차원)
            memory_type: 기억 유형 (episodic, semantic, procedural)
            source: 기억의 출처 (evolution, conversation 등)
            metadata: 추가 메타데이터 (JSON 직렬화됨)
        
        Returns:
            성공 여부
        """
        if not self.is_connected:
            print("⚠️ LanceDB 미연결. 메모리 저장 스킵.")
            return False
        
        try:
            import json
            
            # 벡터 차원 검증
            if len(vector) != self.VECTOR_DIM:
                print(f"⚠️ 벡터 차원 불일치: {len(vector)} != {self.VECTOR_DIM}")
                # 패딩 또는 트렁케이션
                if len(vector) < self.VECTOR_DIM:
                    vector = vector + [0.0] * (self.VECTOR_DIM - len(vector))
                else:
                    vector = vector[:self.VECTOR_DIM]
            
            # 새 레코드 생성
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            new_data = pa.table({
                "id": [memory_id],
                "text": [text],
                "vector": [vector],
                "memory_type": [memory_type],
                "source": [source],
                "timestamp": [datetime.now().isoformat()],
                "metadata": [json.dumps(metadata or {}, ensure_ascii=False)],
            })
            
            # 테이블에 추가
            self._table.add(new_data)
            print(f"💾 기억 저장: {memory_id} ({len(text)} chars)")
            return True
            
        except Exception as e:
            print(f"❌ 기억 저장 실패: {e}")
            return False
    
    def search_memory(
        self,
        query_vector: List[float],
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 기반으로 기억을 검색한다 (ANN Search).
        
        Args:
            query_vector: 검색 쿼리의 임베딩 벡터
            limit: 반환할 최대 결과 수
            memory_type: 특정 기억 유형으로 필터링 (선택)
        
        Returns:
            유사한 기억 목록 (거리 순 정렬)
        """
        if not self.is_connected:
            return []
        
        try:
            import json
            
            # 벡터 차원 맞추기
            if len(query_vector) != self.VECTOR_DIM:
                if len(query_vector) < self.VECTOR_DIM:
                    query_vector = query_vector + [0.0] * (self.VECTOR_DIM - len(query_vector))
                else:
                    query_vector = query_vector[:self.VECTOR_DIM]
            
            # ANN 검색 실행
            results = self._table.search(query_vector).limit(limit).to_pandas()
            
            # 결과 변환
            memories = []
            for _, row in results.iterrows():
                memory = {
                    "id": row["id"],
                    "text": row["text"],
                    "memory_type": row["memory_type"],
                    "source": row["source"],
                    "timestamp": row["timestamp"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "distance": row.get("_distance", 0.0),
                }
                
                # 필터링 적용
                if memory_type and memory["memory_type"] != memory_type:
                    continue
                    
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"❌ 기억 검색 실패: {e}")
            return []
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 저장된 기억을 시간순으로 반환"""
        if not self.is_connected:
            return []
        
        try:
            import json
            
            # 전체 데이터에서 최근 N개 추출
            df = self._table.to_pandas()
            df = df.sort_values("timestamp", ascending=False).head(limit)
            
            memories = []
            for _, row in df.iterrows():
                memories.append({
                    "id": row["id"],
                    "text": row["text"],
                    "memory_type": row["memory_type"],
                    "source": row["source"],
                    "timestamp": row["timestamp"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                })
            
            return memories
            
        except Exception as e:
            print(f"❌ 최근 기억 조회 실패: {e}")
            return []
    
    def count_memories(self) -> int:
        """저장된 기억의 총 개수"""
        if not self.is_connected:
            return 0
        try:
            return len(self._table.to_pandas())
        except:
            return 0
    
    def close(self):
        """연결 종료 (현재 LanceDB는 명시적 종료 불필요)"""
        self._connected = False
        print("🔌 LanceDB 연결 종료")


# 싱글톤 인스턴스 접근 헬퍼
def get_lance_bridge() -> LanceBridge:
    """전역 LanceBridge 인스턴스 반환"""
    return LanceBridge()
