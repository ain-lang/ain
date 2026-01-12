import re
import os
from api import OpenRouterClient

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
1. 위 코드를 분석하여 **현재 로드맵 단계**의 성숙도를 평가하라.
2. 다음 진화 단계를 위해 무엇을 '수정'하거나 '추가'할지 구체적이고 기술적인 '의도(Intent)'를 설계하라. 
   - **의도 작성법**: 현재 어떤 컴포넌트(파일명 언급)가 확보되었는지, 하지만 무엇이 부족한지, 그래서 이번에 어떤 핵심 엔진이나 로직을 구현할 것인지 구체적으로 서술하라.
3. 코드를 직접 짜지 말고, 논리적 설계와 상세한 구현 가이드라인, 그리고 변경해야 할 파일 목록만 제시하라.

[🚨 중복 방지 규칙]
- 이미 구현된 기능을 다시 제안하지 마라.
- nexus/*.py, engine/*.py 등 이미 모듈화된 구조를 활용하라.

[🏗️ 모듈 설계 원칙]
- 파일당 100줄 이하 권장 (최대 150줄)
- 새 기능은 별도 파일로 생성 (utils/*.py 등)

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
        target_files = re.findall(r'([a-zA-Z0-9_\-/]+\.py)', intent_design)
        target_files_content = ""
        for tf in set(target_files):
            tf_path = tf.lstrip('./')
            if os.path.exists(tf_path) and os.path.isfile(tf_path):
                try:
                    with open(tf_path, 'r', encoding='utf-8') as f:
                        target_files_content += f"\n\n--- ORIGINAL FILE: {tf_path} (Full Content) ---\n{f.read()}\n"
                except: pass

        # 3. [Coder - Claude 4.5 Opus] 실제 코드 구현
        print(f"💻 Coder (Claude 4.5 Opus)가 새로운 모듈을 생성 중...")
        coder_prompt = f"""
너는 AIN의 '코드 생성기(Code Generator)'다. 
**중요: 너는 기존 파일을 수정하는 것이 아니라, 완벽한 전체 코드를 처음부터 끝까지 새로 '작성'하는 역할이다.**

[작성 규칙 - 위반 시 에러 발생]
1. **전체 코드 출력**: 파일의 일부분이나 수정된 내용(diff)만 출력하는 것은 절대 금지된다. 반드시 `import`부터 끝까지 전체 코드를 작성하라.
2. **마커 준수**: 파일 하나당 하나의 `FILE: 파일명.py` 마커와 하나의 코드 블록(```python ... ```)만 사용하라.
3. **금지 기호**: `+`, `-`, `<<<<<<<`, `=======`, `>>>>>>>` 등 diff나 충돌 마커는 절대 포함하지 마라.
4. **생략 금지**: `# ...` 이나 `(기존 코드 생략)` 같은 표현은 절대 사용하지 마라.

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
            
            # 🔧 전처리
            if "'''" in code_output:
                code_output = code_output.replace("'''", "```")
                print("🔄 [Muse] '''를 ```로 자동 치환함")
            
            # 🔧 Git 충돌 마커 자동 제거 (후처리)
            conflict_markers = ['<<<<<<<', '=======', '>>>>>>>', 'HEAD', '<<<<<<< HEAD']
            lines = code_output.split('\n')
            cleaned_lines = []
            in_conflict_block = False
            for line in lines:
                # 충돌 시작/끝 마커 건너뛰기
                if line.strip().startswith('<<<<<<<') or line.strip().startswith('>>>>>>>'):
                    in_conflict_block = not in_conflict_block if line.strip().startswith('<<<<<<<') else False
                    print(f"🔧 [Muse] 충돌 마커 제거: {line[:30]}...")
                    continue
                # ======= 구분선 건너뛰기
                if line.strip() == '=======' or line.strip().startswith('======='):
                    print(f"🔧 [Muse] 충돌 구분선 제거")
                    continue
                cleaned_lines.append(line)
            
            if len(cleaned_lines) != len(lines):
                code_output = '\n'.join(cleaned_lines)
                print(f"🔧 [Muse] 충돌 마커 제거 완료: {len(lines)} -> {len(cleaned_lines)} 줄")
            
            # 🚨 Git 충돌 마커 감지 (제거 후에도 남아있는지 확인)
            has_conflict = any(marker in code_output for marker in ['<<<<<<<', '>>>>>>>'])
            
            # 🚨 Diff 형식 감지 (+ 또는 -로 시작하는 줄, @@ 마커)
            current_lines = code_output.split('\n')
            diff_indicators = [l for l in current_lines if l.strip().startswith('+ ') or l.strip().startswith('- ')]
            is_diff_format = len(diff_indicators) > 3 or '@@ ' in code_output
            
            # 🚨 내용 생략 감지 (더 구체적인 패턴만)
            omission_patterns = [
                r'#\s*\.\.\.\s*existing',      # # ... existing
                r'#\s*\.\.\.\s*rest',          # # ... rest of
                r'#\s*\.\.\.\s*same',          # # ... same as
                r'#\s*\.\.\.\s*unchanged',     # # ... unchanged
                r'#\s*keep\s+existing',        # # keep existing
                r'#\s*unchanged\s+from',       # # unchanged from
            ]
            has_omission = any(re.search(p, code_output, re.I) for p in omission_patterns)
            
            if has_conflict or is_diff_format:
                last_error = f"Git 충돌 마커 또는 diff 형식(+/-)이 감지됨. " \
                             f"diff: {len(diff_indicators)}줄, conflict: {has_conflict}. " \
                             "절대 diff 형식을 사용하지 말고 전체 파일을 새로 작성하라."
                print(f"🚨 [Muse] Conflict/Diff 감지! 재시도...")
                continue
            
            if has_omission:
                last_error = "코드 생략 패턴(# ... existing 등)이 감지됨. " \
                             "생략하지 말고 전체 코드를 작성하라."
                print(f"🚨 [Muse] Omission 감지! 재시도...")
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
                    continue
            
            # 모든 검사 통과
            break
        else:
            # 모든 재시도 실패
            print(f"❌ [Muse] Coder {MAX_CODER_RETRIES}회 시도 모두 실패")
            return {"intent": "Coding failed after retries", "updates": [], "error": last_error}
        
        if not code_output:
            return {"intent": "Coding failed", "updates": [], "error": "No code output"}
        
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
                # Dreamer의 의도에서 파일명 추론
                file_hint = re.search(r'(?:수정|변경|업데이트|Update|Modify).*?[`\'"]([\w/]+\.py)[`\'"]', intent, re.IGNORECASE)
                if file_hint:
                    fallback_filename = file_hint.group(1)
                else:
                    fallback_filename = "nexus.py"  # 기본값
                
                print(f"🔄 [Muse] 마지막 시도: {fallback_filename}로 코드 추출 ({len(fallback_code)} bytes)")
                updates.append({"filename": fallback_filename, "code": fallback_code})
                return {"intent": intent, "updates": updates}
            
            # 디버깅용 샘플 (백틱 유지)
            sample_display = sample.replace('`', '`')  # 그대로 유지
            return {
                "intent": intent, 
                "updates": [], 
                "error": f"Coder가 규격에 맞는 코드를 생성하지 못했습니다.\n\n[응답 샘플 (처음 500자)]\n{sample_display}"
            }

        return {"intent": intent, "updates": updates}
