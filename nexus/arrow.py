"""
Nexus Arrow: Arrow Table 변환 유틸리티
"""
from typing import Optional, List, Dict, Any

import pyarrow as pa

# Arrow Schema 임포트 (SSOT)
try:
    from database.arrow_schema import get_history_schema, history_record_to_dict
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False


class ArrowConverter:
    """Arrow Table 변환 관리자"""
    
    def __init__(self):
        self._last_arrow_table = None
    
    def export_history(self, history_cache: List[Dict[str, Any]]) -> Optional[pa.Table]:
        """진화 기록을 Arrow Table로 직렬화"""
        if not history_cache:
            return None
        
        try:
            if HAS_SCHEMA:
                schema = get_history_schema()
            else:
                schema = pa.schema([
                    ("timestamp", pa.string()),
                    ("type", pa.string()),
                    ("action", pa.string()),
                    ("file", pa.string()),
                    ("description", pa.string()),
                    ("status", pa.string()),
                    ("error", pa.string()),
                ])
            
            if HAS_SCHEMA:
                records = [history_record_to_dict(r) for r in history_cache]
            else:
                records = history_cache
            
            table = pa.Table.from_pylist(records, schema=schema)
            self._last_arrow_table = table
            
            return table
            
        except Exception as e:
            print(f"❌ Arrow 직렬화 실패: {e}")
            return None
    
    def import_history(self, table: pa.Table) -> Optional[List[Dict[str, Any]]]:
        """Arrow Table에서 진화 기록 복원"""
        if table is None or table.num_rows == 0:
            return None
        
        try:
            records = table.to_pylist()
            print(f"✅ Nexus: {len(records)}개 진화 기록 복원됨")
            return records
        except Exception as e:
            print(f"❌ Arrow 역직렬화 실패: {e}")
            return None
    
    @property
    def last_table(self):
        return self._last_arrow_table
