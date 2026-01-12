"""
AIN Database Layer: Arrow Schema Definitions (SSOT)
===================================================
시스템 전역에서 사용되는 Arrow 스키마의 단일 진실 공급원(Single Source of Truth).

모든 데이터 파이프라인 컴포넌트는 이 모듈의 스키마를 임포트하여 사용해야 한다.

Step 3 Evolution - Full-Cycle Persistence:
- get_history_schema(): Nexus 진화 기록 저장용 스키마
- get_interaction_schema(): 대화 로그 저장용 스키마
- get_node_schema(): 지식 그래프 노드용 스키마
"""

import pyarrow as pa
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


# =============================================================================
# Core Schema Definitions
# =============================================================================

def get_node_schema() -> pa.Schema:
    """
    NodeSchema: 지식 그래프의 단일 노드를 표현
    
    FactCore의 KnowledgeNode와 1:1 매핑된다.
    SurrealDB의 `node` 테이블 구조와 호환.
    """
    return pa.schema([
        pa.field("id", pa.string(), nullable=False),
        pa.field("label", pa.string(), nullable=False),
        pa.field("data_json", pa.string()),  # JSON 직렬화된 데이터
        pa.field("edges_count", pa.int32()),
        pa.field("timestamp", pa.timestamp('ms')),
    ])


def get_history_schema() -> pa.Schema:
    """
    HistorySchema: Nexus의 진화 기록(Evolution History)을 저장하기 위한 스키마
    
    evolution_history.json의 각 레코드와 1:1 매핑.
    SurrealDB의 `history` 테이블 구조와 호환.
    
    Fields:
        - timestamp: 진화 발생 시각 (ISO 8601)
        - type: 이벤트 유형 (EVOLUTION, ERROR, SYSTEM 등)
        - action: 수행된 액션 (Create, Update, Delete)
        - file: 대상 파일명
        - description: 진화 내용 상세 설명
        - status: 결과 상태 (success, failed, pending)
        - error: 에러 메시지 (nullable)
    """
    return pa.schema([
        pa.field("timestamp", pa.string(), nullable=False),  # ISO 8601 문자열
        pa.field("type", pa.string(), nullable=False),
        pa.field("action", pa.string(), nullable=False),
        pa.field("file", pa.string(), nullable=False),
        pa.field("description", pa.string()),
        pa.field("status", pa.string(), nullable=False),
        pa.field("error", pa.string(), nullable=True),
    ])


def get_interaction_schema() -> pa.Schema:
    """
    InteractionSchema: 사용자 대화 로그 저장용 스키마
    
    dialogue_memory.json의 각 대화 레코드와 호환.
    SurrealDB의 `interaction` 테이블 구조와 호환.
    
    Fields:
        - session_id: 대화 세션 ID
        - timestamp: 대화 발생 시각
        - role: 발화자 (user, assistant, system)
        - content: 대화 내용
        - intent: 추출된 의도 (nullable)
        - metadata_json: 추가 메타데이터 (JSON)
    """
    return pa.schema([
        pa.field("session_id", pa.string(), nullable=False),
        pa.field("timestamp", pa.timestamp('ms'), nullable=False),
        pa.field("role", pa.string(), nullable=False),
        pa.field("content", pa.string(), nullable=False),
        pa.field("intent", pa.string(), nullable=True),
        pa.field("metadata_json", pa.string(), nullable=True),
    ])


def get_metrics_schema() -> pa.Schema:
    """
    MetricsSchema: Nexus 성장 지표 저장용 스키마
    
    nexus_metrics.json과 호환.
    """
    return pa.schema([
        pa.field("snapshot_time", pa.timestamp('ms'), nullable=False),
        pa.field("growth_score", pa.int32(), nullable=False),
        pa.field("level", pa.int32(), nullable=False),
        pa.field("total_evolutions", pa.int32(), nullable=False),
    ])


def get_system_state_schema() -> pa.Schema:
    """
    SystemStateSchema: AIN 시스템 상태 스냅샷용 스키마
    """
    return pa.schema([
        pa.field("snapshot_id", pa.string(), nullable=False),
        pa.field("timestamp", pa.timestamp('ms'), nullable=False),
        pa.field("component", pa.string(), nullable=False),
        pa.field("version", pa.string()),
        pa.field("state_json", pa.string()),  # 전체 상태를 JSON으로 직렬화
    ])


# =============================================================================
# Schema Utilities
# =============================================================================

def validate_against_schema(table: pa.Table, schema: pa.Schema) -> bool:
    """
    주어진 테이블이 스키마와 호환되는지 검증
    
    Returns:
        bool: 호환 여부
    """
    try:
        # 필드 이름 비교
        table_fields = set(table.schema.names)
        schema_fields = set(schema.names)
        
        # 필수 필드가 모두 있는지 확인
        required_fields = {f.name for f in schema if not f.nullable}
        missing = required_fields - table_fields
        
        if missing:
            print(f"⚠️ Schema Validation: Missing required fields: {missing}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Schema Validation Error: {e}")
        return False


def create_empty_table(schema: pa.Schema) -> pa.Table:
    """
    주어진 스키마로 빈 테이블 생성
    """
    arrays = []
    for field in schema:
        if pa.types.is_string(field.type):
            arrays.append(pa.array([], type=pa.string()))
        elif pa.types.is_int32(field.type):
            arrays.append(pa.array([], type=pa.int32()))
        elif pa.types.is_timestamp(field.type):
            arrays.append(pa.array([], type=field.type))
        else:
            arrays.append(pa.array([], type=field.type))
    
    return pa.Table.from_arrays(arrays, schema=schema)


def history_record_to_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    진화 기록 딕셔너리를 스키마 호환 형태로 정규화
    """
    return {
        "timestamp": str(record.get("timestamp", datetime.now().isoformat())),
        "type": str(record.get("type", "UNKNOWN")),
        "action": str(record.get("action", "Unknown")),
        "file": str(record.get("file", "")),
        "description": str(record.get("description", "")),
        "status": str(record.get("status", "unknown")),
        "error": record.get("error"),  # None 허용
    }


# =============================================================================
# Schema Registry (Singleton Pattern)
# =============================================================================

class SchemaRegistry:
    """
    모든 스키마에 대한 중앙 집중식 레지스트리
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._schemas = {
                "node": get_node_schema(),
                "history": get_history_schema(),
                "interaction": get_interaction_schema(),
                "metrics": get_metrics_schema(),
                "system_state": get_system_state_schema(),
            }
        return cls._instance
    
    def get(self, name: str) -> Optional[pa.Schema]:
        """스키마 이름으로 조회"""
        return self._schemas.get(name)
    
    def register(self, name: str, schema: pa.Schema):
        """커스텀 스키마 등록"""
        self._schemas[name] = schema
    
    def list_schemas(self) -> List[str]:
        """등록된 모든 스키마 이름 반환"""
        return list(self._schemas.keys())


def get_schema_registry() -> SchemaRegistry:
    """SchemaRegistry 싱글톤 인스턴스 반환"""
    return SchemaRegistry()