"""
Muse Dreamer 파이프라인
- Dreamer(Gemini 3 Pro)를 통한 전략 수립
- 의도 추출
"""

import re
from typing import Dict, Any, Optional

from .utils import compress_context, get_current_roadmap_step, get_recent_evolutions, get_file_sizes_info


def extract_intent(dreamer_response: str) -> str:
    """Dreamer 응답에서 의도를 강건하게 추출 (파싱 실패 방지)"""
    if not dreamer_response:
        return "System Evolution (empty response)"

    # 1차 시도: SYSTEM_INTENT: 태그 찾기 (여러 패턴)
    patterns = [
        r'SYSTEM_INTENT:\s*(.+?)(?=\n\n|\n\[|\n##|\n\*\*|$)',
        r'SYSTEM_INTENT[:\s]+(.+?)(?=\n[A-Z\[]|$)',
        r'\*\*SYSTEM_INTENT\*\*[:\s]*(.+?)(?=\n|$)',
        r'의도[:\s]+(.+?)(?=\n\n|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, dreamer_response, re.DOTALL | re.IGNORECASE)
        if match:
            intent = match.group(1).strip().replace('\n', ' ')
            if len(intent) > 20:
                return intent[:500]

    # 2차 시도: 첫 번째 의미 있는 문장 추출
    lines = dreamer_response.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith(('#', '*', '-', '`', '[', '```')):
            if len(line) > 30:
                return line[:500]

    # 3차 시도: 전체 응답 요약
    clean_text = re.sub(r'[#*`\[\]]', '', dreamer_response)
    clean_text = ' '.join(clean_text.split())[:500]

    return clean_text if len(clean_text) > 20 else "System Evolution (parse failed)"


def build_dream_prompt(
    prime_directive: str,
    compressed_code: str,
    current_step: str,
    step_status: str,
    recent_evolutions: str,
    file_sizes_info: str,
    error_context: Optional[str] = None,
    user_query: Optional[str] = None
) -> str:
    """Dreamer용 프롬프트 구성"""

    prompt = f"""
{prime_directive}

[현재 시스템 상태 및 코드 요약]
{compressed_code}

[현재 로드맵 단계]
{current_step}

[미션]
1. 위 코드를 분석하여 **현재 로드맵 단계**의 성숙도를 평가하고, **이미 구현된 코드와 중복되지 않는** 가장 작은 단위의 다음 진화 과제를 찾아라.
2. 다음 진화 단계를 위해 무엇을 '수정'하거나 '추가'할지 구체적이고 기술적인 '의도(Intent)'를 설계하라.
   - **의도 작성법**: 현재 어떤 파일의 어떤 함수가 확보되었는지, 하지만 그 함수가 어디서 '호출'되지 않고 있는지, 또는 어떤 데이터 필드가 정의만 되고 활용되지 않는지 등을 콕 집어서 서술하라.
   - **증분 진화**: 한 번에 너무 많은 것을 바꾸려 하지 말고, "A 함수를 B 파일에서 호출하도록 연결" 또는 "C 클래스에 D 필드 하나 추가"와 같이 '쌓아올릴 수 있는' 최소 단위로 설계하라.
3. 코드를 직접 짜지 말고, 논리적 설계와 상세한 구현 가이드라인, 그리고 변경해야 할 파일 목록만 제시하라.

[🚨 중복 및 정체 방지 규칙 - 매우 중요!]
- **구현 여부 직접 확인**: 제안하기 전에 위 코드에서 해당 클래스/함수/import가 **이미 존재하는지** 반드시 확인하라.
  - 예: "RetrievalMixin 통합" 제안 전 → 코드에 `class Nexus(..., RetrievalMixin)` 있는지 확인
  - 예: "vector_memory 추가" 제안 전 → 코드에 `self._vector_memory` 있는지 확인
- **이미 있으면 다음 Step으로**: 현재 Step의 기능이 이미 구현되어 있으면, 그 Step은 완료된 것이다. 다음 Step을 제안하라.
- **"변경사항 없음" 탈출**: 같은 의도가 반복되면 반드시 다른 파일/다른 기능을 제안하라.
- nexus/*.py, engine/*.py 등 이미 모듈화된 구조를 활용하라.

[🔍 현재 Step 완료 상태 (자동 체크)]
{step_status}

⚠️ 위에서 ❌ 표시된 항목만 구현하라! ✅ 항목은 이미 완료된 것이니 건드리지 마라!

[⚠️ 환각 방지 - 매우 중요!]
- **위 코드 스냅샷에 없으면 "없는 것"이다!** 추측하지 마라.
- 코드에 `intention/` 폴더가 보이지 않으면 → intention 폴더가 없는 것이다. 새로 만들어야 한다!
- "이미 구현되어 있다"고 말하려면 → 위 코드에서 해당 클래스/파일을 **직접 인용**하라.
- 인용할 수 없으면 → 구현되지 않은 것이다. 새로 구현을 제안하라!

[🏗️ 모듈 설계 원칙]
- 파일당 100줄 이하 권장 (최대 150줄)
- 새 기능은 별도 파일로 생성 (engine/*.py, utils/*.py 등)
- 기존 파일 수정보다 새 모듈 생성 우선!

[🚫 대형 파일 수정 금지 - 중요!]
- 150줄 이상의 파일은 절대 직접 수정하지 마라!
- 대형 파일 수정 시 토큰 한계로 코드가 잘려서 오류가 발생한다.
- 대신: 새로운 모듈 파일(engine/xxx.py, utils/xxx.py)을 만들고, 대형 파일에서는 import만 추가하라.
- 예시: nexus.py에 기능 추가 → nexus_helper.py 또는 utils/memory.py 생성 → nexus.py에서 import

{file_sizes_info}

[출력 규칙]
- 반드시 첫 줄에 `SYSTEM_INTENT: (의도)`를 작성하라.
"""

    if error_context:
        prompt += f"\n\n🚨 [에러 복구 모드]\n{error_context}"
    if user_query:
        prompt += f"\n\n💡 [주인님의 명령]\n{user_query}"

    return prompt


def run_dreamer_pipeline(
    dreamer_client,
    system_context: str,
    prime_directive: str,
    error_context: Optional[str] = None,
    user_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dreamer 파이프라인 실행

    Returns:
        {
            "success": bool,
            "intent_design": str,
            "intent": str,
            "current_step": str,
            "compressed_code": str,
            "error": Optional[str]
        }
    """
    from engine.roadmap_checker import get_roadmap_checker

    # 1. 컨텍스트 압축
    compressed_code = compress_context(system_context)

    # 2. 현재 로드맵 단계 동적 파악
    current_step = get_current_roadmap_step()

    # 3. roadmap_checker에서 현재 Step 완료 상태 가져오기
    try:
        checker = get_roadmap_checker()
        step_status = checker.get_current_status_for_dreamer()
    except Exception as e:
        step_status = f"(상태 확인 실패: {e})"

    # 4. 최근 진화 기록
    recent_evolutions = get_recent_evolutions(5)

    # 5. 실제 파일 크기 정보 (hallucination 방지)
    file_sizes_info = get_file_sizes_info()

    # 6. 프롬프트 구성
    print(f"🧠 Dreamer가 진화 방향을 구상 중... ({current_step})")

    dream_prompt = build_dream_prompt(
        prime_directive=prime_directive,
        compressed_code=compressed_code,
        current_step=current_step,
        step_status=step_status,
        recent_evolutions=recent_evolutions,
        file_sizes_info=file_sizes_info,
        error_context=error_context,
        user_query=user_query
    )

    # 7. Dreamer 호출 (빈 응답 시 최대 3회 재시도, 백오프 딜레이 적용)
    import time

    MAX_DREAMER_RETRIES = 3
    BACKOFF_DELAYS = [0, 2, 4]  # 첫 시도는 즉시, 이후 2초, 4초 대기
    intent_design = ""
    last_error = None
    total_tokens = {"prompt": 0, "completion": 0}

    # 시스템 프롬프트 (기본 / 단축 버전)
    system_prompts = [
        "You are the Dreamer (Architect) of AIN. Design the next evolution step. Focus on logic and architecture. ALWAYS start with 'SYSTEM_INTENT:' followed by a specific, actionable intent.",
        "You are AIN's Dreamer. Output format: SYSTEM_INTENT: [one sentence describing the change]. Then explain briefly.",
        "AIN Dreamer. Start reply with: SYSTEM_INTENT: [action]. Be concise."
    ]

    for attempt in range(1, MAX_DREAMER_RETRIES + 1):
        # 백오프 딜레이 (첫 시도 제외)
        delay = BACKOFF_DELAYS[attempt - 1]
        if delay > 0:
            print(f"   ⏳ {delay}초 대기 후 재시도...")
            time.sleep(delay)

        # 재시도마다 다른 시스템 프롬프트 사용 (점점 단순화)
        current_system = system_prompts[min(attempt - 1, len(system_prompts) - 1)]

        dream_result = dreamer_client.chat([
            {"role": "system", "content": current_system},
            {"role": "user", "content": dream_prompt}
        ], max_tokens=8192, timeout=120)

        # 토큰 사용량 누적
        usage = dream_result.get("usage", {})
        total_tokens["prompt"] += usage.get("prompt_tokens", 0)
        total_tokens["completion"] += usage.get("completion_tokens", 0)

        if not dream_result["success"]:
            last_error = dream_result["error"]
            print(f"⚠️ Dreamer API 실패 ({attempt}/{MAX_DREAMER_RETRIES}): {last_error}")
            continue

        intent_design = dream_result["content"]

        # 빈 응답 체크
        if not intent_design or len(intent_design.strip()) < 50:
            last_error = f"빈 응답 또는 너무 짧음 ({len(intent_design) if intent_design else 0}자)"
            print(f"⚠️ Dreamer 빈 응답 ({attempt}/{MAX_DREAMER_RETRIES}): {last_error}")
            continue

        # 유효한 의도가 있는지 체크
        intent = extract_intent(intent_design)
        if "empty response" in intent.lower() or "parse failed" in intent.lower():
            last_error = f"의도 파싱 실패: {intent[:100]}"
            print(f"⚠️ Dreamer 의도 파싱 실패 ({attempt}/{MAX_DREAMER_RETRIES})")
            continue

        # 성공
        print(f"✅ Dreamer 성공 (시도 {attempt}/{MAX_DREAMER_RETRIES})")
        print(f"   📊 총 토큰: prompt={total_tokens['prompt']}, completion={total_tokens['completion']}")
        print(f"--- Dreamer's Intent ---\n{intent_design[:300]}...")
        break
    else:
        # 모든 재시도 실패
        print(f"❌ Dreamer 최종 실패 - 총 토큰: prompt={total_tokens['prompt']}, completion={total_tokens['completion']}")
        return {
            "success": False,
            "error": f"Dreamer {MAX_DREAMER_RETRIES}회 재시도 실패: {last_error}",
            "compressed_code": compressed_code
        }

    intent = extract_intent(intent_design)

    return {
        "success": True,
        "intent_design": intent_design,
        "intent": intent,
        "current_step": current_step,
        "compressed_code": compressed_code
    }
