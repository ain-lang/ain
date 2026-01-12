"""
🧠 AIN Error Memory - 실패 기억 시스템

Coder가 반복하는 실수를 기록하고, 다음 시도 시 프롬프트에 주입하여
같은 실수를 반복하지 않도록 합니다.

사용법:
    from utils.error_memory import ErrorMemory
    em = ErrorMemory()
    em.record_error("engine/handlers.py", "unterminated string literal", "line 177")
    hints = em.get_hints_for_file("engine/handlers.py")
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


class ErrorMemory:
    """
    실패 기억 저장소
    
    - 파일별 오류 기록 저장
    - 자주 발생하는 오류 패턴 추적
    - Coder 프롬프트용 힌트 생성
    """
    
    MEMORY_FILE = "error_memory.json"
    MAX_ERRORS_PER_FILE = 5  # 파일당 최대 기록 수
    MAX_TOTAL_ERRORS = 50    # 전체 최대 기록 수
    
    def __init__(self):
        self.errors: Dict[str, List[Dict]] = defaultdict(list)
        self.patterns: Dict[str, int] = defaultdict(int)  # 오류 패턴 빈도
        self._load()
    
    def _load(self):
        """저장된 오류 기록 로드"""
        if os.path.exists(self.MEMORY_FILE):
            try:
                with open(self.MEMORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.errors = defaultdict(list, data.get("errors", {}))
                    self.patterns = defaultdict(int, data.get("patterns", {}))
            except Exception as e:
                print(f"⚠️ ErrorMemory 로드 실패: {e}")
    
    def _save(self):
        """오류 기록 저장"""
        try:
            with open(self.MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "errors": dict(self.errors),
                    "patterns": dict(self.patterns),
                    "updated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ ErrorMemory 저장 실패: {e}")
    
    def record_error(self, filename: str, error_type: str, details: str = ""):
        """
        오류 기록
        
        Args:
            filename: 오류가 발생한 파일
            error_type: 오류 유형 (예: "unterminated string literal")
            details: 추가 세부사항 (예: "line 177")
        """
        error_record = {
            "type": error_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # 파일별 오류 기록
        self.errors[filename].append(error_record)
        
        # 최대 개수 유지
        if len(self.errors[filename]) > self.MAX_ERRORS_PER_FILE:
            self.errors[filename] = self.errors[filename][-self.MAX_ERRORS_PER_FILE:]
        
        # 오류 패턴 빈도 증가
        pattern_key = f"{error_type}"
        self.patterns[pattern_key] += 1
        
        self._save()
        print(f"🧠 [ErrorMemory] 기록됨: {filename} - {error_type}")
    
    def get_hints_for_file(self, filename: str) -> str:
        """
        특정 파일에 대한 오류 힌트 생성
        
        Args:
            filename: 대상 파일명
        
        Returns:
            Coder 프롬프트에 주입할 힌트 문자열
        """
        hints = []
        
        # 해당 파일의 최근 오류
        file_errors = self.errors.get(filename, [])
        if file_errors:
            hints.append(f"🚨 [{filename}] 이전 오류 기록:")
            for err in file_errors[-3:]:  # 최근 3개
                hints.append(f"  - {err['type']}: {err['details']}")
        
        return "\n".join(hints) if hints else ""
    
    def get_common_errors(self, limit: int = 5) -> str:
        """
        자주 발생하는 오류 패턴 반환
        
        Args:
            limit: 반환할 최대 패턴 수
        
        Returns:
            자주 발생하는 오류 목록 문자열
        """
        if not self.patterns:
            return ""
        
        # 빈도순 정렬
        sorted_patterns = sorted(
            self.patterns.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        lines = ["⚠️ 자주 발생하는 오류 패턴 (반드시 피하라):"]
        for pattern, count in sorted_patterns:
            lines.append(f"  - {pattern} ({count}회)")
        
        return "\n".join(lines)
    
    def get_all_hints(self, target_files: List[str] = None) -> str:
        """
        Coder 프롬프트용 종합 힌트 생성
        
        Args:
            target_files: 수정 대상 파일 목록 (선택)
        
        Returns:
            종합 힌트 문자열
        """
        hints = []
        
        # 공통 오류 패턴
        common = self.get_common_errors(3)
        if common:
            hints.append(common)
        
        # 대상 파일별 오류 기록
        if target_files:
            for f in target_files:
                file_hint = self.get_hints_for_file(f)
                if file_hint:
                    hints.append(file_hint)
        
        return "\n\n".join(hints) if hints else ""
    
    def clear_file(self, filename: str):
        """특정 파일의 오류 기록 삭제 (성공 시 호출)"""
        if filename in self.errors:
            del self.errors[filename]
            self._save()


# 싱글톤 인스턴스
_error_memory = None

def get_error_memory() -> ErrorMemory:
    """ErrorMemory 싱글톤 반환"""
    global _error_memory
    if _error_memory is None:
        _error_memory = ErrorMemory()
    return _error_memory
