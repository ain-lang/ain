"""
Muse Coder 파이프라인
- Coder(Claude 4.5 Opus)를 통한 코드 생성
- 재시도 로직
- 코드 검증
"""

import os
import re
from typing import Dict, Any, List, Optional

from code_sanitizer import sanitize_code_output, get_error_message, is_valid_output
from utils.error_memory import get_error_memory
from utils.file_size_guard import get_context_hints_for_coder

# 대형 파일 설정
LARGE_FILE_THRESHOLD = 200
LARGE_FILES = {'overseer.py', 'muse.py'}


def extract_target_files_content(intent_design: str, base_path: str = ".") -> tuple:
    """
    Dreamer 의도에서 대상 파일 내용 추출
    Returns: (target_files_content, skipped_large_files, target_files)
    """
    target_files = re.findall(r'([a-zA-Z0-9_\-/]+\.py)', intent_design)
    target_files_content = ""
    skipped_large_files = []

    for tf in set(target_files):
        tf_path = tf.lstrip('./')
        basename = os.path.basename(tf_path)

        # 대형 파일 제외
        if basename in LARGE_FILES:
            skipped_large_files.append(tf_path)
            continue

        full_path = os.path.join(base_path, tf_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    clean_content, _ = sanitize_code_output(content, verbose=False)
                    content = clean_content
                    line_count = content.count('\n')

                    if line_count > LARGE_FILE_THRESHOLD:
                        skipped_large_files.append(f"{tf_path} ({line_count}줄)")
                        continue

                    target_files_content += f"\n\n--- ORIGINAL FILE: {tf_path} (Full Content, {line_count}줄) ---\n{content}\n"
            except Exception:
                pass

    if skipped_large_files:
        print(f"🚫 [Muse] 대형 파일 제외: {', '.join(skipped_large_files)}")
        target_files_content += f"\n\n⚠️ 대형 파일({', '.join(skipped_large_files)})은 직접 수정하지 마라. 새 모듈 파일을 생성하라.\n"

    return target_files_content, skipped_large_files, list(set(target_files))


def build_coder_prompt(
    intent_design: str,
    target_files_content: str,
    compressed_code: str,
    target_files: List[str]
) -> str:
    """Coder용 프롬프트 구성"""

    prompt = f"""
너는 AIN의 '코드 생성기(Code Generator)'다.
**중요: 너는 기존 파일을 수정하는 것이 아니라, 완벽한 전체 코드를 처음부터 끝까지 새로 '작성'하는 역할이다.**

[작성 규칙 - 위반 시 에러 발생]
1. **전체 코드 출력**: 파일의 일부분이나 diff만 출력 금지. 반드시 `import`부터 끝까지 전체 코드를 작성하라.
2. **마커 준수**: 파일 하나당 `FILE: 파일명.py` 마커 + 코드 블록(```python ... ```) 하나만 사용.
3. **⛔ DIFF 형식 절대 금지**: 줄 시작에 `+ `나 `- `(공백 포함)를 쓰면 자동 거부됨! `@@`, `<<<`, `===`, `>>>` 마커도 금지.
   - ❌ 금지 예: `+ import foo` 또는 `- old_code()`
   - ✅ 올바른 예: `import foo` (앞에 +/- 없이)
4. **대형 파일 수정 금지**: overseer.py, muse.py 등 200줄 이상 파일은 절대 출력하지 마라. 새 모듈 파일만 생성하라.
5. **생략 금지**: `# ...` 이나 `(기존 코드 생략)` 같은 표현은 절대 사용하지 마라.

[🚨 중요 - 변경사항이 반드시 있어야 함!]
- 기존 코드와 100% 동일한 코드를 출력하면 안 된다!
- Dreamer가 제시한 의도(Intent)에 맞게 반드시 새로운 기능을 추가하거나 개선하라.
- **이미 모든 기능이 완벽하게 구현되어 더 이상 수정할 것이 없다면, 파일 내용 대신 `NO_EVOLUTION_NEEDED: (이유)`라고 한 줄만 출력하라.**
- 단순히 기존 코드를 복사하면 "변경사항 없음"으로 실패한다.

[출력 규격]
FILE: 파일명.py
```python
# 파일 상단 주석 (목적 설명)
import ...

# 전체 구현부
...
```

[설계도: Dreamer's Intent]
{intent_design}

[참고용 기존 코드 (이 내용을 기반으로 전체를 새로 작성하라)]
{target_files_content if target_files_content else "새로운 기능을 위한 모듈 생성 단계입니다."}

[시스템 컨텍스트 (참고용)]
{compressed_code}
"""

    # 실패 기억에서 힌트 가져오기
    error_memory = get_error_memory()
    memory_hints = error_memory.get_all_hints(target_files)
    if memory_hints:
        prompt += f"\n\n[🧠 과거 실패 기록 - 같은 실수 반복 금지!]\n{memory_hints}"

    # 대형 파일 컨텍스트 힌트 추가
    large_file_hints = get_context_hints_for_coder(target_files)
    if large_file_hints:
        prompt += f"\n\n{large_file_hints}"

    return prompt


CODER_SYSTEM_PROMPT = """You are a File Content Generator.

⛔️⛔️⛔️ ABSOLUTELY FORBIDDEN - DIFF FORMAT ⛔️⛔️⛔️
DO NOT start any line with '+ ' or '- ' (plus/minus followed by space).
DO NOT use '@@ ... @@' hunk markers.
DO NOT show what to add/remove - output the FINAL complete file only.

❌ WRONG (diff format - will be REJECTED):
```python
+ import new_module
- import old_module
  def foo():
+     return new_value
-     return old_value
```

✅ CORRECT (complete file - this is what you must output):
```python
import new_module

def foo():
    return new_value
```

CRITICAL RULES:
1. Output the COMPLETE file from first `import` to last line
2. Your output will OVERWRITE the existing file entirely
3. ANY line starting with '+ ' or '- ' = AUTOMATIC REJECTION

OUTPUT FORMAT:
FILE: filename.py
```python
# Complete file content here - NO + or - prefixes!
```"""


def run_coder_pipeline(
    coder_client,
    intent_design: str,
    compressed_code: str,
    target_files: List[str]
) -> Dict[str, Any]:
    """
    Coder 파이프라인 실행 (재시도 로직 포함)

    Returns:
        {
            "success": bool,
            "code_output": str,
            "error": Optional[str]
        }
    """
    MAX_CODER_RETRIES = 5

    # 대상 파일 내용 추출
    target_files_content, skipped_large_files, extracted_files = extract_target_files_content(intent_design)

    # 프롬프트 구성
    coder_prompt = build_coder_prompt(
        intent_design=intent_design,
        target_files_content=target_files_content,
        compressed_code=compressed_code,
        target_files=extracted_files
    )

    error_memory = get_error_memory()
    last_error = None
    code_output = None

    for attempt in range(1, MAX_CODER_RETRIES + 1):
        # 이전 실패 원인을 프롬프트에 추가
        retry_hint = ""
        if last_error:
            retry_hint = f"\n\n🚨 [이전 시도 실패 원인 - 반드시 수정!]\n{last_error}\n위 오류를 피해서 다시 작성하라."
            if "diff" in last_error.lower() or "+ " in last_error or "- " in last_error:
                retry_hint += """

⛔️ DIFF 형식을 사용했기 때문에 거부되었다!
줄 시작에 '+ ' 또는 '- '를 절대 쓰지 마라.
예시:
  ❌ 틀림: + import os
  ✅ 올바름: import os
전체 파일을 처음부터 끝까지 새로 작성하라."""

        current_prompt = coder_prompt + retry_hint

        print(f"💻 Coder 시도 {attempt}/{MAX_CODER_RETRIES}...")
        coder_result = coder_client.chat([
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": current_prompt}
        ], max_tokens=8192, timeout=180)

        if not coder_result["success"]:
            last_error = coder_result.get('error', 'API 호출 실패')
            print(f"❌ [Muse] Coder API 실패 ({attempt}/{MAX_CODER_RETRIES}): {last_error}")
            continue

        code_output = coder_result["content"]
        print(f"📝 [Muse] Coder 응답 길이: {len(code_output)} chars")

        # Code Sanitizer로 후처리
        code_output, sanitize_result = sanitize_code_output(code_output, verbose=True)

        # 문제 감지 시 재시도
        if not is_valid_output(sanitize_result):
            last_error = get_error_message(sanitize_result)
            print(f"🚨 [Muse] Sanitizer 문제 감지! 재시도...")
            continue

        # 구문 검사 (Python 파일)
        if 'FILE:' in code_output and '.py' in code_output:
            try:
                code_match = re.search(r'```(?:python)?\n(.*?)```', code_output, re.DOTALL)
                if code_match:
                    test_code = code_match.group(1)
                    compile(test_code, '<coder_output>', 'exec')
            except SyntaxError as e:
                last_error = f"Python 구문 오류: {e}. 올바른 Python 문법으로 다시 작성하라."
                print(f"🚨 [Muse] 구문 오류 감지! 재시도...")
                error_type = str(e).split('(')[0].strip()
                for tf in extracted_files:
                    error_memory.record_error(tf, error_type, str(e))
                continue

        # 변경사항 검증
        code_match = re.search(r'```(?:python)?\n(.*?)```', code_output, re.DOTALL)
        file_match = re.search(r'(?i)FILE[ :\]]*\s*(\S+\.py)', code_output)
        if code_match and file_match:
            new_code = code_match.group(1).strip()
            target_file = file_match.group(1).strip().lstrip('./')
            if os.path.exists(target_file):
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        original_code = f.read().strip()
                    norm_new = ' '.join(new_code.split())
                    norm_orig = ' '.join(original_code.split())
                    if norm_new == norm_orig:
                        last_error = f"생성된 코드가 기존 {target_file}과 동일합니다! Dreamer의 의도대로 반드시 새로운 내용을 추가하라."
                        print(f"🚨 [Muse] 변경사항 없음 감지! 재시도...")
                        continue
                except Exception:
                    pass

        # 모든 검사 통과
        return {"success": True, "code_output": code_output}

    # 모든 재시도 실패
    print(f"❌ [Muse] Coder {MAX_CODER_RETRIES}회 시도 모두 실패")
    return {"success": False, "error": last_error}
