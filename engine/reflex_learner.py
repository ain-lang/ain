"""
Engine Reflex Learner: 반사 행동 학습기
Step 8: Intuition - System 2(Evolution)에서 System 1(Reflex)으로의 지식 이양

이 모듈은 시스템의 진화 기록(Evolution History)을 분석하여,
반복적으로 발생하는 성공적인 행동 패턴을 찾아내고
이를 자동화된 반사 행동(Reflex)으로 변환할 것을 제안한다.

Architecture:
    Nexus (History)
        ↓ 진화 기록 수집
    ReflexLearner (이 모듈)
        ↓ 패턴 군집화 및 Muse(LLM) 분석
    Reflex Candidate (제안)

Usage:
    from engine.reflex_learner import ReflexLearner
    
    learner = ReflexLearner(nexus, muse)
    candidates = await learner.propose_new_reflexes()
"""

import json
import re
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

# Type hints for external modules
try:
    from muse import Muse
    from nexus import Nexus
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    Muse = None
    Nexus = None


# Reflex 제안 생성을 위한 프롬프트
REFLEX_LEARNING_PROMPT = """
당신은 AIN의 '직관 학습 모듈'입니다.
다음은 시스템이 수행한 반복적인 진화 기록(System 2)들입니다.

[반복 패턴 그룹]
{pattern_group}

[임무]
이 반복적인 작업을 즉각적인 '반사 행동(Reflex)'으로 자동화할 수 있는지 판단하고,
가능하다면 정규표현식(Regex) 기반의 트리거와 행동 유형을 정의하십시오.

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "is_automatable": true,
    "trigger_regex": "에러나 상황을 감지할 정규표현식",
    "reflex_type": "quick_fix",
    "action_name": "제안할_반사행동_이름",
    "description": "이 반사 행동이 하는 일 요약"
}}

자동화가 불가능한 경우:
{{
    "is_automatable": false,
    "reason": "자동화 불가능한 이유"
}}
"""


@dataclass
class ReflexCandidate:
    """
    반사 행동 후보 데이터 클래스
    
    Attributes:
        action_name: 제안된 반사 행동 이름
        trigger_regex: 트리거 정규표현식
        reflex_type: 반사 행동 유형 (quick_fix, ignore, retry, escalate)
        description: 행동 설명
        confidence: 제안 신뢰도 (0.0 ~ 1.0)
        source_patterns: 이 제안의 근거가 된 패턴들
        created_at: 생성 시각
    """
    action_name: str
    trigger_regex: str
    reflex_type: str
    description: str
    confidence: float = 0.0
    source_patterns: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "action_name": self.action_name,
            "trigger_regex": self.trigger_regex,
            "reflex_type": self.reflex_type,
            "description": self.description,
            "confidence": self.confidence,
            "source_patterns": self.source_patterns,
            "created_at": self.created_at
        }


class ReflexLearner:
    """
    반사 행동 학습기
    
    반복적인 성공 경험을 System 1(Reflex)으로 이관하여
    시스템의 인지 부하를 줄이고 반응 속도를 높인다.
    
    Attributes:
        nexus: Nexus 인스턴스 (기억 저장소)
        muse: Muse 인스턴스 (LLM 분석)
        min_occurrences: 패턴으로 인정하기 위한 최소 반복 횟수
    """

    def __init__(self, nexus: "Nexus", muse: "Muse"):
        self.nexus = nexus
        self.muse = muse
        self.min_occurrences = 3  # 최소 반복 횟수
        self._learned_candidates: List[ReflexCandidate] = []

    async def propose_new_reflexes(self, lookback: int = 50) -> List[ReflexCandidate]:
        """
        최근 기록을 분석하여 새로운 반사 행동 후보를 제안한다.
        
        Args:
            lookback: 분석할 최근 기록 수
            
        Returns:
            ReflexCandidate 리스트
        """
        # 1. 최근 성공한 진화 기록 수집
        history = self._get_recent_history(limit=lookback)
        successful_actions = [
            h for h in history 
            if h.get("status") == "success" and h.get("type") == "EVOLUTION"
        ]

        if not successful_actions:
            print("ℹ️ [ReflexLearner] 분석할 성공 기록이 없습니다.")
            return []

        # 2. 유사성 기반 군집화 (파일명 + 액션 기준)
        clusters = self._cluster_by_similarity(successful_actions)
        
        candidates = []

        # 3. 군집별 분석 및 제안 생성
        for key, group in clusters.items():
            if len(group) < self.min_occurrences:
                continue

            # Muse에게 분석 요청
            proposal = await self._analyze_cluster(key, group)
            if proposal and proposal.get("is_automatable"):
                candidate = self._create_candidate_from_proposal(proposal, key, group)
                if candidate:
                    candidates.append(candidate)

        self._learned_candidates.extend(candidates)
        print(f"💡 [ReflexLearner] {len(candidates)}개의 새로운 반사 행동 후보 제안됨")
        return candidates

    def _get_recent_history(self, limit: int) -> List[Dict[str, Any]]:
        """Nexus에서 최근 기록을 가져온다."""
        if hasattr(self.nexus, 'get_recent_history'):
            return self.nexus.get_recent_history(limit=limit)
        return []

    def _cluster_by_similarity(
        self, 
        actions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        행동들을 유사성 기준으로 군집화한다.
        
        현재는 간이 구현으로 파일명 + 액션 타입을 키로 사용.
        향후 임베딩 기반 유사도로 확장 가능.
        """
        clusters = defaultdict(list)
        
        for action in actions:
            file_name = action.get('file', 'unknown')
            action_type = action.get('action', 'unknown')
            
            # 파일 경로에서 핵심 부분 추출
            if '/' in file_name:
                file_key = file_name.split('/')[-1]
            else:
                file_key = file_name
            
            key = f"{file_key}::{action_type}"
            clusters[key].append(action)
        
        return dict(clusters)

    async def _analyze_cluster(
        self, 
        key: str, 
        group: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Muse를 사용하여 특정 패턴 그룹을 분석한다.
        
        Args:
            key: 클러스터 키 (파일명::액션)
            group: 해당 클러스터에 속한 기록들
            
        Returns:
            분석 결과 딕셔너리 또는 None
        """
        # 그룹 내 설명(Description) 요약
        descriptions = []
        for h in group:
            desc = h.get("description", "")
            if desc:
                descriptions.append(desc[:100])
        
        group_text = f"Target: {key}\n"
        group_text += f"Occurrences: {len(group)}\n"
        group_text += "Descriptions:\n"
        group_text += "\n".join(f"- {d}" for d in descriptions[:5])

        try:
            # Muse(Dreamer) 호출
            prompt = REFLEX_LEARNING_PROMPT.format(pattern_group=group_text)
            
            if hasattr(self.muse, '_ask_dreamer'):
                response = self.muse._ask_dreamer(prompt)
            elif hasattr(self.muse, 'dreamer_client'):
                result = self.muse.dreamer_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                response = result.get("content", "")
            else:
                print("⚠️ [ReflexLearner] Muse 인터페이스를 찾을 수 없습니다.")
                return None
            
            # JSON 파싱
            return self._parse_llm_response(response)
            
        except Exception as e:
            print(f"⚠️ [ReflexLearner] 클러스터 분석 실패: {e}")
            return None

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """LLM 응답에서 JSON을 추출하고 파싱한다."""
        if not response:
            return None
        
        try:
            # JSON 블록 추출 시도
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 직접 파싱 시도
            return json.loads(response)
            
        except json.JSONDecodeError:
            print(f"⚠️ [ReflexLearner] JSON 파싱 실패: {response[:100]}...")
            return None

    def _create_candidate_from_proposal(
        self,
        proposal: Dict[str, Any],
        key: str,
        group: List[Dict[str, Any]]
    ) -> Optional[ReflexCandidate]:
        """
        LLM 제안을 ReflexCandidate 객체로 변환한다.
        
        Args:
            proposal: LLM의 분석 결과
            key: 클러스터 키
            group: 원본 기록 그룹
            
        Returns:
            ReflexCandidate 또는 None
        """
        try:
            # 필수 필드 검증
            action_name = proposal.get("action_name", "")
            trigger_regex = proposal.get("trigger_regex", "")
            reflex_type = proposal.get("reflex_type", "quick_fix")
            description = proposal.get("description", "")
            
            if not action_name or not trigger_regex:
                return None
            
            # 정규표현식 유효성 검증
            try:
                re.compile(trigger_regex)
            except re.error:
                print(f"⚠️ [ReflexLearner] 유효하지 않은 정규표현식: {trigger_regex}")
                return None
            
            # 신뢰도 계산 (반복 횟수 기반)
            confidence = min(len(group) / 10.0, 1.0)
            
            # 원본 패턴 추출
            source_patterns = [key]
            for h in group[:3]:
                desc = h.get("description", "")[:50]
                if desc:
                    source_patterns.append(desc)
            
            return ReflexCandidate(
                action_name=action_name,
                trigger_regex=trigger_regex,
                reflex_type=reflex_type,
                description=description,
                confidence=confidence,
                source_patterns=source_patterns
            )
            
        except Exception as e:
            print(f"⚠️ [ReflexLearner] 후보 생성 실패: {e}")
            return None

    def get_learned_candidates(self) -> List[ReflexCandidate]:
        """학습된 모든 후보를 반환한다."""
        return self._learned_candidates.copy()

    def clear_candidates(self):
        """학습된 후보를 초기화한다."""
        self._learned_candidates.clear()

    def export_candidates_to_json(self) -> str:
        """학습된 후보들을 JSON 문자열로 내보낸다."""
        candidates_data = [c.to_dict() for c in self._learned_candidates]
        return json.dumps(candidates_data, indent=2, ensure_ascii=False)


def get_reflex_learner(nexus: "Nexus", muse: "Muse") -> ReflexLearner:
    """ReflexLearner 인스턴스를 생성하는 팩토리 함수."""
    return ReflexLearner(nexus, muse)