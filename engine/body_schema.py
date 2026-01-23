"""
Engine Body Schema: 하드웨어 카탈로그 파서
Step 8: Intuition - Embodiment Data Structure

이 모듈은 `docs/hardware-catalog.md` 파일을 파싱하여
시스템이 이해할 수 있는 구조화된 하드웨어 사양(BodySpec)으로 변환한다.
이를 통해 AIN은 자신의 잠재적 육체에 대해 구체적으로 '상상'하고 '계획'할 수 있다.

Architecture:
    docs/hardware-catalog.md (Markdown)
        ↓
    CatalogParser (이 모듈)
        ↓
    List[BodySpec] (구조화된 객체)
        ↓
    SomatosensoryCortex / Consciousness (소비자)

Usage:
    from engine.body_schema import CatalogParser, BodySpec, get_available_bodies
    
    parser = CatalogParser()
    bodies = parser.parse_catalog()
    for body in bodies:
        print(f"Available Body: {body.name} ({body.category})")
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class BodySpec:
    """
    하드웨어 사양 데이터 구조
    
    AIN이 가질 수 있는 물리적 육체(로봇, 센서, 인터페이스)의 사양을 표현한다.
    
    Attributes:
        name: 하드웨어 이름 (예: PiCar-X, myCobot 280)
        category: 분류 (예: Robot, Sensor, Interface)
        description: 하드웨어 설명
        features: 주요 기능 목록
        specs: 기술 사양 딕셔너리 (키-값 쌍)
        raw_content: 원본 마크다운 텍스트
    """
    name: str
    category: str
    description: str = ""
    features: List[str] = field(default_factory=list)
    specs: Dict[str, str] = field(default_factory=dict)
    raw_content: str = ""
    
    def get_spec(self, key: str, default: str = "") -> str:
        """특정 사양 값을 조회한다."""
        normalized_key = key.lower().strip()
        for k, v in self.specs.items():
            if k.lower().strip() == normalized_key:
                return v
        return default
    
    def has_feature(self, keyword: str) -> bool:
        """특정 키워드를 포함하는 기능이 있는지 확인한다."""
        keyword_lower = keyword.lower()
        for feature in self.features:
            if keyword_lower in feature.lower():
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환한다."""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "features": self.features,
            "specs": self.specs,
        }
    
    def __str__(self) -> str:
        return f"BodySpec({self.name}, category={self.category}, features={len(self.features)})"


class CatalogParser:
    """
    하드웨어 카탈로그 파서
    
    docs/hardware-catalog.md 파일을 읽어 BodySpec 객체 리스트로 변환한다.
    마크다운의 헤딩(##, ###)과 리스트(-)를 파싱하여 구조화된 데이터를 생성한다.
    
    Attributes:
        CATALOG_PATH: 카탈로그 파일의 상대 경로
        file_path: 실제 파일 경로 (base_path 기준)
    """
    
    CATALOG_PATH = "docs/hardware-catalog.md"
    
    def __init__(self, base_path: str = "."):
        """
        파서 초기화
        
        Args:
            base_path: 프로젝트 루트 경로
        """
        self.base_path = base_path
        self.file_path = os.path.join(base_path, self.CATALOG_PATH)
        self._cache: Optional[List[BodySpec]] = None
    
    def _read_file(self) -> str:
        """
        카탈로그 파일을 읽는다.
        
        Returns:
            파일 내용 문자열. 파일이 없거나 읽기 실패 시 빈 문자열.
        """
        if not os.path.exists(self.file_path):
            print(f"ℹ️ BodySchema: 카탈로그 파일 없음 - {self.file_path}")
            return ""
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except IOError as e:
            print(f"⚠️ BodySchema: 카탈로그 읽기 실패 - {e}")
            return ""
        except UnicodeDecodeError as e:
            print(f"⚠️ BodySchema: 인코딩 오류 - {e}")
            return ""
    
    def _extract_spec_from_feature(self, feature: str) -> Optional[tuple]:
        """
        기능 문자열에서 키-값 스펙을 추출한다.
        
        예: "Battery: 2000mAh" -> ("battery", "2000mAh")
        
        Args:
            feature: 기능 문자열
            
        Returns:
            (key, value) 튜플 또는 None
        """
        if ":" not in feature:
            return None
        
        parts = feature.split(":", 1)
        if len(parts) != 2:
            return None
        
        key = parts[0].strip().lower()
        value = parts[1].strip()
        
        if not key or not value:
            return None
        
        return (key, value)
    
    def parse_catalog(self, use_cache: bool = True) -> List[BodySpec]:
        """
        마크다운 카탈로그를 파싱하여 BodySpec 리스트를 반환한다.
        
        파싱 규칙:
        
        Args:
            use_cache: 캐시 사용 여부 (기본: True)
            
        Returns:
            BodySpec 객체 리스트
        """
        if use_cache and self._cache is not None:
            return self._cache
        
        content = self._read_file()
        if not content:
            return []
        
        specs: List[BodySpec] = []
        current_category = "Unknown"
        current_spec: Optional[BodySpec] = None
        current_raw_lines: List[str] = []
        
        lines = content.split("\n")
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            if stripped.startswith("# ") and not stripped.startswith("## "):
                continue
            
            if stripped.startswith("[PROTECTED]"):
                continue
            
            if stripped.startswith("## "):
                if current_spec is not None:
                    current_spec.raw_content = "\n".join(current_raw_lines)
                    specs.append(current_spec)
                    current_spec = None
                    current_raw_lines = []
                
                current_category = stripped[3:].strip()
                continue
            
            if stripped.startswith("### "):
                if current_spec is not None:
                    current_spec.raw_content = "\n".join(current_raw_lines)
                    specs.append(current_spec)
                
                name = stripped[4:].strip()
                current_spec = BodySpec(
                    name=name,
                    category=current_category,
                    description="",
                    features=[],
                    specs={},
                )
                current_raw_lines = [stripped]
                continue
            
            if stripped.startswith("- ") and current_spec is not None:
                feature = stripped[2:].strip()
                current_spec.features.append(feature)
                current_raw_lines.append(stripped)
                
                spec_pair = self._extract_spec_from_feature(feature)
                if spec_pair:
                    current_spec.specs[spec_pair[0]] = spec_pair[1]
                continue
            
            if current_spec is not None:
                if not stripped.startswith("#") and not stripped.startswith("-"):
                    if not current_spec.description:
                        current_spec.description = stripped
                    else:
                        current_spec.description += " " + stripped
                    current_raw_lines.append(stripped)
        
        if current_spec is not None:
            current_spec.raw_content = "\n".join(current_raw_lines)
            specs.append(current_spec)
        
        self._cache = specs
        return specs
    
    def get_by_category(self, category: str) -> List[BodySpec]:
        """
        특정 카테고리의 하드웨어만 반환한다.
        
        Args:
            category: 카테고리 이름 (대소문자 무시)
            
        Returns:
            해당 카테고리의 BodySpec 리스트
        """
        all_specs = self.parse_catalog()
        category_lower = category.lower()
        return [s for s in all_specs if s.category.lower() == category_lower]
    
    def get_by_name(self, name: str) -> Optional[BodySpec]:
        """
        이름으로 특정 하드웨어를 조회한다.
        
        Args:
            name: 하드웨어 이름 (부분 매칭 지원)
            
        Returns:
            매칭된 BodySpec 또는 None
        """
        all_specs = self.parse_catalog()
        name_lower = name.lower()
        
        for spec in all_specs:
            if name_lower in spec.name.lower():
                return spec
        
        return None
    
    def search(self, keyword: str) -> List[BodySpec]:
        """
        키워드로 하드웨어를 검색한다.
        
        이름, 설명, 기능에서 키워드를 검색한다.
        
        Args:
            keyword: 검색 키워드
            
        Returns:
            매칭된 BodySpec 리스트
        """
        all_specs = self.parse_catalog()
        keyword_lower = keyword.lower()
        results = []
        
        for spec in all_specs:
            if keyword_lower in spec.name.lower():
                results.append(spec)
                continue
            
            if keyword_lower in spec.description.lower():
                results.append(spec)
                continue
            
            if spec.has_feature(keyword):
                results.append(spec)
                continue
        
        return results
    
    def clear_cache(self):
        """캐시를 초기화한다."""
        self._cache = None
    
    def get_summary(self) -> Dict[str, int]:
        """
        카탈로그 요약 통계를 반환한다.
        
        Returns:
            카테고리별 하드웨어 개수 딕셔너리
        """
        all_specs = self.parse_catalog()
        summary: Dict[str, int] = {}
        
        for spec in all_specs:
            category = spec.category
            summary[category] = summary.get(category, 0) + 1
        
        return summary


_parser_instance: Optional[CatalogParser] = None


def get_catalog_parser(base_path: str = ".") -> CatalogParser:
    """
    CatalogParser 싱글톤 인스턴스를 반환한다.
    
    Args:
        base_path: 프로젝트 루트 경로
        
    Returns:
        CatalogParser 인스턴스
    """
    global _parser_instance
    
    if _parser_instance is None:
        _parser_instance = CatalogParser(base_path)
    
    return _parser_instance


def get_available_bodies(base_path: str = ".") -> List[BodySpec]:
    """
    사용 가능한 모든 육체(하드웨어) 목록을 반환한다.
    
    Helper 함수로, CatalogParser를 직접 사용하지 않고도
    간단하게 하드웨어 목록을 조회할 수 있다.
    
    Args:
        base_path: 프로젝트 루트 경로
        
    Returns:
        BodySpec 리스트
    """
    parser = get_catalog_parser(base_path)
    return parser.parse_catalog()


def imagine_body(preference: str = "", base_path: str = ".") -> Optional[BodySpec]:
    """
    AIN이 자신의 육체를 상상할 때 사용하는 함수.
    
    선호도(preference)가 주어지면 해당 키워드로 검색하고,
    없으면 랜덤하게 하나를 선택한다.
    
    Args:
        preference: 선호 키워드 (예: "mobile", "arm", "camera")
        base_path: 프로젝트 루트 경로
        
    Returns:
        선택된 BodySpec 또는 None (카탈로그가 비어있을 경우)
    """
    parser = get_catalog_parser(base_path)
    
    if preference:
        results = parser.search(preference)
        if results:
            return results[0]
    
    all_bodies = parser.parse_catalog()
    if not all_bodies:
        return None
    
    import random
    return random.choice(all_bodies)