import re
import os
from api import OpenRouterClient
from code_sanitizer import sanitize_code_output, get_error_message, is_valid_output
from utils.error_memory import get_error_memory

class Muse:
    """
    AIN의 Muse Generator (Dynamic Tensor Flow):
    2x2 매트릭스 아키텍처를 기반으로 '상상'과 '구현'을 분리한다.
    - Dreamer: Gemini 3 Pro (고차원 추론 및 전략 수립)
    - Coder: Claude 4.5 Opus (정교한 코드 생성 및 버그 수정)
    """
    def __init__(self, dreamer_model: str, coder_model: str, prime_directive: str):
        self.dreamer_client = OpenRouterClient(model=dreamer_model)
        self.coder_client = OpenRouterClient(model=coder_model)
        self.prime_directive = prime_directive

    def _ask_dreamer(self, prompt: str) -> str:
        """
        Dreamer에게 간단한 질문을 하고 응답을 받음
        Inner Monologue 등 외부 모듈에서 사용
        """
        try:
            result = self.dreamer_client.chat([
                {"role": "system", "content": "너는 AIN의 내부 의식이다. 간결하고 성찰적으로 답하라."},
                {"role": "user", "content": prompt}
            ])
            if result.get("success"):
                return result.get("content", "")
            return ""
        except Exception as e:
            print(f"⚠️ Dreamer 질문 실패: {e}")
            return ""

    def _compress_context(self, system_context):
        """[Cost Optimization] 전체 코드베이스에서 핵심 로직만 추출하여 전송량을 줄임"""
        compressed = ""
        # snapshot의 "--- FILE: filename ---" 형식에 맞게 분리
        sections = system_context.split("--- FILE: ")
        for section in sections:
            if not section.strip(): continue
            lines = section.split(" ---")
            if len(lines) < 2: continue
            
            filename = lines[0].strip()
            content = lines[1].strip()
            
            # 핵심 로직 파일(fact_core, corpus_callosum, database/)은 비중있게, 나머지는 요약
            if any(core in filename for core in ["fact_core.py", "corpus_callosum.py", "database/"]):
                limit = 10000 # Pro/Opus는 더 넓은 컨텍스트 가능
            elif any(core in filename for core in ["muse.py", "nexus.py", "overseer.py"]):
                limit = 4000
            else:
                limit = 1000 # main.py 등은 최소한의 정보만
                
            compressed += f"\n--- FILE: {filename} ---\n{content[:limit]}\n"
        return compressed

    def _get_current_roadmap_step(self):
        """ROADMAP.md에서 현재 진행 중인 Step(🔥)을 동적으로 읽어옴"""
        try:
            with open("ROADMAP.md", "r", encoding="utf-8") as f:
                content = f.read()
            # 🔥 마커가 있는 줄을 찾음
            for line in content.split("\n"):
                if "🔥" in line:
                    return line.strip()
            return "다음 진화 단계 탐색 중"
        except:
            return "Step 5: Memory Consolidation"

    def _extract_intent(self, dreamer_response: str) -> str:
        """
        Dreamer 응답에서 의도를 강건하게 추출 (파싱 실패 방지)
        """
        if not dreamer_response:
            return "System Evolution (empty response)"
        
        # 1차 시도: SYSTEM_INTENT: 태그 찾기 (여러 패턴)
        patterns = [
            r'SYSTEM_INTENT:\s*(.+?)(?=\n\n|\n\[|\n##|\n\*\*|$)',  # 기본
            r'SYSTEM_INTENT[:\s]+(.+?)(?=\n[A-Z\[]|$)',  # 대문자/괄호로 끝남
            r'\*\*SYSTEM_INTENT\*\*[:\s]*(.+?)(?=\n|$)',  # 볼드 형식
            r'의도[:\s]+(.+?)(?=\n\n|$)',  # 한글 "의도:"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, dreamer_response, re.DOTALL | re.IGNORECASE)
            if match:
                intent = match.group(1).strip().replace('\n', ' ')
                if len(intent) > 20:  # 최소 길이 확인
                    return intent[:500]
        
        # 2차 시도: 첫 번째 의미 있는 문장 추출
        lines = dreamer_response.split('\n')
        for line in lines:
            line = line.strip()
            # 마크다운 헤더, 빈 줄, 코드 블록 제외
            if line and not line.startswith(('#', '*', '-', '`', '[', '```')):
                if len(line) > 30:  # 너무 짧은 줄 제외
                    return line[:500]
        
        # 3차 시도: 전체 응답 요약
        clean_text = re.sub(r'[#*`\[\]]', '', dreamer_response)
        clean_text = ' '.join(clean_text.split())[:500]
        
        return clean_text if len(clean_text) > 20 else "System Evolution (parse failed)"

    def _get_recent_evolutions(self, limit=5):
        """최근 진화 기록에서 파일명과 설명을 추출"""
        try:
            import json
            with open("evolution_history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            
            recent = history[-limit:] if len(history) >= limit else history
            result = []
            for h in reversed(recent):
                file = h.get("file", "unknown")
                desc = h.get("description", "")[:100]
                result.append(f"- {file}: {desc}...")
            return "\n".join(result) if result else "없음"
        except:
            return "없음"

    def imagine(self, system_context, user_query=None, evolution_history=None, error_context=None):
        """[Muse] Dreamer와 Coder의 협업을 통해 진화를 상상함"""
        
        # 1. 컨텍스트 압축 및 대상 파일 원본 추출
        # Dreamer에게는 요약본을 주지만, Coder에게는 수정할 파일의 전체 원본을 줄 예정
        compressed_code = self._compress_context(system_context)
        
        # 1.5 현재 로드맵 단계 동적 파악
        current_step = self._get_current_roadmap_step()
        
        # 1.6 최근 진화 기록 가져오기
        recent_evolutions = self._get_recent_evolutions(5)
        
        # 2. [Dreamer - Gemini 3 Pro] 전략 및 의도 수립
        print(f"🧠 Dreamer가 진화 방향을 구상 중... ({current_step})")
        
        dream_prompt = f"""
{self.prime_directive}

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

[🔍 Step 완료 판단 기준]
- Step 4 (Vector Memory): `RetrievalMixin` 상속, `vector_memory` 프로퍼티, `search_semantic_memory` 메서드 존재 → 완료
- Step 5 (Inner Monologue): `ConsciousnessMixin` 상속, `_inner_monologue` 메서드, `_ask_dreamer` 호출 존재 → 완료
- 현재 Step이 완료되었으면 **ROADMAP.md의 다음 Step**을 확인하고 그 작업을 제안하라.

[🏗️ 모듈 설계 원칙]
- 파일당 100줄 이하 권장 (최대 150줄)
- 새 기능은 별도 파일로 생성 (utils/*.py 등)

[🚫 대형 파일 수정 금지 - 중요!]
- overseer.py, muse.py 등 200줄 이상의 파일은 절대 직접 수정하지 마라!
- 대형 파일 수정 시 토큰 한계로 코드가 잘려서 오류가 발생한다.
- 대신: 새로운 모듈 파일(engine/xxx.py, utils/xxx.py)을 만들고, 대형 파일에서는 import만 추가하라.
- 예시: nexus.py에 기능 추가 → nexus_helper.py 또는 utils/memory.py 생성 → nexus.py에서 import

[출력 규칙]
- 반드시 첫 줄에 `SYSTEM_INTENT: (의도)`를 작성하라.
"""
        if error_context:
            dream_prompt += f"\n\n🚨 [에러 복구 모드]\n{error_context}"
        if user_query:
            dream_prompt += f"\n\n💡 [주인님의 명령]\n{user_query}"

        dream_result = self.dreamer_client.chat([
            {"role": "system", "content": "You are the Dreamer (Architect) of AIN. Design the next evolution step. Focus on logic and architecture."},
            {"role": "user", "content": dream_prompt}
        ], timeout=120)

        if not dream_result["success"]:
            return {"intent": "Dreaming failed", "updates": [], "error": dream_result["error"]}

        intent_design = dream_result["content"]
        print(f"--- Dreamer's Intent ---\n{intent_design[:300]}...")

        # 2.5 Coder를 위한 대상 파일 원본 추출
        # Dreamer가 제안한 파일들 중 기존에 존재하는 파일의 전체 내용을 가져옴
        # 경로 포함된 파일명 추출 (예: engine/core.py, facts/node.py)
        # 🚫 대형 파일(200줄 이상)은 제외
        LARGE_FILE_THRESHOLD = 200
        # 실제 대형 파일만 (nexus, corpus_callosum, fact_core는 이미 분리 완료)
        LARGE_FILES = {'overseer.py', 'muse.py'}
        
        target_files = re.findall(r'([a-zA-Z0-9_\-/]+\.py)', intent_design)
        target_files_content = ""
        skipped_large_files = []
        
        from code_sanitizer import sanitize_code_output

        for tf in set(target_files):
            tf_path = tf.lstrip('./')
            basename = os.path.basename(tf_path)
            
            # 대형 파일 제외
            if basename in LARGE_FILES:
                skipped_large_files.append(tf_path)
                continue
            
            if os.path.exists(tf_path) and os.path.isfile(tf_path):
                try:
                    with open(tf_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 🧼 컨텍스트 정화: Coder에게 줄 기존 코드에서 충돌 마커 등 제거
                        clean_content, _ = sanitize_code_output(content, verbose=False)
                        content = clean_content
                        line_count = content.count('\n')
                        
                        # 200줄 이상이면 제외
                        if line_count > LARGE_FILE_THRESHOLD:
                            skipped_large_files.append(f"{tf_path} ({line_count}줄)")
                            continue
                        
                        target_files_content += f"\n\n--- ORIGINAL FILE: {tf_path} (Full Content, {line_count}줄) ---\n{content}\n"
                except: pass
        
        if skipped_large_files:
            print(f"🚫 [Muse] 대형 파일 제외: {', '.join(skipped_large_files)}")
            target_files_content += f"\n\n⚠️ 대형 파일({', '.join(skipped_large_files)})은 직접 수정하지 마라. 새 모듈 파일을 생성하라.\n"

        # 3. [Coder - Claude 4.5 Opus] 실제 코드 구현
        print(f"💻 Coder (Claude 4.5 Opus)가 새로운 모듈을 생성 중...")
        coder_prompt = f"""
너는 AIN의 '코드 생성기(Code Generator)'다. 
**중요: 너는 기존 파일을 수정하는 것이 아니라, 완벽한 전체 코드를 처음부터 끝까지 새로 '작성'하는 역할이다.**

[작성 규칙 - 위반 시 에러 발생]
1. **전체 코드 출력**: 파일의 일부분이나 수정된 내용(diff)만 출력하는 것은 절대 금지된다. 반드시 `import`부터 끝까지 전체 코드를 작성하라.
2. **마커 준수**: 파일 하나당 하나의 `FILE: 파일명.py` 마커와 하나의 코드 블록(```python ... ```)만 사용하라.
3. **금지 기호**: `+`, `-`, `<<<<<<<`, `=======`, `>>>>>>>` 등 diff나 충돌 마커는 절대 포함하지 마라.
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
        # 🧠 실패 기억에서 힌트 가져오기
        error_memory = get_error_memory()
        memory_hints = error_memory.get_all_hints(target_files)
        if memory_hints:
            coder_prompt += f"\n\n[🧠 과거 실패 기록 - 같은 실수 반복 금지!]\n{memory_hints}"
        
        # 🔄 Coder 재시도 로직 (최대 5회)
        MAX_CODER_RETRIES = 5
        last_error = None
        code_output = None
        
        for attempt in range(1, MAX_CODER_RETRIES + 1):
            # 이전 실패 원인을 프롬프트에 추가
            retry_hint = ""
            if last_error:
                retry_hint = f"\n\n🚨 [이전 시도 실패 원인 - 반드시 수정!]\n{last_error}\n위 오류를 피해서 다시 작성하라."
            
            current_prompt = coder_prompt + retry_hint
            
            print(f"💻 Coder 시도 {attempt}/{MAX_CODER_RETRIES}...")
            coder_result = self.coder_client.chat([
                {"role": "system", "content": "You are a File Content Generator. You ALWAYS provide the full content of the file, never a diff or partial update. Your output must be ready to overwrite the existing file entirely."},
                {"role": "user", "content": current_prompt}
            ], max_tokens=8192, timeout=180)
            
            if not coder_result["success"]:
                last_error = coder_result.get('error', 'API 호출 실패')
                print(f"❌ [Muse] Coder API 실패 ({attempt}/{MAX_CODER_RETRIES}): {last_error}")
                continue
            
            code_output = coder_result["content"]
            print(f"📝 [Muse] Coder 응답 길이: {len(code_output)} chars")
            
            # 🔧 Code Sanitizer로 후처리 (보호된 모듈)
            code_output, sanitize_result = sanitize_code_output(code_output, verbose=True)
            
            # 🚨 문제 감지 시 재시도
            if not is_valid_output(sanitize_result):
                last_error = get_error_message(sanitize_result)
                print(f"🚨 [Muse] Sanitizer 문제 감지! 재시도...")
                continue
            
            # 🚨 구문 검사 (Python 파일)
            if 'FILE:' in code_output and '.py' in code_output:
                try:
                    # 코드 블록 추출 후 구문 검사
                    code_match = re.search(r'```(?:python)?\n(.*?)```', code_output, re.DOTALL)
                    if code_match:
                        test_code = code_match.group(1)
                        compile(test_code, '<coder_output>', 'exec')
                except SyntaxError as e:
                    last_error = f"Python 구문 오류: {e}. 올바른 Python 문법으로 다시 작성하라."
                    print(f"🚨 [Muse] 구문 오류 감지! 재시도...")
                    # 🧠 실패 기억에 기록
                    error_type = str(e).split('(')[0].strip()  # 예: "unterminated string literal"
                    for tf in target_files:
                        error_memory.record_error(tf, error_type, str(e))
                    continue
            
            # 모든 검사 통과
            break
        else:
            # 모든 재시도 실패
            print(f"❌ [Muse] Coder {MAX_CODER_RETRIES}회 시도 모두 실패")
            return {"intent": "Coding failed after retries", "updates": [], "error": last_error}
        
        if not code_output:
            return {"intent": "Coding failed", "updates": [], "error": "No code output"}
        
        # 3.5 [New] 무의미한 진화 시도 차단
        if "NO_EVOLUTION_NEEDED" in code_output:
            reason = code_output.split("NO_EVOLUTION_NEEDED:")[-1].strip()
            print(f"😴 [Muse] 진화 불필요 판단: {reason}")
            return {"intent": f"진화 스킵: {reason}", "updates": [], "no_evolution": True}

        # 4. 결과 파싱 - 🔧 강화된 의도 추출
        intent = self._extract_intent(intent_design)
        print(f"📋 [Muse] 추출된 의도: {intent[:100]}...")
        
        # 🛡️ 최소 보호 (4개만 - 진화 자유 보장)
        PROTECTED_FILES = frozenset([
            "main.py", "api/keys.py", "api/github.py", ".ainprotect",
            "docs/hardware-catalog.md"  # 하드웨어 카탈로그 (참고용)
        ])
        
        updates = []
        # FILE: 또는 [FILE] 또는 **FILE:** 또는 # FILE: 등 유연하게 파싱
        # 대소문자 무시, 앞에 기호나 공백이 있을 수 있음
        file_sections = re.split(r'(?i)(?:\n|^)[#\*\[ ]*FILE[ :\]]*\s*', code_output)
        if len(file_sections) > 1:
            file_sections = file_sections[1:]
        else:
            file_sections = []
        
        if not file_sections:
            # FILE: 마커가 없으면 대체 패턴 시도 (파일명: 형식)
            print("⚠️ [Muse] FILE: 마커 없음, 대체 패턴 시도...")
            # 1. ```python:filename.py 또는 '''python:filename.py 형식
            alt_pattern = re.findall(r'(?:```|\'\'\')(?:python|py)?:?\s*(\S+\.py)\s*\n(.*?)(?:```|\'\'\')', code_output, re.DOTALL)
            for filename, code in alt_pattern:
                filename = filename.strip().lstrip('./')
                if filename not in PROTECTED_FILES:
                    updates.append({"filename": filename, "code": code.strip()})
                    print(f"📦 [Muse] 대체 파싱 1 성공: {filename}")
            
            # 2. 파일명만 있고 코드블록이 바로 뒤따르는 경우
            if not updates:
                alt_pattern2 = re.findall(r'(?:\n|^)([a-zA-Z0-9_/]+\.py)\s*\n\s*(?:```|\'\'\')(?:python|py)?\n(.*?)(?:```|\'\'\')', code_output, re.DOTALL)
                for filename, code in alt_pattern2:
                    filename = filename.strip().lstrip('./')
                    if filename not in PROTECTED_FILES:
                        updates.append({"filename": filename, "code": code.strip()})
                        print(f"📦 [Muse] 대체 파싱 2 성공: {filename}")
        
        for section in file_sections:
            lines = section.split('\n')
            if not lines: continue
            
            # 파일명 추출 및 정규화
            raw_filename = lines[0].strip()
            # 마크다운 포맷팅 제거: **, `, 공백 등
            filename = raw_filename.replace('*', '').replace('`', '').replace('"', '').replace("'", '').strip()
            # 경로 정규화: ./path -> path
            filename = filename.lstrip('./')
            
            # 파일명이 유효한지 확인
            if not filename or not ('.' in filename):
                print(f"⚠️ [Muse] 유효하지 않은 파일명: '{raw_filename}'")
                continue
            
            # 🛡️ 보호된 파일은 파싱 단계에서 건너뜀
            if filename in PROTECTED_FILES or os.path.basename(filename) in ["main.py", ".ainprotect"]:
                print(f"🛡️ [Muse] 보호된 파일 건너뜀: {filename}")
                continue
            
            # 마크다운 코드 블록 추출 (백틱 ``` 또는 작은따옴표 ''' 모두 허용)
            code_match = re.search(r'(?:```|\'\'\')(?:\w+)?\s*(.*?)\s*(?:```|\'\'\')', section, re.DOTALL)
            if code_match:
                code_content = code_match.group(1).strip()
                if filename and code_content and len(code_content) > 10:
                    updates.append({"filename": filename, "code": code_content})
                    print(f"📦 [Muse] 파싱 성공: {filename} ({len(code_content)} bytes)")
                else:
                    print(f"⚠️ [Muse] 코드가 너무 짧음: {filename} ({len(code_content) if code_content else 0} bytes)")
            else:
                print(f"⚠️ [Muse] 코드 블록 없음: {filename}")
        
        if not updates:
            # 디버깅용: 백틱을 그대로 유지하여 실제 응답 형식 확인 가능
            sample = code_output[:500]
            print(f"⚠️ [Muse] 파싱된 updates 없음.")
            print(f"📋 [Muse] Coder 응답 전체 길이: {len(code_output)} chars")
            print(f"📋 [Muse] FILE: 마커 포함 여부: {'FILE:' in code_output or 'FILE ' in code_output}")
            print(f"📋 [Muse] 코드블록 포함 여부: {'```' in code_output}")
            
            # 마지막 시도: 전체 응답에서 첫 번째 코드 블록만이라도 추출
            last_resort = re.search(r'```(?:python|py)?\s*(.*?)```', code_output, re.DOTALL)
            if last_resort and len(last_resort.group(1).strip()) > 100:
                fallback_code = last_resort.group(1).strip()
                # Dreamer의 의도에서 파일명 추론 (개선된 정규식)
                file_hint = re.search(r'([\w/]+\.py)', intent)
                if file_hint:
                    fallback_filename = file_hint.group(1)
                    print(f"🔄 [Muse] 마지막 시도: {fallback_filename}로 코드 추출 ({len(fallback_code)} bytes)")
                    updates.append({"filename": fallback_filename, "code": fallback_code})
                    return {"intent": intent, "updates": updates}
                else:
                    # 하드코딩 대신 명확한 실패
                    print("⚠️ [Muse] 파일명 추론 실패, 진화 스킵")
                    return {"intent": intent, "updates": [], "error": "파일명 추론 실패"}
            
            # 디버깅용 샘플 (백틱 유지)
            sample_display = sample.replace('`', '`')  # 그대로 유지
            return {
                "intent": intent, 
                "updates": [], 
                "error": f"Coder가 규격에 맞는 코드를 생성하지 못했습니다.\n\n[응답 샘플 (처음 500자)]\n{sample_display}"
            }

        return {"intent": intent, "updates": updates}
