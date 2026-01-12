"""
Facts Snapshot: 시스템 스냅샷 생성
"""
import os
import json


# 🔒 보호된 파일 목록
PROTECTED_FILES = frozenset([
    "main.py",
    "api/keys.py",
    "api/github.py",
    ".ainprotect",
    "docs/hardware-catalog.md",
])


def is_protected(file_path: str) -> bool:
    """파일이 보호 목록에 있는지 확인"""
    normalized = file_path.lstrip('./').replace('\\', '/')
    
    if normalized in PROTECTED_FILES:
        return True
    
    filename = os.path.basename(file_path)
    if filename in ["main.py", ".ainprotect"]:
        return True
    
    if "api/" in normalized and filename in ["keys.py", "github.py"]:
        return True
    
    return False


class SnapshotMixin:
    """스냅샷 생성 믹스인"""
    
    def get_system_snapshot(self):
        """시스템 스냅샷 생성 - AI가 코드를 분석할 때 사용"""
        snapshot = "=== AIN SYSTEM SNAPSHOT ===\n"
        snapshot += f"Roadmap Progress: {self.facts['roadmap']['current_focus']}\n"
        snapshot += f"Architecture Guide: {json.dumps(self.facts['architecture_guide'], indent=2, ensure_ascii=False)}\n"
        snapshot += f"Lessons Learned (Self-Correction): {json.dumps(self.facts.get('lessons_learned', []), indent=2, ensure_ascii=False)}\n"
        
        included_extensions = ('.py', '.md', '.txt', '.json', '.mojo')
        
        for root, dirs, files in os.walk("."):
            if any(x in root for x in ["backups", ".git", "__pycache__", ".ain_cache"]):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if is_protected(file_path):
                    snapshot += f"\n--- FILE: {file_path} (🔒 PROTECTED) ---\n"
                    snapshot += "# [PROTECTED] This file is managed by human master only.\n"
                    snapshot += "# AIN cannot and should not modify this file.\n"
                    continue

                if file.endswith(included_extensions):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if len(content) > 15000:
                                content = content[:15000] + "\n... (truncated)"
                            snapshot += f"\n--- FILE: {file_path} ---\n{content}\n"
                    except: 
                        pass
        
        return snapshot
