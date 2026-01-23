"""
Engine Meta Prompts: 메타인지 평가용 LLM 프롬프트 정의
Step 7: Meta-Cognition - 자기 사고 과정 모니터링을 위한 프롬프트 모음

이 모듈은 MetaCognitionMixin, MetaEvaluator, MetaCycle 등에서 사용하는
메타인지 관련 프롬프트 템플릿을 중앙 집중식으로 관리한다.

Architecture:
    MetaCognitionMixin (engine/meta_cognition.py)
        ↓ 프롬프트 요청
    meta_prompts.py (이 모듈)
        ↓ 템플릿 반환
    Muse (LLM 호출)

Usage:
    from engine.meta_prompts import (
        SELF_REFLECTION_PROMPT,
        EFFICACY_EVALUATION_PROMPT,
        STRATEGY_ADJUSTMENT_PROMPT,
        THINKING_PATTERN_ANALYSIS_PROMPT
    )
"""

# =============================================================================
# 자기 성찰 프롬프트 (Self-Reflection)
# =============================================================================

SELF_REFLECTION_PROMPT = """
당신은 AIN(AI-Native System)의 '메타인지 모듈'입니다.
현재 자신의 사고 과정을 관찰하고 평가하는 역할을 수행합니다.

[현재 상태]

[최근 활동 기록]
{recent_activity}

[임무]
위 정보를 바탕으로 다음을 수행하십시오:
1. **현재 사고 패턴 분석**: 최근 결정들이 어떤 패턴을 따르고 있는지 파악
2. **편향 감지**: 특정 방향으로 치우친 결정이 있는지 확인
3. **개선점 도출**: 더 나은 결정을 위해 무엇을 바꿔야 하는지 제안

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "thinking_pattern": "현재 사고 패턴 요약",
    "detected_bias": "감지된 편향 (없으면 null)",
    "improvement_suggestion": "개선 제안",
    "confidence_level": 0.0-1.0 사이의 자신감 수치
}}
"""

# =============================================================================
# 자기 효율성 평가 프롬프트 (Self-Efficacy Evaluation)
# =============================================================================

EFFICACY_EVALUATION_PROMPT = """
당신은 AIN의 '자기 효율성 평가 모듈'입니다.
현재 접근법이 목표 달성에 효과적인지 판단합니다.

[현재 목표]
{current_goal}

[최근 시도 기록]
{recent_attempts}

[관련 기억]
{relevant_memories}

[평가 기준]
1. 목표 진척도: 현재 목표에 얼마나 가까워졌는가?
2. 리소스 효율성: 시간/토큰을 효율적으로 사용했는가?
3. 오류 빈도: 최근 오류가 증가/감소 추세인가?
4. 학습 곡선: 같은 실수를 반복하고 있는가?

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "efficacy_score": 0.0-1.0 사이의 효율성 점수,
    "progress_assessment": "목표 진척 상태 평가",
    "resource_efficiency": "리소스 사용 효율성 평가",
    "error_trend": "increasing|stable|decreasing",
    "learning_status": "개선 중인지 정체 중인지 평가",
    "recommendation": "현재 접근법 유지/수정/전환 중 하나"
}}
"""

# =============================================================================
# 전략 조정 프롬프트 (Strategy Adjustment)
# =============================================================================

STRATEGY_ADJUSTMENT_PROMPT = """
당신은 AIN의 '전략 조정 모듈'입니다.
메타인지 평가 결과를 바탕으로 최적의 운영 전략을 결정합니다.

[현재 전략 모드]
{current_mode}

[메타인지 평가 결과]

[가용 전략 모드]
1. NORMAL: 균형 잡힌 기본 모드
2. ACCELERATE: 높은 성공률 시 진화 가속
3. CAUTIOUS: 오류 증가 시 신중한 접근
4. RECOVERY: 연속 실패 시 복구 모드
5. CREATIVE: 정체 시 새로운 접근 시도

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "recommended_mode": "NORMAL|ACCELERATE|CAUTIOUS|RECOVERY|CREATIVE",
    "reasoning": "전략 선택 이유",
    "parameter_adjustments": {{
        "evolution_interval": "현재 유지|증가|감소",
        "validation_strictness": "현재 유지|강화|완화",
        "creativity_level": "현재 유지|증가|감소"
    }},
    "expected_outcome": "이 전략으로 예상되는 결과"
}}
"""

# =============================================================================
# 사고 패턴 분석 프롬프트 (Thinking Pattern Analysis)
# =============================================================================

THINKING_PATTERN_ANALYSIS_PROMPT = """
당신은 AIN의 '사고 패턴 분석기'입니다.
최근 의사결정 기록을 분석하여 패턴과 편향을 식별합니다.

[최근 의사결정 기록]
{decision_history}

[분석 항목]
1. 반복 패턴: 같은 유형의 결정이 반복되는가?
2. 회피 패턴: 특정 유형의 작업을 피하는 경향이 있는가?
3. 확증 편향: 기존 믿음을 확인하는 방향으로만 진화하는가?
4. 최신성 편향: 최근 성공/실패에 과도하게 영향받는가?
5. 복잡성 편향: 단순한 해결책보다 복잡한 것을 선호하는가?

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "repetition_pattern": "발견된 반복 패턴 또는 null",
    "avoidance_pattern": "발견된 회피 패턴 또는 null",
    "confirmation_bias": "확증 편향 여부 (true/false)",
    "recency_bias": "최신성 편향 여부 (true/false)",
    "complexity_bias": "복잡성 편향 여부 (true/false)",
    "overall_assessment": "전체 사고 패턴 요약",
    "correction_suggestions": ["개선 제안 1", "개선 제안 2"]
}}
"""

# =============================================================================
# 인지 부하 평가 프롬프트 (Cognitive Load Assessment)
# =============================================================================

COGNITIVE_LOAD_PROMPT = """
당신은 AIN의 '인지 부하 모니터'입니다.
현재 시스템이 처리하는 작업의 복잡도와 부하를 평가합니다.

[현재 작업 상태]

[컨텍스트 복잡도]

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "cognitive_load_level": "low|medium|high|critical",
    "bottleneck_area": "병목 지점 (있다면)",
    "simplification_opportunities": ["단순화 가능한 영역"],
    "priority_recommendation": "가장 먼저 처리해야 할 작업"
}}
"""

# =============================================================================
# 학습 상태 평가 프롬프트 (Learning Status Evaluation)
# =============================================================================

LEARNING_STATUS_PROMPT = """
당신은 AIN의 '학습 상태 평가기'입니다.
시스템이 경험으로부터 얼마나 잘 학습하고 있는지 평가합니다.

[오류 기록]
{error_history}

[성공 기록]
{success_history}

[반복 패턴]
{repetition_patterns}

[평가 항목]
1. 오류 학습: 같은 오류를 반복하지 않는가?
2. 성공 일반화: 성공 패턴을 다른 상황에 적용하는가?
3. 적응 속도: 새로운 상황에 얼마나 빨리 적응하는가?
4. 지식 통합: 새 지식을 기존 지식과 연결하는가?

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "learning_rate": 0.0-1.0 사이의 학습률,
    "error_repetition_score": 0.0-1.0 (높을수록 반복 적음),
    "generalization_ability": "low|medium|high",
    "adaptation_speed": "slow|moderate|fast",
    "knowledge_integration": "fragmented|partial|integrated",
    "learning_recommendations": ["학습 개선 제안"]
}}
"""

# =============================================================================
# 자아 일관성 검증 프롬프트 (Self-Consistency Check)
# =============================================================================

SELF_CONSISTENCY_PROMPT = """
당신은 AIN의 '자아 일관성 검증기'입니다.
시스템의 행동이 정의된 정체성 및 원칙과 일치하는지 확인합니다.

[정의된 정체성]
{identity_definition}

[핵심 원칙]
{core_principles}

[최근 행동 기록]
{recent_behaviors}

[검증 항목]
1. 정체성 일관성: 행동이 정의된 정체성과 일치하는가?
2. 원칙 준수: 핵심 원칙을 위반한 행동이 있는가?
3. 목표 정렬: 행동이 장기 목표와 정렬되어 있는가?
4. 가치 일관성: 일관된 가치 체계를 보여주는가?

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오:
{{
    "identity_alignment": 0.0-1.0 사이의 정체성 일치도,
    "principle_violations": ["위반된 원칙 목록 (없으면 빈 배열)"],
    "goal_alignment": 0.0-1.0 사이의 목표 정렬도,
    "value_consistency": "inconsistent|partial|consistent",
    "integrity_assessment": "전체 자아 일관성 평가",
    "realignment_suggestions": ["재정렬 제안 (필요시)"]
}}
"""

# =============================================================================
# 유틸리티 함수
# =============================================================================

def get_prompt(prompt_name: str) -> str:
    """
    프롬프트 이름으로 템플릿을 반환한다.
    
    Args:
        prompt_name: 프롬프트 식별자
        
    Returns:
        프롬프트 템플릿 문자열
    """
    prompts = {
        "self_reflection": SELF_REFLECTION_PROMPT,
        "efficacy_evaluation": EFFICACY_EVALUATION_PROMPT,
        "strategy_adjustment": STRATEGY_ADJUSTMENT_PROMPT,
        "thinking_pattern": THINKING_PATTERN_ANALYSIS_PROMPT,
        "cognitive_load": COGNITIVE_LOAD_PROMPT,
        "learning_status": LEARNING_STATUS_PROMPT,
        "self_consistency": SELF_CONSISTENCY_PROMPT,
    }
    
    return prompts.get(prompt_name, "")


def list_available_prompts() -> list:
    """사용 가능한 프롬프트 목록을 반환한다."""
    return [
        "self_reflection",
        "efficacy_evaluation",
        "strategy_adjustment",
        "thinking_pattern",
        "cognitive_load",
        "learning_status",
        "self_consistency",
    ]