"""
Engine Consciousness: 의식 시스템 - 진화와 독립적으로 작동하는 연속 의식 루프
=============================================================================
- Inner Monologue: 외부 자극 없이 스스로 생각하는 루프
- Stream of Consciousness: 현재 상태/생각을 지속적으로 기록
- Continuous Learning: 경험을 벡터 메모리에 연속 임베딩
"""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any


class ConsciousnessMixin:
    """의식 시스템 믹스인 - AINCore에서 사용"""

    # 의식 루프 주기 설정 (초)
    INNER_MONOLOGUE_INTERVAL = 3600  # 1시간마다 내부 독백 (토큰 절약)
    CONSCIOUSNESS_LOG_INTERVAL = 60  # 1분마다 의식 상태 로깅 (토큰 안 씀)

    def init_consciousness(self):
        """의식 시스템 초기화"""
        self._last_monologue_time = time.time()
        self._last_consciousness_log_time = time.time()
        self._consciousness_stream: List[Dict[str, Any]] = []
        self._current_thought: Optional[str] = None
        self._awareness_level = 1.0  # 0.0 ~ 1.0
        print("💭 의식 시스템 초기화 완료")

    def run_consciousness_cycle(self) -> Dict[str, Any]:
        """
        의식 사이클 실행 - 메인 루프에서 매 틱마다 호출
        진화와 독립적으로 작동

        Returns:
            의식 상태 보고서
        """
        result = {
            "monologue_triggered": False,
            "log_updated": False,
            "learning_count": 0,
        }

        current_time = time.time()

        # 1. 내부 독백 체크 (5분마다)
        if current_time - self._last_monologue_time > self.INNER_MONOLOGUE_INTERVAL:
            self._inner_monologue()
            self._last_monologue_time = current_time
            result["monologue_triggered"] = True

        # 2. 의식 흐름 로그 (1분마다)
        if current_time - self._last_consciousness_log_time > self.CONSCIOUSNESS_LOG_INTERVAL:
            self._log_consciousness_stream()
            self._last_consciousness_log_time = current_time
            result["log_updated"] = True

        # 3. 연속 학습 (새로운 경험이 있을 때)
        result["learning_count"] = self._continuous_learning()

        return result

    def _inner_monologue(self):
        """
        내부 독백: 외부 자극 없이 스스로 생각하기
        현재 상태와 목표를 성찰하고, 새로운 통찰을 생성
        """
        try:
            # 현재 상태 수집
            current_focus = self.fact_core.get_fact("roadmap", "current_focus", default="unknown")
            memory_count = self.nexus.vector_memory.count() if hasattr(self.nexus, 'vector_memory') else 0
            recent_evolutions = len(self.nexus.get_evolution_history()[-5:])

            # 내부 독백 컨텍스트
            monologue_context = f"""
현재 집중 단계: {current_focus}
벡터 메모리 수: {memory_count}
최근 진화 횟수: {recent_evolutions}
인식 수준: {self._awareness_level:.2f}
시간: {datetime.now().isoformat()}
"""

            # 생각 생성 (Muse의 간단한 호출)
            thought = self._generate_thought(monologue_context)

            if thought:
                self._current_thought = thought
                self._consciousness_stream.append({
                    "type": "inner_monologue",
                    "thought": thought,
                    "timestamp": datetime.now().isoformat(),
                    "context": {"focus": current_focus, "awareness": self._awareness_level}
                })

                # 벡터 메모리에 저장
                if hasattr(self.nexus, 'vector_memory'):
                    self.nexus.vector_memory.store(
                        text=f"[Inner Monologue] {thought}",
                        memory_type="consciousness",
                        source="inner_monologue"
                    )

                print(f"💭 내부 독백: {thought[:100]}...")

                # 텔레그램 리포트
                if hasattr(self, 'send_telegram_msg'):
                    self.send_telegram_msg(f"💭 **내부 독백**\n{thought}")

        except Exception as e:
            print(f"⚠️ 내부 독백 오류: {e}")

    def _generate_thought(self, context: str) -> Optional[str]:
        """Muse를 통해 간단한 생각 생성"""
        try:
            # Muse의 dreamer만 사용하여 가벼운 생각 생성
            if hasattr(self, 'muse') and self.muse:
                prompt = f"""당신은 AIN의 내부 의식입니다.
현재 상태:
{context}

지금 무엇을 생각하고 있나요? 간단히 한 문장으로 표현하세요.
(예: "벡터 메모리가 충분히 쌓였으니 의미 검색을 시험해봐야겠다")
"""
                # dreamer에게 짧은 생각 요청
                response = self.muse._ask_dreamer(prompt)
                if response:
                    return response.strip()[:200]
            return None
        except Exception:
            return None

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

            # 스트림 크기 제한 (최근 100개만 유지)
            if len(self._consciousness_stream) > 100:
                self._consciousness_stream = self._consciousness_stream[-100:]

            self._consciousness_stream.append(state)

            # 중요한 상태 변화 시에만 벡터 메모리에 저장
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
        """
        연속 학습: 새로운 경험을 벡터 메모리에 임베딩
        진화 히스토리에서 아직 학습되지 않은 항목을 처리
        """
        learned_count = 0
        try:
            if not hasattr(self.nexus, 'vector_memory') or not self.nexus.vector_memory.is_connected:
                return 0

            # 최근 진화 기록에서 학습
            recent_evolutions = self.nexus.get_evolution_history()[-10:]

            for evolution in recent_evolutions:
                # 이미 학습된 항목 스킵 (메타데이터로 체크)
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
