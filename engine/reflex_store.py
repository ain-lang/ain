"""
Engine Reflex Store: 학습된 반사 행동 영속화
Step 8: Intuition - Learned Reflex Persistence

이 모듈은 ReflexLearner가 학습한 반사 행동을 파일 시스템(JSON)에 저장하고,
시스템 부팅 시 이를 로드하여 ReflexRegistry에 등록할 수 있도록 데이터를 제공한다.

Step 8 Enhancement: ReflexArrowBridge 연동
저장된 반사 행동을 Apache Arrow Table 포맷으로 내보내거나 가져오는 기능을 제공하여
고속 분석 파이프라인과 CorpusCallosum을 통한 데이터 전송을 지원한다.
"""

import os
from typing import List, Dict, Any, Optional

from nexus.storage import load_json, save_json

# Step 8: Arrow Bridge Integration
try:
    import pyarrow as pa
    from database.reflex_arrow_bridge import get_reflex_arrow_bridge, ReflexArrowBridge
    HAS_ARROW_BRIDGE = True
except ImportError:
    HAS_ARROW_BRIDGE = False
    pa = None
    ReflexArrowBridge = None


class ReflexStore:
    """
    학습된 반사 행동(Learned Reflexes) 저장소
    
    ReflexLearner가 제안하고 승인된 반사 행동을 영구 저장한다.
    저장된 데이터는 시스템 부팅 시 ReflexLearningMixin에 의해 로드되어 활성화된다.
    
    Step 8 Enhancement:
    """

    STORAGE_FILE = "learned_reflexes.json"

    def __init__(self, base_path: str = "."):
        self.file_path = os.path.join(base_path, self.STORAGE_FILE)
        self._arrow_bridge: Optional[ReflexArrowBridge] = None
        
        if HAS_ARROW_BRIDGE:
            try:
                self._arrow_bridge = get_reflex_arrow_bridge()
            except Exception as e:
                print(f"⚠️ ReflexArrowBridge 초기화 실패: {e}")

    def save_reflex(self, reflex_data: Dict[str, Any]) -> bool:
        """
        학습된 반사 행동 하나를 저장소에 추가하거나 업데이트한다.
        
        Args:
            reflex_data: {
                "name": str,          # 고유 식별자
                "type": str,          # ReflexType.value
                "pattern": str,       # 감지 패턴 (Regex)
                "handler_type": str,  # 핸들러 유형 (generic_fix, ignore 등)
                "response_template": str, # (Optional) 응답 템플릿
                "confidence": float,  # 신뢰도
                "created_at": str     # 생성 일시
            }
        
        Returns:
            bool: 저장 성공 여부
        """
        if not reflex_data or "name" not in reflex_data:
            return False

        reflexes = self.load_all()
        
        updated = False
        for i, r in enumerate(reflexes):
            if r.get("name") == reflex_data.get("name"):
                reflexes[i] = reflex_data
                updated = True
                break
        
        if not updated:
            reflexes.append(reflex_data)
            
        return save_json(self.file_path, reflexes)

    def load_all(self) -> List[Dict[str, Any]]:
        """
        저장된 모든 반사 행동 데이터를 로드한다.
        
        Returns:
            List[Dict]: 반사 행동 데이터 목록
        """
        data = load_json(self.file_path)
        if data and isinstance(data, list):
            return data
        return []

    def delete_reflex(self, name: str) -> bool:
        """
        특정 반사 행동을 삭제한다.
        
        Args:
            name: 삭제할 반사 행동의 이름
        
        Returns:
            bool: 삭제 성공 여부
        """
        reflexes = self.load_all()
        original_count = len(reflexes)
        
        reflexes = [r for r in reflexes if r.get("name") != name]
        
        if len(reflexes) < original_count:
            return save_json(self.file_path, reflexes)
        return False

    def get_reflex_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        이름으로 특정 반사 행동을 조회한다.
        
        Args:
            name: 조회할 반사 행동의 이름
        
        Returns:
            Dict or None: 반사 행동 데이터 또는 None
        """
        reflexes = self.load_all()
        for r in reflexes:
            if r.get("name") == name:
                return r
        return None

    def count(self) -> int:
        """
        저장된 반사 행동의 개수를 반환한다.
        
        Returns:
            int: 반사 행동 개수
        """
        return len(self.load_all())

    def clear_all(self) -> bool:
        """
        모든 반사 행동을 삭제한다.
        
        Returns:
            bool: 삭제 성공 여부
        """
        return save_json(self.file_path, [])

    def export_as_arrow(self) -> Optional[Any]:
        """
        저장된 반사 행동을 Arrow Table로 변환하여 반환한다.
        고속 분석 및 CorpusCallosum을 통한 전송에 사용된다.
        
        Returns:
            pa.Table or None: Arrow Table 또는 None (브릿지 미설치 시)
        """
        if not HAS_ARROW_BRIDGE or self._arrow_bridge is None:
            print("⚠️ ReflexArrowBridge 미설치. Arrow 변환 불가.")
            return None
        
        try:
            reflexes = self.load_all()
            if not reflexes:
                print("ℹ️ 저장된 반사 행동이 없습니다.")
                return self._arrow_bridge.convert_to_arrow([])
            
            table = self._arrow_bridge.convert_to_arrow(reflexes)
            print(f"✅ Arrow Table 변환 완료: {table.num_rows} rows")
            return table
        except Exception as e:
            print(f"❌ Arrow 변환 실패: {e}")
            return None

    def import_from_arrow(self, table: Any) -> bool:
        """
        Arrow Table에서 반사 행동을 로드하여 저장소에 덮어쓴다.
        외부 시스템이나 CorpusCallosum으로부터 데이터를 수신할 때 사용된다.
        
        Args:
            table: pa.Table - 반사 행동이 담긴 Arrow Table
        
        Returns:
            bool: 저장 성공 여부
        """
        if not HAS_ARROW_BRIDGE or self._arrow_bridge is None:
            print("⚠️ ReflexArrowBridge 미설치. Arrow 임포트 불가.")
            return False
        
        if table is None:
            print("⚠️ 유효하지 않은 Arrow Table입니다.")
            return False
        
        try:
            reflexes = self._arrow_bridge.convert_from_arrow(table)
            if not reflexes:
                print("ℹ️ Arrow Table에 반사 행동이 없습니다.")
                return save_json(self.file_path, [])
            
            result = save_json(self.file_path, reflexes)
            if result:
                print(f"✅ Arrow에서 {len(reflexes)}개 반사 행동 임포트 완료")
            return result
        except Exception as e:
            print(f"❌ Arrow 임포트 실패: {e}")
            return False

    def merge_from_arrow(self, table: Any) -> int:
        """
        Arrow Table의 반사 행동을 기존 저장소에 병합한다.
        중복된 이름은 업데이트하고, 새로운 항목은 추가한다.
        
        Args:
            table: pa.Table - 병합할 반사 행동이 담긴 Arrow Table
        
        Returns:
            int: 병합된 항목 수 (새로 추가 + 업데이트)
        """
        if not HAS_ARROW_BRIDGE or self._arrow_bridge is None:
            print("⚠️ ReflexArrowBridge 미설치. Arrow 병합 불가.")
            return 0
        
        if table is None:
            return 0
        
        try:
            incoming_reflexes = self._arrow_bridge.convert_from_arrow(table)
            if not incoming_reflexes:
                return 0
            
            merged_count = 0
            for reflex in incoming_reflexes:
                if self.save_reflex(reflex):
                    merged_count += 1
            
            print(f"✅ {merged_count}개 반사 행동 병합 완료")
            return merged_count
        except Exception as e:
            print(f"❌ Arrow 병합 실패: {e}")
            return 0

    def get_arrow_statistics(self) -> Dict[str, Any]:
        """
        Arrow 기반 고속 통계 분석을 수행한다.
        ReflexArrowBridge의 get_statistics() 메서드를 활용한다.
        
        Returns:
            Dict: 통계 정보 (총 개수, 타입별 개수, 평균 신뢰도 등)
        """
        if not HAS_ARROW_BRIDGE or self._arrow_bridge is None:
            return {
                "total_count": self.count(),
                "type_counts": {},
                "avg_confidence": 0.0,
                "total_usage": 0,
                "arrow_available": False
            }
        
        try:
            table = self.export_as_arrow()
            if table is None:
                return {
                    "total_count": 0,
                    "type_counts": {},
                    "avg_confidence": 0.0,
                    "total_usage": 0,
                    "arrow_available": True
                }
            
            stats = self._arrow_bridge.get_statistics(table)
            stats["arrow_available"] = True
            return stats
        except Exception as e:
            print(f"⚠️ Arrow 통계 분석 실패: {e}")
            return {
                "total_count": self.count(),
                "type_counts": {},
                "avg_confidence": 0.0,
                "total_usage": 0,
                "arrow_available": False,
                "error": str(e)
            }

    def filter_by_type_arrow(self, reflex_type: str) -> List[Dict[str, Any]]:
        """
        Arrow 기반 고속 필터링으로 특정 타입의 반사 행동만 반환한다.
        
        Args:
            reflex_type: 필터링할 반사 행동 타입 (예: "quick_fix", "ignore")
        
        Returns:
            List[Dict]: 필터링된 반사 행동 목록
        """
        if not HAS_ARROW_BRIDGE or self._arrow_bridge is None:
            reflexes = self.load_all()
            return [r for r in reflexes if r.get("type") == reflex_type]
        
        try:
            table = self.export_as_arrow()
            if table is None or table.num_rows == 0:
                return []
            
            filtered_table = self._arrow_bridge.filter_by_type(table, reflex_type)
            return self._arrow_bridge.convert_from_arrow(filtered_table)
        except Exception as e:
            print(f"⚠️ Arrow 필터링 실패, 폴백 사용: {e}")
            reflexes = self.load_all()
            return [r for r in reflexes if r.get("type") == reflex_type]

    def is_arrow_available(self) -> bool:
        """
        Arrow Bridge 사용 가능 여부를 반환한다.
        
        Returns:
            bool: Arrow Bridge 사용 가능 여부
        """
        return HAS_ARROW_BRIDGE and self._arrow_bridge is not None


_reflex_store_instance: Optional[ReflexStore] = None


def get_reflex_store(base_path: str = ".") -> ReflexStore:
    """
    ReflexStore 싱글톤 인스턴스를 반환한다.
    
    Args:
        base_path: 저장소 기본 경로
    
    Returns:
        ReflexStore: 싱글톤 인스턴스
    """
    global _reflex_store_instance
    if _reflex_store_instance is None:
        _reflex_store_instance = ReflexStore(base_path)
    return _reflex_store_instance