"""
Database Reflex Bridge: Reflex Knowledge to Arrow Adapter
Step 8: Intuition - System 1 Data Integration

이 모듈은 학습된 반사 행동(Reflexes)을 Apache Arrow 형식으로 변환하여
고성능 분석 및 CorpusCallosum을 통한 전송을 지원한다.

Architecture:
    ReflexStore (JSON) -> ReflexArrowBridge -> Arrow Table -> Nexus/SurrealDB
"""

import json
import pyarrow as pa
from typing import List, Dict, Any, Optional
from datetime import datetime

# Schema Registry 연동 시도
try:
    from database.arrow_schema import get_schema_registry
    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False


def get_reflex_schema() -> pa.Schema:
    """
    ReflexSchema: 반사 행동 데이터 스키마
    ReflexRegistry 및 learned_reflexes.json 구조와 호환
    """
    return pa.schema([
        pa.field("id", pa.string(), nullable=False),
        pa.field("type", pa.string(), nullable=False),
        pa.field("pattern", pa.string()),
        pa.field("handler_type", pa.string()),
        pa.field("created_at", pa.timestamp("ms")),
        pa.field("confidence", pa.float32()),
        pa.field("usage_count", pa.int32()),
        pa.field("metadata_json", pa.string()),
    ])


class ReflexArrowBridge:
    """
    Reflex 데이터를 Arrow Table로 변환하는 브릿지
    
    학습된 반사 행동(Learned Reflexes)을 Apache Arrow 포맷으로 변환하여
    고성능 분석 파이프라인에 통합한다.
    
    Features:
    
    Usage:
        bridge = ReflexArrowBridge()
        
        # JSON -> Arrow
        reflexes = [{"name": "greet", "type": "quick_fix", ...}]
        table = bridge.convert_to_arrow(reflexes)
        
        # Arrow -> JSON
        reflexes_back = bridge.convert_from_arrow(table)
    """
    
    def __init__(self):
        self.schema = get_reflex_schema()
        self._register_schema()

    def _register_schema(self):
        """SchemaRegistry에 스키마 등록 (런타임 확장)"""
        if HAS_REGISTRY:
            try:
                registry = get_schema_registry()
                registry.register("reflex", self.schema)
                print("✅ Reflex schema registered to global registry")
            except Exception as e:
                print(f"⚠️ Reflex schema registration failed: {e}")

    def _create_empty_table(self) -> pa.Table:
        """빈 Arrow Table 생성"""
        arrays = []
        for field in self.schema:
            if pa.types.is_string(field.type):
                arrays.append(pa.array([], type=pa.string()))
            elif pa.types.is_int32(field.type):
                arrays.append(pa.array([], type=pa.int32()))
            elif pa.types.is_float32(field.type):
                arrays.append(pa.array([], type=pa.float32()))
            elif pa.types.is_timestamp(field.type):
                arrays.append(pa.array([], type=field.type))
            else:
                arrays.append(pa.array([], type=field.type))
        return pa.Table.from_arrays(arrays, schema=self.schema)

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """타임스탬프 문자열을 datetime으로 변환"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def convert_to_arrow(self, reflexes: List[Dict[str, Any]]) -> pa.Table:
        """
        Reflex 딕셔너리 리스트를 Arrow Table로 변환
        
        Args:
            reflexes: 반사 행동 딕셔너리 리스트
                      각 딕셔너리는 name/id, type, pattern 등을 포함
        
        Returns:
            Arrow Table (reflex 스키마 준수)
        """
        if not reflexes:
            return self._create_empty_table()

        ids = []
        types = []
        patterns = []
        handlers = []
        created_ats = []
        confidences = []
        usage_counts = []
        metadata_jsons = []

        for r in reflexes:
            ids.append(str(r.get("name", r.get("id", "unknown"))))
            types.append(str(r.get("type", "unknown")))
            patterns.append(str(r.get("pattern", "")))
            handlers.append(str(r.get("handler_type", "default")))
            
            ts = r.get("created_at")
            parsed_ts = self._parse_timestamp(ts)
            created_ats.append(parsed_ts)
            
            conf = r.get("confidence")
            if conf is not None:
                try:
                    confidences.append(float(conf))
                except (ValueError, TypeError):
                    confidences.append(0.0)
            else:
                confidences.append(0.0)
            
            count = r.get("usage_count")
            if count is not None:
                try:
                    usage_counts.append(int(count))
                except (ValueError, TypeError):
                    usage_counts.append(0)
            else:
                usage_counts.append(0)
            
            metadata = r.get("metadata", {})
            if isinstance(metadata, dict):
                metadata_jsons.append(json.dumps(metadata, ensure_ascii=False))
            elif isinstance(metadata, str):
                metadata_jsons.append(metadata)
            else:
                metadata_jsons.append("{}")

        table = pa.table({
            "id": pa.array(ids, type=pa.string()),
            "type": pa.array(types, type=pa.string()),
            "pattern": pa.array(patterns, type=pa.string()),
            "handler_type": pa.array(handlers, type=pa.string()),
            "created_at": pa.array(created_ats, type=pa.timestamp("ms")),
            "confidence": pa.array(confidences, type=pa.float32()),
            "usage_count": pa.array(usage_counts, type=pa.int32()),
            "metadata_json": pa.array(metadata_jsons, type=pa.string()),
        })

        return table

    def convert_from_arrow(self, table: pa.Table) -> List[Dict[str, Any]]:
        """
        Arrow Table을 Reflex 딕셔너리 리스트로 역변환
        
        Args:
            table: Arrow Table (reflex 스키마)
        
        Returns:
            반사 행동 딕셔너리 리스트
        """
        if table is None or table.num_rows == 0:
            return []

        reflexes = []
        df = table.to_pydict()

        for i in range(table.num_rows):
            reflex = {
                "name": df["id"][i],
                "id": df["id"][i],
                "type": df["type"][i],
                "pattern": df["pattern"][i],
                "handler_type": df["handler_type"][i],
                "confidence": df["confidence"][i],
                "usage_count": df["usage_count"][i],
            }
            
            ts = df["created_at"][i]
            if ts is not None:
                if hasattr(ts, "isoformat"):
                    reflex["created_at"] = ts.isoformat()
                else:
                    reflex["created_at"] = str(ts)
            else:
                reflex["created_at"] = None
            
            metadata_str = df["metadata_json"][i]
            if metadata_str:
                try:
                    reflex["metadata"] = json.loads(metadata_str)
                except json.JSONDecodeError:
                    reflex["metadata"] = {}
            else:
                reflex["metadata"] = {}

            reflexes.append(reflex)

        return reflexes

    def merge_tables(self, tables: List[pa.Table]) -> pa.Table:
        """
        여러 Arrow Table을 하나로 병합
        
        Args:
            tables: 병합할 Arrow Table 리스트
        
        Returns:
            병합된 Arrow Table
        """
        valid_tables = [t for t in tables if t is not None and t.num_rows > 0]
        if not valid_tables:
            return self._create_empty_table()
        if len(valid_tables) == 1:
            return valid_tables[0]
        return pa.concat_tables(valid_tables)

    def filter_by_type(self, table: pa.Table, reflex_type: str) -> pa.Table:
        """
        특정 타입의 반사 행동만 필터링
        
        Args:
            table: 원본 Arrow Table
            reflex_type: 필터링할 타입 (예: "quick_fix", "ignore")
        
        Returns:
            필터링된 Arrow Table
        """
        if table is None or table.num_rows == 0:
            return self._create_empty_table()

        import pyarrow.compute as pc
        mask = pc.equal(table.column("type"), reflex_type)
        return table.filter(mask)

    def get_statistics(self, table: pa.Table) -> Dict[str, Any]:
        """
        반사 행동 테이블의 통계 정보 반환
        
        Args:
            table: Arrow Table
        
        Returns:
            통계 딕셔너리 (총 개수, 타입별 개수, 평균 신뢰도 등)
        """
        if table is None or table.num_rows == 0:
            return {
                "total_count": 0,
                "type_counts": {},
                "avg_confidence": 0.0,
                "total_usage": 0,
            }

        import pyarrow.compute as pc

        type_counts = {}
        types = table.column("type").to_pylist()
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1

        confidences = table.column("confidence").to_pylist()
        valid_confidences = [c for c in confidences if c is not None]
        avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0

        usage_counts = table.column("usage_count").to_pylist()
        total_usage = sum(u for u in usage_counts if u is not None)

        return {
            "total_count": table.num_rows,
            "type_counts": type_counts,
            "avg_confidence": round(avg_confidence, 4),
            "total_usage": total_usage,
        }


def get_reflex_arrow_bridge() -> ReflexArrowBridge:
    """ReflexArrowBridge 싱글톤 인스턴스 반환"""
    if not hasattr(get_reflex_arrow_bridge, "_instance"):
        get_reflex_arrow_bridge._instance = ReflexArrowBridge()
    return get_reflex_arrow_bridge._instance