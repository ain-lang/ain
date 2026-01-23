"""
Engine Consolidation: 기억 응고화 (Memory Consolidation)
========================================================
단기 기억(Recent History)을 분석하여 장기 기억(Semantic Insight)으로 변환.
로드맵 Step 5의 핵심 기능 - 뇌과학의 '해마(Hippocampus)' 역할 수행.

Usage:
    from engine.consolidation import get_consolidator
    consolidator = get_consolidator(nexus, muse)
    result = await consolidator.consolidate_cycle()
"""

import json
from typing import Dict, Any, Optional, TYPE_CHECKING

from engine.prompts import CONSOLIDATION_PROMPT

# 순환 임포트 방지
if TYPE_CHECKING:
    from nexus import Nexus
    from muse import Muse


class MemoryConsolidator:
    """
    기억 응고화 관리자
    
    주기적으로 최근 활동을 회고하고, 통찰(Insight)을 추출하여
    Vector DB(LanceDB)에 장기 기억으로 저장한다.
    
    Attributes:
        nexus: Nexus 인스턴스 (기억 저장소)
        muse: Muse 인스턴스 (LLM 추론)
        lance: LanceBridge 인스턴스 (벡터 DB)
    """

    VECTOR_DIM = 384  # MiniLM 임베딩 차원

    def __init__(self, nexus: "Nexus", muse: "Muse"):
        self.nexus = nexus
        self.muse = muse
        self._lance = None
        self._is_consolidating = False
        self._init_lance()

    def _init_lance(self):
        """LanceBridge 초기화 (Graceful Degradation)"""
        try:
            from database.lance_bridge import get_lance_bridge
            self._lance = get_lance_bridge()
        except ImportError:
            print("⚠️ Consolidator: LanceBridge 미사용")
            self._lance = None

    async def consolidate_cycle(self, recent_count: int = 10) -> Dict[str, Any]:
        """
        응고화 사이클 실행
        
        Args:
            recent_count: 분석할 최근 기록 수
            
        Returns:
            {"status": str, "insight": str, "saved": bool}
        """
        if self._is_consolidating:
            return {"status": "skipped", "reason": "already_running"}
        
        self._is_consolidating = True
        print("🧠 Memory Consolidation: 기억 응고화 시작...")

        try:
            # 1. 최근 기록 가져오기
            history_items = self._get_recent_history(recent_count)
            if not history_items:
                return {"status": "skipped", "reason": "no_recent_memories"}

            # 2. LLM 통찰 추출
            insight_data = self._extract_insight(history_items)

            # 3. 장기 기억으로 저장
            saved = self._save_insight(insight_data, len(history_items))

            result = {
                "status": "success",
                "insight": insight_data.get("insight", ""),
                "saved": saved
            }
            print(f"✨ Consolidation Complete: {result['insight'][:50]}...")
            return result

        except Exception as e:
            print(f"❌ Consolidation Failed: {e}")
            return {"status": "error", "error": str(e)}
        
        finally:
            self._is_consolidating = False

    def _get_recent_history(self, limit: int) -> list:
        """최근 기록 조회 (LanceDB 또는 Nexus 캐시)"""
        # LanceDB 우선 시도
        if self._lance and self._lance.is_connected:
            return self._lance.get_recent_memories(limit=limit)
        
        # Fallback: Nexus 캐시
        if hasattr(self.nexus, '_evolution_cache'):
            cache = self.nexus._evolution_cache[-limit:]
            return [
                {"text": r.get("description", ""), 
                 "timestamp": r.get("timestamp", ""),
                 "source": r.get("file", "unknown")}
                for r in cache
            ]
        return []

    def _extract_insight(self, history_items: list) -> Dict[str, Any]:
        """LLM을 통한 통찰 추출"""
        # 텍스트 변환
        history_text = "\n".join(
            f"- [{item.get('timestamp', 'N/A')}] {item.get('text', '')} "
            f"(Source: {item.get('source', 'unknown')})"
            for item in history_items
        )

        # 프롬프트 구성
        current_step = "Step 5: Memory Consolidation"
        prompt = CONSOLIDATION_PROMPT.format(
            history_text=history_text,
            current_step=current_step
        )

        # Muse Dreamer 호출
        response = self.muse.dreamer_client.chat([
            {"role": "system", "content": "Analyze system logs."},
            {"role": "user", "content": prompt}
        ])

        content = response.get("content", "{}")
        return self._parse_insight_response(content)

    def _parse_insight_response(self, content: str) -> Dict[str, Any]:
        """JSON 응답 파싱 (실패 시 Fallback)"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "insight": content[:200] if content else "Parse failed",
                "strategy": "Retry with cleaner prompt",
                "tags": ["consolidation_error"]
            }

    def _save_insight(self, insight_data: Dict, source_count: int) -> bool:
        """통찰을 장기 기억으로 저장"""
        if not self._lance or not self._lance.is_connected:
            print("⚠️ LanceDB 미연결. 저장 스킵.")
            return False

        insight_text = f"[INSIGHT] {insight_data.get('insight', '')}"
        # TODO: Muse Embedding API 연동 시 실제 벡터 생성
        dummy_vector = [0.0] * self.VECTOR_DIM

        return self._lance.add_memory(
            text=insight_text,
            vector=dummy_vector,
            memory_type="semantic",
            source="consolidation_engine",
            metadata={
                "strategy": insight_data.get("strategy"),
                "tags": insight_data.get("tags"),
                "consolidated_count": source_count
            }
        )


def get_consolidator(nexus: "Nexus", muse: "Muse") -> MemoryConsolidator:
    """Consolidator 팩토리 함수"""
    return MemoryConsolidator(nexus, muse)