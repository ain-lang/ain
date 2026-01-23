"""
Engine Consciousness: 의식 시스템 - 진화와 독립적으로 작동하는 연속 의식 루프
=============================================================================
- Inner Monologue: 외부 자극 없이 스스로 생각하는 루프
- Stream of Consciousness: 현재 상태/생각을 지속적으로 기록
- Continuous Learning: 경험을 벡터 메모리에 연속 임베딩
"""

import time
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any

from .consciousness_utils import gather_internal_context, generate_thought_hybrid


class ConsciousnessMixin:
    """의식 시스템 믹스인 - AINCore에서 사용"""

    INNER_MONOLOGUE_INTERVAL = 3600  # 1시간마다 내부 독백
    CONSCIOUSNESS_LOG_INTERVAL = 60  # 1분마다 의식 상태 로깅

    def init_consciousness(self):
        """의식 시스템 초기화"""
        self._last_monologue_time = time.time()
        self._last_consciousness_log_time = time.time()
        self._consciousness_stream: List[Dict[str, Any]] = []
        self._current_thought: Optional[str] = None
        self._awareness_level = 1.0
        print("💭 의식 시스템 초기화 완료")

    def run_consciousness_cycle(self) -> Dict[str, Any]:
        """의식 사이클 실행 - 메인 루프에서 매 틱마다 호출"""
        result = {
            "monologue_triggered": False,
            "log_updated": False,
            "learning_count": 0,
        }

        current_time = time.time()

        if current_time - self._last_monologue_time > self.INNER_MONOLOGUE_INTERVAL:
            self._inner_monologue()
            self._last_monologue_time = current_time
            result["monologue_triggered"] = True

        if current_time - self._last_consciousness_log_time > self.CONSCIOUSNESS_LOG_INTERVAL:
            self._log_consciousness_stream()
            self._last_consciousness_log_time = current_time
            result["log_updated"] = True

        result["learning_count"] = self._continuous_learning()
        return result

    def _inner_monologue(self):
        """내부 독백 (하이브리드): 내부 데이터 수집 + LLM 해석"""
        try:
            internal_data = gather_internal_context(self)
            thought = generate_thought_hybrid(self, internal_data)

            if thought:
                self._current_thought = thought
                self._consciousness_stream.append({
                    "type": "inner_monologue",
                    "thought": thought,
                    "timestamp": datetime.now().isoformat(),
                    "context": internal_data.get("summary", {})
                })

                if hasattr(self.nexus, 'vector_memory'):
                    self.nexus.vector_memory.store(
                        text=f"[Inner Monologue] {thought}",
                        memory_type="consciousness",
                        source="inner_monologue"
                    )

                print(f"💭 내부 독백: {thought[:100]}...")

                if hasattr(self, 'send_telegram_msg'):
                    self.send_telegram_msg(f"💭 **내부 독백**\n{thought}")

        except Exception as e:
            print(f"⚠️ 내부 독백 오류: {e}")

    def _log_consciousness_stream(self):
        """의식 흐름 로그: 현재 상태를 스트림에 기록"""
        try:
            state = {
                "type": "consciousness_state",
                "timestamp": datetime.now().isoformat(),
                "awareness_level": self._awareness_level,
                "current_thought": self._current_thought,
                "is_processing": getattr(self, 'is_processing', False),
                "memory_stream_length": len(self._consciousness_stream),
            }

            if len(self._consciousness_stream) > 100:
                self._consciousness_stream = self._consciousness_stream[-100:]

            self._consciousness_stream.append(state)

            if len(self._consciousness_stream) % 10 == 0:
                summary = f"의식 상태 #{len(self._consciousness_stream)}: awareness={self._awareness_level:.2f}"
                if hasattr(self.nexus, 'vector_memory'):
                    self.nexus.vector_memory.store(
                        text=summary,
                        memory_type="consciousness",
                        source="stream_log"
                    )

        except Exception as e:
            print(f"⚠️ 의식 로그 오류: {e}")

    def _continuous_learning(self) -> int:
        """연속 학습: 새로운 경험을 벡터 메모리에 임베딩"""
        learned_count = 0
        try:
            # 벡터 메모리 연결 상태 확인
            if not hasattr(self.nexus, 'vector_memory'):
                print("⚠️ 연속 학습 스킵: nexus.vector_memory 속성 없음")
                return 0
            if not self.nexus.vector_memory.is_connected:
                print("⚠️ 연속 학습 스킵: 벡터 메모리 미연결")
                return 0

            recent_evolutions = self.nexus.get_evolution_history()[-10:]

            for evolution in recent_evolutions:
                evolution_id = evolution.get('id', str(evolution.get('timestamp', '')))

                if not self._is_already_learned(evolution_id):
                    description = evolution.get('description', '')
                    if description:
                        success = self.nexus.vector_memory.store(
                            text=f"[Evolution] {description}",
                            memory_type="evolution",
                            source="continuous_learning",
                            metadata={"evolution_id": evolution_id}
                        )
                        if success:
                            learned_count += 1
                            self._mark_as_learned(evolution_id)

        except Exception as e:
            print(f"⚠️ 연속 학습 오류: {e}")
            print(f"   스택 트레이스:\n{traceback.format_exc()}")

        return learned_count

    def _is_already_learned(self, evolution_id: str) -> bool:
        """해당 진화가 이미 학습되었는지 확인"""
        if not hasattr(self, '_learned_evolutions'):
            self._learned_evolutions = set()
        return evolution_id in self._learned_evolutions

    def _mark_as_learned(self, evolution_id: str):
        """진화를 학습 완료로 마킹"""
        if not hasattr(self, '_learned_evolutions'):
            self._learned_evolutions = set()
        self._learned_evolutions.add(evolution_id)

    def get_consciousness_report(self) -> Dict[str, Any]:
        """의식 상태 보고서 반환"""
        return {
            "awareness_level": self._awareness_level,
            "current_thought": self._current_thought,
            "stream_length": len(self._consciousness_stream),
            "last_monologue": self._consciousness_stream[-1] if self._consciousness_stream else None,
            "learned_count": len(getattr(self, '_learned_evolutions', set())),
        }

    def adjust_awareness(self, delta: float):
        """인식 수준 조정 (0.0 ~ 1.0)"""
        self._awareness_level = max(0.0, min(1.0, self._awareness_level + delta))
