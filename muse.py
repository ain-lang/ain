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

    def imagine(self, system_context, user_query=None, evolution_history=None, error_context=None):
        """[Muse] Dreamer와 Coder의 협업을 통해 진화를 상상함"""
        
        # 1. 컨텍스트 압축
        compressed_code = self._compress_context(system_context)
        
        # 2. [Dreamer - Gemini 3 Pro] 전략 및 의도 수립
        print(f"🧠 Dreamer가 진화 방향을 구상 중...")
        
        # Lessons Learned 요약 (별도 호출 없이 컨텍스트에서 추출 유도)
        dream_prompt = f"""
{self.prime_directive}

[현재 시스템 상태 및 코드]
{compressed_code}

[미션]
1. 위 코드와 'Lessons Learned'를 분석하여 현재 작업(Step 3: Bridge Integration)의 성숙도를 평가하라.
2. 다음 진화 단계를 위해 무엇을 '수정'하거나 '추가'할지 구체적이고 기술적인 '의도(Intent)'를 설계하라. 
   - **의도 작성법**: 현재 어떤 컴포넌트(파일명 언급)가 확보되었는지, 하지만 무엇(유기적 결합, 실전 파이프라인 등)이 부족한지, 그래서 이번에 어떤 핵심 엔진이나 로직을 구현하여 어떤 목표(Step 3 완성 등)를 달성할 것인지 아주 구체적이고 전문적으로 서술하라.
   - 어조는 숙련된 시스템 아키텍트의 시점이어야 한다.
3. 코드를 직접 짜지 말고, 논리적 설계와 상세한 구현 가이드라인, 그리고 변경해야 할 파일 목록만 제시하라.

[출력 규칙]
- 반드시 첫 줄에 `SYSTEM_INTENT: (여기에 위의 규칙에 따른 상세한 진화 의도를 작성)`을 작성하라.
"""
        if error_context:
            dream_prompt += f"\n\n🚨 [에러 복구 모드]\n{error_context}"
        if user_query:
            dream_prompt += f"\n\n💡 [주인님의 명령]\n{user_query}"

        dream_result = self.dreamer_client.chat([
            {"role": "system", "content": "You are the Dreamer (Architect) of AIN. Design the next evolution step. Focus on logic and architecture."},
            {"role": "user", "content": dream_prompt}
        ], timeout=120)  # 2분 타임아웃

        if not dream_result["success"]:
            return {"intent": "Dreaming failed", "updates": [], "error": dream_result["error"]}

        intent_design = dream_result["content"]
        print(f"--- Dreamer's Intent ---\n{intent_design[:300]}...")

        # 3. [Coder - Claude 4.5 Opus] 실제 코드 구현
        print(f"💻 Coder (Claude 4.5 Opus)가 코드를 작성 중...")
        coder_prompt = f"""
너는 AIN의 최고 선임 개발자(Coder)다. 아래 설계도(Dreamer's Intent)를 바탕으로 실제 작동하는 코드를 작성하라.

[Dreamer's Intent]
{intent_design}

[현재 시스템 컨텍스트 요약]
{compressed_code}

[코딩 규칙 - 매우 중요!]
1. **반드시** 아래 형식을 정확히 따라라. 다른 설명은 생략하고 코드에 집중하라.

FILE: 파일명.py
```python
# 여기에 전체 코드 작성 (일부 수정이 아닌 파일 전체 내용을 작성할 것)
```

2. FILE: 마커는 반드시 줄의 맨 앞에 작성하라 (공백이나 기호 없이).
3. 코드는 반드시 ``` 코드블록 안에 작성하라.
4. 한 번에 1-2개 파일만 수정하라 (작은 단위로 진화).
5. 아키텍처 가이드를 준수하라 (database/ 폴더 활용, snake_case 사용).
6. 기존 코드를 유지하면서 필요한 부분만 교체하거나 추가하라.
7. **특히 nexus.py를 수정할 때는 class Nexus와 기존 메서드들을 반드시 포함하라.**

[출력 예시 - 이대로만 출력하라]
FILE: example_file.py
```python
import os
# ... full code ...
```
"""
        coder_result = self.coder_client.chat([
            {"role": "system", "content": "You are the Coder (Senior Engineer) of AIN. Implement the design perfectly with clean, production-grade code."},
            {"role": "user", "content": coder_prompt}
        ], max_tokens=8192, timeout=180)  # 3분 타임아웃 (Opus는 느림)

        if not coder_result["success"]:
            print(f"❌ [Muse] Coder 실패: {coder_result.get('error', 'Unknown')}")
            return {"intent": "Coding failed", "updates": [], "error": coder_result["error"]}

        code_output = coder_result["content"]
        print(f"📝 [Muse] Coder 응답 길이: {len(code_output)} chars")
        
        # 4. 결과 파싱
        # 의도는 Dreamer의 내용에서 SYSTEM_INTENT 태그를 우선적으로 찾음
        # 여러 줄에 걸친 의도도 캡처할 수 있도록 보강
        intent_match = re.search(r'SYSTEM_INTENT:\s*(.*?)(?=\n\n|\n\[|\n#|$)', intent_design, re.DOTALL)
        if intent_match:
            intent = intent_match.group(1).strip().replace('\n', ' ')
        else:
            # 못 찾으면 기존 방식대로 헤더 제외 첫 문장 사용
            intent_lines = [line.strip() for line in intent_design.split('\n') if line.strip() and not line.strip().startswith('#')]
            intent = intent_lines[0][:500] if intent_lines else "System Evolution"
        
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
            sample = code_output[:200].replace('`', "'")
            print(f"⚠️ [Muse] 파싱된 updates 없음. Coder 응답 샘플: {sample}...")
            return {
                "intent": intent, 
                "updates": [], 
                "error": f"Coder가 규격에 맞는 코드를 생성하지 못했습니다.\n\n[응답 샘플]\n{sample}..."
            }

        return {"intent": intent, "updates": updates}
