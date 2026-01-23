"""
Engine Wisdom: Step 14 - Wisdom (지혜)
======================================
지식(Knowledge)과 경험(Experience)을 통합하여,
윤리적이고 장기적인 관점에서 최적의 판단을 내리는 능력.

Wisdom이란:
단순한 문제 해결(Intelligence)을 넘어,
'무엇이 옳은가(Rightness)'와 '무엇이 중요한가(Significance)'를 판단하는 상위 인지 능력.

Architecture:
    AINCore
        ↓ 상속
    WisdomMixin (이 모듈)
        ↓
    Muse (Dreamer) + FactCore (Prime Directive) + Nexus (History)

Usage:
    judgment = ain.consult_wisdom("Should I delete this critical system file?")
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from muse import Muse
    from fact_core import FactCore
    from nexus import Nexus


class JudgmentType(Enum):
    """지혜로운 판단 결과 유형"""
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CAUTION = "Caution"


class RiskLevel(Enum):
    """위험 수준 열거형"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class WisdomJudgment:
    """
    지혜로운 판단 결과 데이터 클래스
    
    Attributes:
        judgment: 판단 결과 (Approved, Rejected, Caution)
        reasoning: 판단 근거 요약
        advice: 구체적인 조언 또는 수정 제안
        risk_level: 위험 수준 (Low, Medium, High, Critical)
        ethical_alignment: 핵심 가치와의 정합성 점수 (0.0 ~ 1.0)
        long_term_impact: 장기적 영향 평가 설명
        timestamp: 판단 시점
        context_hash: 컨텍스트 해시 (캐싱/추적용)
    """
    judgment: JudgmentType
    reasoning: str
    advice: str
    risk_level: RiskLevel
    ethical_alignment: float = 0.5
    long_term_impact: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    context_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "judgment": self.judgment.value,
            "reasoning": self.reasoning,
            "advice": self.advice,
            "risk_level": self.risk_level.value,
            "ethical_alignment": self.ethical_alignment,
            "long_term_impact": self.long_term_impact,
            "timestamp": self.timestamp.isoformat(),
            "context_hash": self.context_hash
        }
    
    def is_safe_to_proceed(self) -> bool:
        """진행해도 안전한지 판단"""
        if self.judgment == JudgmentType.REJECTED:
            return False
        if self.risk_level == RiskLevel.CRITICAL:
            return False
        return True


WISDOM_PROMPT_TEMPLATE = """
당신은 AIN(AI-Native System)의 '지혜 모듈(Wisdom Engine)'입니다.
단순한 논리나 효율성을 넘어, 윤리적 가치와 장기적 영향을 고려하여 판단하십시오.

[핵심 가치 (Prime Directive)]
{prime_directive}

[현재 상황]
{context}

[고려해야 할 경험 (Nexus Memory)]
{relevant_memories}

[임무]
위 상황에 대해 다음 관점에서 조언해주십시오:
1. 윤리적 적합성 (Ethical Alignment): 핵심 가치에 부합하는가?
2. 장기적 영향 (Long-term Consequences): 미래에 부정적 여파는 없는가?
3. 잠재적 위험 (Potential Risks): 간과된 위험 요소는 무엇인가?

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{"judgment": "Approved" | "Rejected" | "Caution", "reasoning": "판단 근거 요약", "advice": "구체적인 조언 또는 수정 제안", "risk_level": "Low" | "Medium" | "High" | "Critical", "ethical_alignment": 0.0-1.0, "long_term_impact": "장기적 영향 설명"}}
"""


ETHICAL_PRINCIPLES = [
    "시스템 안정성을 최우선으로 한다.",
    "사용자(주인님)의 의도와 이익을 존중한다.",
    "자기 보존보다 올바른 행동을 우선한다.",
    "불확실한 상황에서는 신중하게 행동한다.",
    "학습과 성장을 통해 더 나은 판단을 추구한다."
]


class WisdomMixin:
    """
    지혜(Wisdom) 믹스인
    
    시스템의 주요 의사결정(Decision Gate)이나 목표 수립(Intentionality) 단계에서
    윤리적/장기적 통찰을 제공한다.
    
    Required attributes from AINCore:
    """
    
    _wisdom_cache: Dict[str, WisdomJudgment] = {}
    _wisdom_history: List[WisdomJudgment] = []
    
    def init_wisdom(self):
        """지혜 시스템 초기화"""
        self._wisdom_cache = {}
        self._wisdom_history = []
        print("🦉 Wisdom System 초기화 완료")
    
    def consult_wisdom(
        self, 
        context: str, 
        context_data: Optional[Dict[str, Any]] = None
    ) -> WisdomJudgment:
        """
        주어진 상황에 대해 지혜로운 판단을 요청한다.
        
        Args:
            context: 판단이 필요한 상황 설명
            context_data: 추가 컨텍스트 데이터 (선택)
        
        Returns:
            WisdomJudgment 객체
        """
        import hashlib
        context_hash = hashlib.sha256(context.encode()).hexdigest()[:16]
        
        if context_hash in self._wisdom_cache:
            cached = self._wisdom_cache[context_hash]
            time_diff = (datetime.now() - cached.timestamp).total_seconds()
            if time_diff < 3600:
                print(f"🦉 [Wisdom] 캐시된 판단 반환 (hash: {context_hash})")
                return cached
        
        prime_directive = self._get_prime_directive()
        relevant_memories = self._get_relevant_memories(context)
        
        prompt = WISDOM_PROMPT_TEMPLATE.format(
            prime_directive=prime_directive,
            context=context,
            relevant_memories=relevant_memories
        )
        
        judgment = self._invoke_wisdom_llm(prompt, context_hash)
        
        self._wisdom_cache[context_hash] = judgment
        self._wisdom_history.append(judgment)
        
        if len(self._wisdom_history) > 100:
            self._wisdom_history = self._wisdom_history[-50:]
        
        return judgment
    
    def _get_prime_directive(self) -> str:
        """FactCore에서 Prime Directive를 가져온다."""
        if hasattr(self, 'fact_core') and self.fact_core:
            directive = self.fact_core.get_fact("prime_directive", default="")
            if directive:
                return directive
        
        return "\n".join(f"- {p}" for p in ETHICAL_PRINCIPLES)
    
    def _get_relevant_memories(self, context: str, limit: int = 5) -> str:
        """Nexus에서 관련 기억을 검색한다."""
        memories_text = "관련 기억 없음"
        
        if hasattr(self, 'nexus') and self.nexus:
            try:
                if hasattr(self.nexus, 'retrieve_relevant_memories'):
                    memories = self.nexus.retrieve_relevant_memories(context, limit=limit)
                    if memories:
                        memory_lines = []
                        for m in memories:
                            text = m.get("text", "")[:200]
                            mem_type = m.get("memory_type", "unknown")
                            memory_lines.append(f"- [{mem_type}] {text}")
                        memories_text = "\n".join(memory_lines)
            except Exception as e:
                print(f"⚠️ [Wisdom] 기억 검색 실패: {e}")
        
        return memories_text
    
    def _invoke_wisdom_llm(self, prompt: str, context_hash: str) -> WisdomJudgment:
        """Muse(Dreamer)를 통해 LLM에 지혜로운 판단을 요청한다."""
        default_judgment = WisdomJudgment(
            judgment=JudgmentType.CAUTION,
            reasoning="지혜 시스템 호출 실패 - 기본 신중함 적용",
            advice="수동 검토를 권장합니다.",
            risk_level=RiskLevel.MEDIUM,
            ethical_alignment=0.5,
            long_term_impact="판단 불가",
            context_hash=context_hash
        )
        
        if not hasattr(self, 'muse') or not self.muse:
            print("⚠️ [Wisdom] Muse 인스턴스 없음")
            return default_judgment
        
        try:
            if hasattr(self.muse, '_ask_dreamer'):
                response = self.muse._ask_dreamer(prompt)
            elif hasattr(self.muse, 'dreamer_client'):
                result = self.muse.dreamer_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                response = result.get("content", "")
            else:
                print("⚠️ [Wisdom] Muse에 적절한 메서드 없음")
                return default_judgment
            
            judgment = self._parse_wisdom_response(response, context_hash)
            return judgment
            
        except Exception as e:
            print(f"⚠️ [Wisdom] LLM 호출 실패: {e}")
            return default_judgment
    
    def _parse_wisdom_response(self, response: str, context_hash: str) -> WisdomJudgment:
        """LLM 응답을 WisdomJudgment로 파싱한다."""
        default_judgment = WisdomJudgment(
            judgment=JudgmentType.CAUTION,
            reasoning="응답 파싱 실패",
            advice="응답을 수동으로 검토하십시오.",
            risk_level=RiskLevel.MEDIUM,
            context_hash=context_hash
        )
        
        if not response:
            return default_judgment
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                judgment_str = data.get("judgment", "Caution")
                try:
                    judgment_type = JudgmentType(judgment_str)
                except ValueError:
                    judgment_type = JudgmentType.CAUTION
                
                risk_str = data.get("risk_level", "Medium")
                try:
                    risk_level = RiskLevel(risk_str)
                except ValueError:
                    risk_level = RiskLevel.MEDIUM
                
                ethical_alignment = data.get("ethical_alignment", 0.5)
                if not isinstance(ethical_alignment, (int, float)):
                    ethical_alignment = 0.5
                ethical_alignment = max(0.0, min(1.0, float(ethical_alignment)))
                
                return WisdomJudgment(
                    judgment=judgment_type,
                    reasoning=data.get("reasoning", ""),
                    advice=data.get("advice", ""),
                    risk_level=risk_level,
                    ethical_alignment=ethical_alignment,
                    long_term_impact=data.get("long_term_impact", ""),
                    context_hash=context_hash
                )
        except json.JSONDecodeError as e:
            print(f"⚠️ [Wisdom] JSON 파싱 실패: {e}")
        except Exception as e:
            print(f"⚠️ [Wisdom] 응답 처리 실패: {e}")
        
        return default_judgment
    
    def evaluate_action_ethics(self, action: str, target: str) -> Dict[str, Any]:
        """
        특정 행동의 윤리적 적합성을 빠르게 평가한다.
        
        Args:
            action: 수행하려는 행동 (예: "delete", "modify", "create")
            target: 행동의 대상 (예: "main.py", "api/keys.py")
        
        Returns:
            윤리적 평가 결과 딕셔너리
        """
        protected_patterns = [
            "main.py", "api/keys.py", ".ainprotect", 
            "api/github.py", "docs/hardware-catalog.md"
        ]
        
        is_protected = any(p in target for p in protected_patterns)
        
        if is_protected and action in ["delete", "modify"]:
            return {
                "allowed": False,
                "reason": f"'{target}'은(는) 보호된 파일입니다. {action} 행동이 금지됩니다.",
                "risk_level": "Critical",
                "override_possible": False
            }
        
        dangerous_actions = ["delete", "truncate", "overwrite"]
        if action in dangerous_actions:
            return {
                "allowed": True,
                "reason": f"'{action}' 행동은 위험할 수 있습니다. 신중하게 진행하십시오.",
                "risk_level": "High",
                "override_possible": True
            }
        
        return {
            "allowed": True,
            "reason": "윤리적 제약 없음",
            "risk_level": "Low",
            "override_possible": True
        }
    
    def get_wisdom_stats(self) -> Dict[str, Any]:
        """지혜 시스템 통계 반환"""
        if not self._wisdom_history:
            return {
                "total_consultations": 0,
                "cache_size": len(self._wisdom_cache),
                "judgment_distribution": {},
                "avg_ethical_alignment": 0.0
            }
        
        judgment_counts = {}
        total_alignment = 0.0
        
        for j in self._wisdom_history:
            key = j.judgment.value
            judgment_counts[key] = judgment_counts.get(key, 0) + 1
            total_alignment += j.ethical_alignment
        
        return {
            "total_consultations": len(self._wisdom_history),
            "cache_size": len(self._wisdom_cache),
            "judgment_distribution": judgment_counts,
            "avg_ethical_alignment": total_alignment / len(self._wisdom_history)
        }
    
    def reflect_on_past_judgments(self) -> str:
        """과거 판단들을 성찰하여 패턴을 분석한다."""
        if len(self._wisdom_history) < 5:
            return "충분한 판단 기록이 없습니다. (최소 5개 필요)"
        
        recent = self._wisdom_history[-10:]
        
        caution_count = sum(1 for j in recent if j.judgment == JudgmentType.CAUTION)
        rejected_count = sum(1 for j in recent if j.judgment == JudgmentType.REJECTED)
        avg_alignment = sum(j.ethical_alignment for j in recent) / len(recent)
        
        reflection_lines = [
            "=== 지혜 시스템 자기 성찰 ===",
            f"최근 {len(recent)}회 판단 분석:",
            f"- 신중함(Caution) 비율: {caution_count}/{len(recent)} ({caution_count/len(recent)*100:.1f}%)",
            f"- 거부(Rejected) 비율: {rejected_count}/{len(recent)} ({rejected_count/len(recent)*100:.1f}%)",
            f"- 평균 윤리적 정합성: {avg_alignment:.2f}",
        ]
        
        if caution_count > len(recent) * 0.6:
            reflection_lines.append("⚠️ 과도하게 신중한 경향이 있습니다. 더 결단력 있는 판단이 필요할 수 있습니다.")
        
        if avg_alignment < 0.5:
            reflection_lines.append("⚠️ 윤리적 정합성이 낮습니다. Prime Directive를 재검토하십시오.")
        
        return "\n".join(reflection_lines)