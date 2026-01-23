"""
Muse 유틸리티 함수들
- 컨텍스트 압축
- 로드맵 단계 파악
- 최근 진화 기록 조회
- 파일 크기 정보 생성
"""

import os
import json
from typing import Optional, List


def compress_context(system_context: str) -> str:
    """[Cost Optimization] 전체 코드베이스에서 핵심 로직만 추출하여 전송량을 줄임"""
    compressed = ""
    sections = system_context.split("--- FILE: ")

    for section in sections:
        if not section.strip():
            continue
        lines = section.split(" ---")
        if len(lines) < 2:
            continue

        filename = lines[0].strip()
        content = lines[1].strip()

        # 핵심 로직 파일은 비중있게, 나머지는 요약
        if any(core in filename for core in ["fact_core.py", "corpus_callosum.py", "database/"]):
            limit = 10000
        elif any(core in filename for core in ["muse.py", "nexus.py", "overseer.py"]):
            limit = 4000
        else:
            limit = 1000

        compressed += f"\n--- FILE: {filename} ---\n{content[:limit]}\n"

    return compressed


def get_current_roadmap_step() -> str:
    """ROADMAP.md에서 현재 진행 중인 Step(🔥)을 동적으로 읽어옴"""
    try:
        with open("ROADMAP.md", "r", encoding="utf-8") as f:
            content = f.read()
        for line in content.split("\n"):
            if "🔥" in line:
                return line.strip()
        return "다음 진화 단계 탐색 중"
    except Exception:
        return "Step 5: Memory Consolidation"


def get_recent_evolutions(limit: int = 5) -> str:
    """최근 진화 기록에서 파일명과 설명을 추출"""
    try:
        with open("evolution_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)

        recent = history[-limit:] if len(history) >= limit else history
        result = []
        for h in reversed(recent):
            file = h.get("file", "unknown")
            desc = h.get("description", "")[:100]
            result.append(f"- {file}: {desc}...")
        return "\n".join(result) if result else "없음"
    except Exception:
        return "없음"


def get_file_sizes_info(directories: List[str] = None) -> str:
    """
    주요 디렉토리의 파일 크기 정보를 생성하여 Dreamer에게 전달.
    Dreamer의 파일 크기 hallucination 방지용.
    """
    if directories is None:
        directories = ["engine", "muse", "nexus", "utils", "intention", "api", "database"]

    lines = ["[📊 실제 파일 크기 정보 - 이 정보를 신뢰하라!]"]

    for dir_name in directories:
        if not os.path.isdir(dir_name):
            continue

        dir_files = []
        for f in os.listdir(dir_name):
            if f.endswith(".py") and not f.startswith("__"):
                filepath = os.path.join(dir_name, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        line_count = sum(1 for _ in file)
                    status = "⚠️대형" if line_count > 150 else "✅소형"
                    dir_files.append(f"  - {f}: {line_count}줄 {status}")
                except Exception:
                    pass

        if dir_files:
            lines.append(f"\n{dir_name}/:")
            lines.extend(sorted(dir_files))

    lines.append("\n⚠️ 위 정보가 실제 파일 크기다. 추측하지 마라!")
    return "\n".join(lines)
