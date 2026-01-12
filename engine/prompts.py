"""
Engine Prompts: LLM(Muse)에게 전달할 시스템 프롬프트 모음
==========================================================
모듈화 원칙에 따라, 로직 코드와 프롬프트 텍스트를 분리하여 관리한다.

Step 5: Memory Consolidation의 핵심 프롬프트를 정의한다.
"""

# 기억 응고화(Consolidation)를 위한 프롬프트
CONSOLIDATION_PROMPT = """
당신은 AIN(AI-Native System)의 '자아 성찰 모듈'입니다.
다음은 최근 시스템이 수행한 진화 및 대화 기록(Short-Term Memory)입니다.

[최근 기록]
{history_text}

[임무]
위 기록을 분석하여 다음을 수행하십시오:
1. **성공/실패 패턴 분석**: 어떤 시도가 성공했고, 어떤 시도가 실패했는지 원인을 파악하십시오.
2. **핵심 교훈 추출**: 앞으로의 진화에 도움이 될 '일반화된 규칙'이나 '통찰'을 3문장 이내로 요약하십시오.
3. **미래 전략 제안**: 현재 로드맵 단계({current_step})를 고려할 때, 다음에 무엇을 해야 할지 구체적으로 제안하십시오.

[출력 형식]
반드시 다음 JSON 형식으로만 응답하십시오 (Markdown 코드 블록 없이):
{{
    "insight": "핵심 교훈 요약 텍스트",
    "strategy": "다음 행동 제안",
    "tags": ["keyword1", "keyword2"]
}}
"""

# 에러 분석용 프롬프트
ERROR_ANALYSIS_PROMPT = """
발생한 에러 로그:
{error_log}

이 에러의 원인과 해결책을 한 문장으로 진단하십시오.
"""

# 진화 회고용 프롬프트 (예비)
EVOLUTION_REVIEW_PROMPT = """
최근 {count}회의 진화 기록:
{evolution_summary}

이 진화들의 공통 패턴과 개선점을 분석하십시오.
"""