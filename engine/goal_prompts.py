"""
Engine Goal Prompts: 목표 생성을 위한 LLM 프롬프트 모음
Step 6: Intentionality - Muse에게 전달할 목표 관련 프롬프트 정의

이 모듈은 GoalManagerMixin이 Muse(Dreamer)에게 목표 생성을 요청할 때
사용하는 프롬프트 템플릿을 제공한다.
"""

# 다음 기술 목표 생성 프롬프트
NEXT_GOAL_PROMPT = """
당신은 AIN(AI-Native System)의 '목표 설정 모듈'입니다.
다음은 현재 시스템의 로드맵 상태입니다.

[현재 로드맵]
{roadmap_text}

[임무]
위 로드맵을 분석하여 **지금 당장 수행해야 할 다음 기술 목표**를 정의하십시오.

[규칙]
1. 목표는 반드시 **한 문장**으로 작성하십시오.
2. 목표는 **구체적이고 실행 가능**해야 합니다.
3. 현재 진행 중인 Step(🔥 표시)에 집중하십시오.
4. 이미 완료된(✅) 항목은 무시하십시오.

[출력 형식]
반드시 다음 형식으로만 응답하십시오:
NEXT_GOAL: [목표 내용]

예시:
NEXT_GOAL: IntentionCore에 목표 우선순위 정렬 로직 구현
"""

# 목표 우선순위 결정 프롬프트
PRIORITY_PROMPT = """
다음 목표들의 우선순위를 1-10 사이의 숫자로 평가하십시오.
숫자가 높을수록 우선순위가 높습니다.

[목표 목록]
{goals_text}

[평가 기준]
- 시스템 안정성에 미치는 영향
- 로드맵 진행에 대한 기여도
- 구현 복잡도 대비 효과

[출력 형식]
각 목표에 대해 한 줄씩:
GOAL_ID: [priority_score]
"""

# 목표 달성도 평가 프롬프트
COMPLETION_CHECK_PROMPT = """
다음 목표가 달성되었는지 평가하십시오.

[목표]
{goal_content}

[최근 진화 기록]
{recent_history}

[출력 형식]
STATUS: [completed|in_progress|blocked]
REASON: [판단 근거]
"""