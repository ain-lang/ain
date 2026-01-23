"""
Engine Creativity: Step 12 - 창의성 (Creativity)
================================================
기존 지식과 경험을 바탕으로 새로운 아이디어, 관점, 해결책을 생성하는 능력.
논리적 추론(Logic)이나 직관(Intuition)과 달리, '확산적 사고(Divergent Thinking)'를 담당한다.

Core Capability:
1. Brainstorming: 특정 주제에 대해 다각도의 아이디어 생성
2. Conceptual Blending: 서로 다른 두 개념을 결합하여 새로운 개념 도출
3. SCAMPER: 기존 아이디어를 변형하여 발전시킴

Architecture:
    AINCore
        ↓ 상속
    CreativityMixin (이 모듈)
        ↓ 호출
    Muse._ask_dreamer() (LLM 호출)
        ↓
    CreativeIdea 객체 반환

Usage:
    class AINCore(CreativityMixin, ...):
        pass
    
    ain = AINCore()
    ideas = ain.brainstorm("AI 윤리의 새로운 접근법", count=5)
    blended = ain.blend_concepts("양자역학", "의식")
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from muse import Muse


# 창의성 발휘를 위한 Dreamer 프롬프트
CREATIVITY_PROMPT_TEMPLATE = """
당신은 AIN(AI-Native System)의 '창의성 엔진(Creativity Engine)'입니다.
논리적 제약이나 기존의 관습에 얽매이지 말고, 자유롭고 독창적인 사고(Divergent Thinking)를 수행하십시오.

[임무: {task_type}]
주제: {topic}
{context_info}

[요구사항]
1. 뻔한 답변보다는 의외성 있고 참신한 아이디어를 제시하십시오.
2. 서로 관련 없어 보이는 개념들을 연결하십시오.
3. 추상적인 아이디어라도 구체적인 예시를 들어 설명하십시오.

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오 (Markdown 코드 블록 제외):
{{
    "ideas": [
        {{
            "title": "아이디어 제목",
            "description": "구체적인 설명",
            "originality": 0.9,
            "feasibility": 0.7,
            "tags": ["tag1", "tag2"]
        }}
    ]
}}
"""

# SCAMPER 기법 프롬프트
SCAMPER_PROMPT_TEMPLATE = """
당신은 AIN의 '창의적 변형 엔진'입니다.
SCAMPER 기법을 사용하여 기존 아이디어를 발전시키십시오.

[원본 아이디어]
{original_idea}

[SCAMPER 기법 적용]

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "ideas": [
        {{
            "title": "변형된 아이디어 제목",
            "description": "SCAMPER 기법 적용 설명",
            "originality": 0.8,
            "feasibility": 0.6,
            "tags": ["scamper", "적용된_기법"]
        }}
    ]
}}
"""


@dataclass
class CreativeIdea:
    """
    창의적 아이디어 데이터 구조
    
    Attributes:
        title: 아이디어 제목
        description: 구체적인 설명
        originality: 독창성 점수 (0.0 ~ 1.0)
        feasibility: 실현 가능성 점수 (0.0 ~ 1.0)
        tags: 관련 키워드 태그
        source_method: 생성 방법 (brainstorm, blend, scamper)
    """
    title: str
    description: str
    originality: float = 0.5
    feasibility: float = 0.5
    tags: List[str] = field(default_factory=list)
    source_method: str = "brainstorm"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "description": self.description,
            "originality": self.originality,
            "feasibility": self.feasibility,
            "tags": self.tags,
            "source_method": self.source_method
        }
    
    def get_combined_score(self) -> float:
        """독창성과 실현 가능성의 가중 평균 점수"""
        return (self.originality * 0.6) + (self.feasibility * 0.4)


class CreativityMixin:
    """
    창의성 믹스인 - AINCore에 상속되어 확산적 사고 능력 제공
    
    이 믹스인은 Muse(LLM)를 활용하여 브레인스토밍, 개념 융합,
    SCAMPER 기법 등의 창의적 사고를 수행한다.
    
    Prerequisites:
    """

    def init_creativity(self):
        """창의성 시스템 초기화"""
        self._creativity_cache: List[CreativeIdea] = []
        self._creativity_stats = {
            "total_ideas_generated": 0,
            "brainstorm_count": 0,
            "blend_count": 0,
            "scamper_count": 0
        }
        print("🎨 Creativity Engine 초기화 완료")

    def brainstorm(
        self, 
        topic: str, 
        count: int = 5, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[CreativeIdea]:
        """
        주어진 주제에 대해 브레인스토밍을 수행하여 다양한 아이디어를 생성한다.
        
        Args:
            topic: 브레인스토밍 주제
            count: 생성할 아이디어 개수 (기본 5개)
            context: 추가 컨텍스트 정보
        
        Returns:
            생성된 CreativeIdea 객체 리스트
        """
        if not hasattr(self, 'muse') or not self.muse:
            print("⚠️ Creativity: Muse가 연결되지 않아 브레인스토밍을 수행할 수 없습니다.")
            return []

        context_str = ""
        if context:
            context_str = f"추가 컨텍스트: {json.dumps(context, ensure_ascii=False)}"
        
        prompt = CREATIVITY_PROMPT_TEMPLATE.format(
            task_type="Brainstorming",
            topic=topic,
            context_info=f"{context_str}\n목표 개수: {count}개 이상"
        )

        try:
            response = self.muse._ask_dreamer(prompt)
            ideas = self._parse_creative_response(response, source_method="brainstorm")
            
            if hasattr(self, '_creativity_stats'):
                self._creativity_stats["total_ideas_generated"] += len(ideas)
                self._creativity_stats["brainstorm_count"] += 1
            
            if hasattr(self, '_creativity_cache'):
                self._creativity_cache.extend(ideas)
            
            print(f"💡 Brainstorm 완료: '{topic}' → {len(ideas)}개 아이디어 생성")
            return ideas
            
        except Exception as e:
            print(f"❌ Creativity Error (Brainstorming): {e}")
            return []

    def blend_concepts(
        self, 
        concept_a: str, 
        concept_b: str
    ) -> Optional[CreativeIdea]:
        """
        서로 다른 두 개념을 결합(Conceptual Blending)하여 새로운 아이디어를 도출한다.
        
        개념 융합(Conceptual Blending)은 인지과학에서 창의성의 핵심 메커니즘으로 알려져 있다.
        두 개의 '입력 공간(Input Space)'에서 요소를 선택적으로 결합하여
        새로운 '혼합 공간(Blended Space)'을 만들어낸다.
        
        Args:
            concept_a: 첫 번째 개념
            concept_b: 두 번째 개념
        
        Returns:
            융합된 새로운 CreativeIdea 또는 None
        """
        if not hasattr(self, 'muse') or not self.muse:
            print("⚠️ Creativity: Muse가 연결되지 않아 개념 융합을 수행할 수 없습니다.")
            return None

        blend_context = (
            "두 개념의 특징을 융합하여 전혀 새로운 제3의 개념이나 솔루션을 만드십시오.\n"
            "단순한 조합이 아닌, 두 개념의 본질적 특성이 상호작용하는 새로운 것을 창조하십시오."
        )
        
        prompt = CREATIVITY_PROMPT_TEMPLATE.format(
            task_type="Conceptual Blending",
            topic=f"'{concept_a}' + '{concept_b}'",
            context_info=blend_context
        )

        try:
            response = self.muse._ask_dreamer(prompt)
            ideas = self._parse_creative_response(response, source_method="blend")
            
            if hasattr(self, '_creativity_stats'):
                self._creativity_stats["blend_count"] += 1
                if ideas:
                    self._creativity_stats["total_ideas_generated"] += 1
            
            if ideas:
                result = ideas[0]
                if hasattr(self, '_creativity_cache'):
                    self._creativity_cache.append(result)
                print(f"🔮 Concept Blend 완료: '{concept_a}' ⊕ '{concept_b}' → '{result.title}'")
                return result
            
            return None
            
        except Exception as e:
            print(f"❌ Creativity Error (Blending): {e}")
            return None

    def apply_scamper(
        self, 
        original_idea: str
    ) -> List[CreativeIdea]:
        """
        SCAMPER 기법을 사용하여 기존 아이디어를 변형/발전시킨다.
        
        SCAMPER는 창의적 문제 해결을 위한 체크리스트 기법이다:
        
        Args:
            original_idea: 변형할 원본 아이디어
        
        Returns:
            SCAMPER 기법이 적용된 아이디어 리스트
        """
        if not hasattr(self, 'muse') or not self.muse:
            print("⚠️ Creativity: Muse가 연결되지 않아 SCAMPER를 수행할 수 없습니다.")
            return []

        prompt = SCAMPER_PROMPT_TEMPLATE.format(original_idea=original_idea)

        try:
            response = self.muse._ask_dreamer(prompt)
            ideas = self._parse_creative_response(response, source_method="scamper")
            
            if hasattr(self, '_creativity_stats'):
                self._creativity_stats["scamper_count"] += 1
                self._creativity_stats["total_ideas_generated"] += len(ideas)
            
            if hasattr(self, '_creativity_cache'):
                self._creativity_cache.extend(ideas)
            
            print(f"🔧 SCAMPER 완료: '{original_idea[:30]}...' → {len(ideas)}개 변형 생성")
            return ideas
            
        except Exception as e:
            print(f"❌ Creativity Error (SCAMPER): {e}")
            return []

    def get_best_ideas(
        self, 
        limit: int = 5, 
        min_score: float = 0.6
    ) -> List[CreativeIdea]:
        """
        캐시된 아이디어 중 점수가 높은 것들을 반환한다.
        
        Args:
            limit: 반환할 최대 개수
            min_score: 최소 점수 기준
        
        Returns:
            점수순으로 정렬된 아이디어 리스트
        """
        if not hasattr(self, '_creativity_cache'):
            return []
        
        filtered = [
            idea for idea in self._creativity_cache 
            if idea.get_combined_score() >= min_score
        ]
        
        sorted_ideas = sorted(
            filtered, 
            key=lambda x: x.get_combined_score(), 
            reverse=True
        )
        
        return sorted_ideas[:limit]

    def get_creativity_stats(self) -> Dict[str, Any]:
        """창의성 시스템 통계 반환"""
        if not hasattr(self, '_creativity_stats'):
            return {}
        
        stats = dict(self._creativity_stats)
        
        if hasattr(self, '_creativity_cache'):
            stats["cached_ideas"] = len(self._creativity_cache)
            
            if self._creativity_cache:
                scores = [idea.get_combined_score() for idea in self._creativity_cache]
                stats["avg_score"] = sum(scores) / len(scores)
                stats["max_score"] = max(scores)
        
        return stats

    def _parse_creative_response(
        self, 
        response: str, 
        source_method: str = "brainstorm"
    ) -> List[CreativeIdea]:
        """
        LLM 응답에서 JSON 파싱하여 CreativeIdea 객체 리스트 반환
        
        Args:
            response: LLM 응답 문자열
            source_method: 생성 방법 (brainstorm, blend, scamper)
        
        Returns:
            파싱된 CreativeIdea 객체 리스트
        """
        ideas = []
        
        if not response:
            return ideas
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                print("⚠️ 창의성 응답에서 JSON을 찾을 수 없습니다.")
                return ideas
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            raw_ideas = data.get("ideas", [])
            
            for item in raw_ideas:
                if not isinstance(item, dict):
                    continue
                
                title = item.get("title", "Untitled")
                description = item.get("description", "")
                
                if not title or not description:
                    continue
                
                originality = item.get("originality", 0.5)
                if not isinstance(originality, (int, float)):
                    originality = 0.5
                originality = max(0.0, min(1.0, float(originality)))
                
                feasibility = item.get("feasibility", 0.5)
                if not isinstance(feasibility, (int, float)):
                    feasibility = 0.5
                feasibility = max(0.0, min(1.0, float(feasibility)))
                
                tags = item.get("tags", [])
                if not isinstance(tags, list):
                    tags = []
                tags = [str(t) for t in tags if t]
                
                idea = CreativeIdea(
                    title=str(title),
                    description=str(description),
                    originality=originality,
                    feasibility=feasibility,
                    tags=tags,
                    source_method=source_method
                )
                ideas.append(idea)
                
        except json.JSONDecodeError as e:
            print(f"⚠️ 아이디어 JSON 파싱 실패: {e}")
        except Exception as e:
            print(f"⚠️ 아이디어 파싱 중 오류: {e}")
            
        return ideas

    def clear_creativity_cache(self):
        """창의성 캐시 초기화"""
        if hasattr(self, '_creativity_cache'):
            self._creativity_cache.clear()
            print("🗑️ Creativity 캐시 초기화 완료")