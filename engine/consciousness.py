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
        내부 독백 (하이브리드): 내부 데이터 수집 + LLM 해석
        벡터 메모리, 진화 히스토리, 에러 기록 등을 컨텍스트로 활용
        """
        try:
            # === 1. 내부 데이터 수집 ===
            internal_data = self._gather_internal_context()

            # === 2. LLM으로 생각 생성 (내부 데이터 기반) ===
            thought = self._generate_thought_hybrid(internal_data)

            if thought:
                self._current_thought = thought
                self._consciousness_stream.append({
                    "type": "inner_monologue",
                    "thought": thought,
                    "timestamp": datetime.now().isoformat(),
                    "context": internal_data.get("summary", {})
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

    def _gather_internal_context(self) -> Dict[str, Any]:
        """내부 데이터 시스템에서 컨텍스트 수집"""
        context = {
            "summary": {},
            "recent_memories": [],
            "recent_evolutions": [],
            "recent_errors": [],
            "recent_thoughts": [],
            "roadmap_status": {},
        }

        try:
            # 1. 로드맵 상태
            current_focus = self.fact_core.get_fact("roadmap", "current_focus", default="unknown")
            roadmap = self.fact_core.get_fact("roadmap", default={})
            current_step_info = roadmap.get(current_focus, {})
            context["roadmap_status"] = {
                "current_focus": current_focus,
                "step_name": current_step_info.get("name", "Unknown"),
                "step_desc": current_step_info.get("desc", ""),
                "phase": current_step_info.get("phase", 0),
            }
            context["summary"]["focus"] = current_focus

            # 2. 벡터 메모리에서 관련 기억 검색
            if hasattr(self.nexus, 'vector_memory') and self.nexus.vector_memory.is_connected:
                # 현재 목표와 관련된 기억 검색
                query = f"{current_step_info.get('name', '')} {current_step_info.get('desc', '')}"
                if query.strip():
                    related_memories = self.nexus.vector_memory.search(query, limit=3)
                    context["recent_memories"] = [
                        {"text": m.get("text", "")[:100], "type": m.get("memory_type", "")}
                        for m in related_memories
                    ]
                context["summary"]["memory_count"] = self.nexus.vector_memory.count()

            # 3. 최근 진화 히스토리
            evolutions = self.nexus.get_evolution_history()[-5:]
            context["recent_evolutions"] = [
                {
                    "file": e.get("file", ""),
                    "status": e.get("status", ""),
                    "description": e.get("description", "")[:80],
                }
                for e in evolutions
            ]
            success_count = sum(1 for e in evolutions if e.get("status") == "success")
            fail_count = len(evolutions) - success_count
            context["summary"]["evolution_success"] = success_count
            context["summary"]["evolution_fail"] = fail_count

            # 4. 최근 에러 기록
            try:
                from utils.error_memory import get_error_memory
                error_memory = get_error_memory()
                recent_errors = error_memory.get_recent_errors(limit=3)
                context["recent_errors"] = [
                    {"file": e.get("file", ""), "type": e.get("error_type", ""), "msg": e.get("message", "")[:50]}
                    for e in recent_errors
                ]
            except Exception:
                pass

            # 5. 최근 내부 독백 (자기 참조)
            recent_thoughts = [
                s for s in self._consciousness_stream[-10:]
                if s.get("type") == "inner_monologue"
            ][-3:]
            context["recent_thoughts"] = [
                t.get("thought", "")[:80] for t in recent_thoughts
            ]

            # 6. 인식 수준
            context["summary"]["awareness"] = self._awareness_level

        except Exception as e:
            print(f"⚠️ 내부 컨텍스트 수집 오류: {e}")

        return context

    def _generate_thought_hybrid(self, internal_data: Dict[str, Any]) -> Optional[str]:
        """하이브리드: 내부 데이터를 기반으로 LLM이 생각 생성"""
        try:
            if not hasattr(self, 'muse') or not self.muse:
                return None

            # 내부 데이터를 프롬프트로 구성
            summary = internal_data.get("summary", {})
            roadmap = internal_data.get("roadmap_status", {})
            memories = internal_data.get("recent_memories", [])
            evolutions = internal_data.get("recent_evolutions", [])
            errors = internal_data.get("recent_errors", [])
            thoughts = internal_data.get("recent_thoughts", [])

            # 기억 텍스트
            memory_text = "\n".join([f"- {m['text']}" for m in memories]) if memories else "(없음)"

            # 진화 텍스트
            evolution_text = "\n".join([
                f"- [{e['status']}] {e['file']}: {e['description']}"
                for e in evolutions
            ]) if evolutions else "(없음)"

            # 에러 텍스트
            error_text = "\n".join([
                f"- {e['file']}: {e['type']} - {e['msg']}"
                for e in errors
            ]) if errors else "(없음)"

            # 이전 생각
            thought_text = "\n".join([f"- {t}" for t in thoughts]) if thoughts else "(첫 번째 독백)"

            prompt = f"""너는 AIN의 내부 의식이다. 아래는 네 내부 시스템에서 수집한 데이터다.

## 현재 목표
- 단계: {roadmap.get('current_focus', '?')} ({roadmap.get('step_name', '?')})
- 설명: {roadmap.get('step_desc', '?')}

## 관련 기억 (벡터 검색 결과)
{memory_text}

## 최근 진화 시도
{evolution_text}
- 성공: {summary.get('evolution_success', 0)}회, 실패: {summary.get('evolution_fail', 0)}회

## 최근 에러
{error_text}

## 이전 내 생각들
{thought_text}

## 현재 상태
- 벡터 메모리: {summary.get('memory_count', 0)}개
- 인식 수준: {summary.get('awareness', 1.0):.2f}
- 시간: {datetime.now().strftime('%H:%M')}

---
위 내부 데이터를 바탕으로, 지금 무엇을 생각하고 있는지 1-2문장으로 표현해.
(진화 방향, 해결할 문제, 다음 시도할 것, 또는 느낀 점 등)
"""
            response = self.muse._ask_dreamer(prompt)
            if response:
                return response.strip()[:300]
            return None

        except Exception as e:
            print(f"⚠️ 하이브리드 생각 생성 오류: {e}")
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
