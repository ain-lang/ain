# AIN 개발 메모 (우리를 위한 문서)

> AIN이 자기 코드를 수정할 때 망가뜨리지 않도록 기억하기 위한 참고 문서

---

## 핵심 철학: "Solve the Root, Not Just the Symptom"

> **증상이 아닌 근본을 해결하라**

### 원칙
1. **일시적 해결 + 근본 해결 병행**: Quick Fix로 당장 막되, 근본 해결도 반드시 진행
2. **시스템적 진화**: 모든 수동 개입은 AIN의 자율 능력을 향상시켜야 함
3. **하드코딩 금지**: fallback 기본값 같은 하드코딩은 나중에 반드시 문제됨
4. **수정 후 즉시 푸시**: 코드 수정 완료 시 반드시 `git push origin main`으로 배포

### 2단계 해결 패턴
```
[문제 발생]
    ↓
[1단계: 일시적 해결] → 당장 시스템 안정화
    ↓
[2단계: 근본 해결] → 재발 방지, 아키텍처 개선
    ↓
[문서화] → claude.md에 기록하여 잊지 않기
```

### 적용 사례
```
❌ 나쁜 예: fallback_filename = "nexus.py"  # 하드코딩
✅ 좋은 예: 파일명 추론 실패 시 명확하게 에러 반환

❌ 나쁜 예: except: pass  # 에러 무시
✅ 좋은 예: 에러 로깅 후 적절한 처리

❌ 나쁜 예: 200줄 파일에 기능 추가
✅ 좋은 예: 새 모듈로 분리 후 import
```

---

## 개선 보고서 형식

> 문제 분석 후 사용자에게 보고할 때 이 형식을 따른다

### 템플릿
```markdown
## 분석 결과 - N가지 개선 필요

### 1. 🔴 [문제명] (심각)
```
[에러 로그 또는 증상]
```
- **원인**: 근본 원인 설명
- **영향**: 시스템에 미치는 영향
- **개선**: 제안하는 해결책

### 2. 🟠 [문제명] (중간)
...

### 3. 🟡 [문제명] (낮음)
...

---
어떤 것부터 수정할까요?
1. **전부** - N개 모두 수정
2. **[가장 심각한 것]만**
3. **[중간 것]만**
4. **[가장 간단한 것]만**
```

### 심각도 기준
| 이모지 | 심각도 | 기준 |
|--------|--------|------|
| 🔴 | 심각 | 배포/서비스 중단, 데이터 손실 위험 |
| 🟠 | 중간 | 기능 오작동, 반복 에러 |
| 🟡 | 낮음 | 개선 가능, 당장 문제 없음 |

### 사용 시점
- 텔레그램 로그 분석 후
- 에러 반복 패턴 발견 시
- 시스템 상태 점검 후

---

## 현재 상태 (2026-01-17)

- **버전**: 0.3.0
- **단계**: Phase 3, Step 7 (Meta-Cognition) 🔥
- **완료**: Step 1-6 (Brain, Logic, Bridge, Vector Memory, Inner Monologue, Intentionality)
- **GoalManagerMixin**: AINCore에 연결 완료 ✅

---

## 해결된 문제점 ✅

### 1. ✅ 진화 "완료" but 변경사항 없음 (파일 파싱)
**증상**: Dreamer가 지정한 파일과 다른 파일에 적용됨
**근본 해결**: `muse.py` fallback 하이브리드 방식 적용
- 정규식 개선: 의도에서 첫 `.py` 파일 추출
- 추론 실패 시 `nexus.py` 하드코딩 대신 에러 반환

### 2. ✅ 독백 작동 안 됨
**근본 해결**: `muse.py`에 `_ask_dreamer()` 메서드 추가
- 타이밍: 진화 후 30분에 독백 실행

### 3. ✅ "변경사항 없음" 무한 반복
**증상**: Dreamer가 이미 완료된 Step 작업 계속 제안
**근본 해결**:
- `muse.py` Dreamer 프롬프트에 "구현 여부 직접 확인" 규칙 추가
- `muse.py`에 Step 완료 판단 기준 명시
- `evolution.py`에 연속 3회 변경없음 시 "다음 Step 탐색" 강제 지시

### 4. ✅ 진화 시도 결과 안 보임
**증상**: 독백만 오고 진화 결과가 텔레그램에 안 옴
**원인**: `introspect.py`에서 `updates` 비면 주기적 진화 시 조용히 종료
**근본 해결**: 모든 진화 시도 결과를 텔레그램에 알림
- `no_evolution=True` → "😴 Step 완료" 메시지
- `updates=[]` → "💭 진화 탐색 (적용할 변경사항 없음)" 메시지

### 5. ✅ 로드맵 완료 체크 안 함
**증상**: Step 완료되어도 다음 Step으로 자동 이동 안 함
**근본 해결**: `engine/roadmap_checker.py` 생성
- 진화 성공 후 현재 Step 완료 조건 자동 체크
- 완료 시 `fact_core.json` 자동 업데이트
- 다음 Step으로 `current_focus` 자동 이동
- 텔레그램에 "🗺️ 로드맵 업데이트" 알림

### 6. ✅ Coder가 기존 코드와 동일한 코드 생성
**증상**: "진화 완료"라고 하지만 실제 변경사항 없음 (nothing to commit)
**원인**: Coder가 기존 파일과 동일한 코드를 생성해도 검출 로직이 없었음
**근본 해결**: `muse.py:348-365` 변경사항 검증 로직 추가
- 기존 파일 내용과 Coder 출력을 비교
- 공백/개행 정규화 후 비교하여 동일하면 재시도
- 에러 메시지: "생성된 코드가 기존 파일과 동일합니다! Dreamer의 의도대로 반드시 새로운 내용을 추가하라."
- 최대 5회 재시도 (기존 재시도 로직에 통합)

### 7. ✅ Dreamer가 이미 구현된 기능을 다시 제안
**증상**: "이미 개발한 것 다시 개발" 반복
**원인**: Dreamer 프롬프트의 Step 완료 기준이 하드코딩되어 실제 상태와 불일치
**근본 해결**: 동적 완료 상태 전달 시스템
- `roadmap_checker.py`: `get_current_status_for_dreamer()` 메서드 추가
- `muse.py`: 하드코딩된 Step 기준 제거, 동적 결과 `{step_status}` 전달
- Dreamer에게 "❌ 표시된 항목만 구현하라" 명시
- 완료 조건은 `roadmap_checker.py:STEP_COMPLETION_CRITERIA`에서 **한 곳에서만** 관리

### 8. ✅ 진화 스킵 시 로드맵 업데이트 안 됨
**증상**: Step 완료 조건 충족 → 진화 스킵 → fact_core.json 업데이트 안 됨 → 무한 반복
**원인**: `introspect.py`에서 `no_evolution=True`일 때 `roadmap_checker.check_and_advance()` 호출 안 함
**근본 해결**: `introspect.py:55-67` 수정
- 진화 스킵 시에도 `roadmap_checker.check_and_advance()` 호출
- Step 완료 시 `fact_core.json` 자동 업데이트 및 텔레그램 알림

### 9. ✅ Step 완료 시 영속성 문제 (fact_core.json 업데이트 안 됨)
**증상**: Step 6 완료 조건 모두 충족 → "Step 완료" 반복 → Step 7로 넘어가지 않음
**원인**: `roadmap_checker.check_and_advance()`가 `fact_core.json` 업데이트해도 Git에 커밋/푸시 안 됨
- Railway 재배포 시 원래 상태로 복원
**근본 해결**: `roadmap_checker.py`에 `_commit_and_push_roadmap()` 메서드 추가
- Step 완료 후 `fact_core.json` 변경사항 자동 Git 커밋/푸시
- 영속성 보장으로 다음 배포에서도 Step 진행 상태 유지

### 10. ✅ consciousness.py가 벡터 메모리에 접근 못함 (2026-01-17)
**증상**: 독백에서 "텅 빈 기억", "참조할 기억 없이" 반복
**원인**: `Nexus` 클래스가 `_vector_memory` (private)만 선언하고 public property 미노출
- `consciousness.py`는 `self.nexus.vector_memory` 접근 시도
- `hasattr(self.nexus, 'vector_memory')` → 항상 False
- 벡터 메모리 저장/검색 전혀 실행 안 됨
**근본 해결**: `nexus/__init__.py:61-64` property 추가
```python
@property
def vector_memory(self):
    return self._vector_memory
```

### 11. ✅ Coder diff 형식 감지 기준 너무 관대 (2026-01-17)
**증상**: "Git 충돌 마커 또는 diff 형식(+/-)이 감지됨" 에러
**원인**: `code_sanitizer.py`에서 diff 감지 기준이 `> 3`으로 설정
- 1-3줄의 diff 패턴은 감지 안 되고 통과
**근본 해결**: `code_sanitizer.py:133, 190` 기준 변경
- `> 3` → `>= 1`로 변경
- 단 1줄이라도 diff 형식이면 감지 및 자동 변환 시도

### 12. ✅ Coder가 diff 형식 계속 사용 (2026-01-17, 추가 강화)
**증상**: 감지 기준 강화해도 "diff: 15줄", "diff: 7줄" 에러 반복
**원인**: Coder 시스템 프롬프트에 구체적인 예시가 없어서 LLM이 diff 형식 이해 못함
**근본 해결**: `muse.py` 3곳 강화
1. **coder_system** (317-350줄): 잘못된 예시 + 올바른 예시 추가
```
⛔️⛔️⛔️ ABSOLUTELY FORBIDDEN - DIFF FORMAT ⛔️⛔️⛔️
❌ WRONG: + import new_module / - import old_module
✅ CORRECT: import new_module (앞에 +/- 없이)
```
2. **coder_prompt** (265-272줄): 한국어로 diff 금지 명시 + 예시 추가
```
⛔ DIFF 형식 절대 금지: 줄 시작에 `+ `나 `- `(공백 포함)를 쓰면 자동 거부됨!
❌ 금지 예: `+ import foo`
✅ 올바른 예: `import foo`
```
3. **retry_hint** (315-324줄): diff 에러 시 추가 힌트 자동 삽입
```
⛔️ DIFF 형식을 사용했기 때문에 거부되었다!
줄 시작에 '+ ' 또는 '- '를 절대 쓰지 마라.
```

### 13. ✅ Python 구문 오류 반복 - 대형 파일 보호 (2026-01-17)
**증상**: `unterminated string literal` 에러 427회 반복
**원인**: Coder가 200줄+ 파일 수정 시 토큰 한계로 코드 잘림
**근본 해결**: `utils/file_size_guard.py` 모듈 추가
- `ALWAYS_PROTECTED`: main.py, muse.py, overseer.py 등 (크기 무관 보호)
- `DEFAULT_THRESHOLD = 150`: 권장 최대 줄 수
- `HARD_LIMIT = 200`: 절대 수정 금지 줄 수
- `validate_coder_output()`: Coder 출력에서 대형 파일 수정 자동 거부
- `muse.py:542-556`: 파싱 단계에서 대형 파일 보호 로직 통합
```python
# muse.py 마지막 부분
valid_updates, rejected = validate_coder_output(updates)
if rejected:
    return {"error": f"대형 파일 보호에 의해 거부됨.\n{rejection_msg}"}
```

### 14. ✅ 충돌 마커 오감지 - 문서 데코레이션 제거됨 (2026-01-17)
**증상**: "Git 충돌 마커" 에러가 문서 데코레이션 `========================================`에서 발생
**원인**: `code_sanitizer.py`에서 충돌 마커 감지가 substring 매칭
- `'=======' in code_output` → 40개 `=` 데코레이션에서도 True
- Step 2 제거 로직도 "7개 이상 =만 있는 줄" 모두 제거
**근본 해결**: `code_sanitizer.py:97, 124-129` 수정
- Step 2: `stripped == '======='` (정확히 7개만 제거)
- Step 3: 독립 줄로만 감지 (substring 매칭 제거)
```python
# Step 2: 정확히 7개 = 만 제거
elif stripped == '=======':  # 기존: '=======' in stripped

# Step 3: 독립 줄로만 감지
has_separator = any(line.strip() == '=======' for line in code_output.split('\n'))
```

### 15. ✅ Dreamer 파일 크기 hallucination (2026-01-17)
**증상**: "meta_cognition.py 369줄 대형 파일"이라고 하지만 실제는 84줄
**원인**: Dreamer에게 실제 파일 크기 정보가 전달되지 않아 hallucination 발생
**근본 해결**: `muse/utils.py`에 `get_file_sizes_info()` 함수 추가
- 모든 주요 디렉토리의 `.py` 파일 크기를 실제로 측정
- 150줄 기준 ✅소형/⚠️대형 표시
- `muse/dreamer.py`에서 Dreamer 프롬프트에 실제 파일 크기 정보 전달
```python
# muse/utils.py
def get_file_sizes_info(directories: List[str] = None) -> str:
    # 실제 파일 크기 측정하여 Dreamer에게 전달

# muse/dreamer.py
file_sizes_info = get_file_sizes_info()
# 프롬프트에 {file_sizes_info} 포함
```

---

## 미해결 문제점

### 1. ✅ Python 구문 오류 반복 (해결됨 - 2026-01-17)
**증상**: `unterminated string literal` 에러 427회 반복
**원인**: 대형 파일 수정 시 토큰 한계로 코드 잘림
**근본 해결**: `utils/file_size_guard.py` 모듈 추가
- 150줄 권장, 200줄 절대 한계
- `ALWAYS_PROTECTED`: main.py, muse.py, overseer.py 등
- `validate_coder_output()`: Coder 출력에서 대형 파일 수정 자동 거부
- `muse.py:542-556`: 파싱 단계에서 대형 파일 보호 로직 통합
→ 해결된 문제점 #13 참조

### 2. ✅ 독백이 "빈 데이터" 반복 (해결됨 - 2가지 원인)
**증상**: "텅 빈 기억 속에서", "참조할 기억 없이" 동일한 내용 반복
**원인 A**: Railway에서 LanceDB 데이터가 영속되지 않음
- `database/lance_bridge.py:39`의 `DEFAULT_DB_PATH = "/data/lancedb"`
- Railway 컨테이너 재배포 시 `/data/` 폴더 초기화 → 벡터 메모리 삭제
**해결 A (2026-01-17)**:
- Railway CLI로 볼륨 추가: `railway volume add -m /data`
- 볼륨명: `ain-core-volume`
- 마운트 경로: `/data` (50GB)
- 재배포 후에도 벡터 메모리 영속
**원인 B**: Nexus가 vector_memory public property 미노출
- `consciousness.py`가 `self.nexus.vector_memory` 접근 불가
**해결 B (2026-01-17)**: → 해결된 문제점 #10 참조

---

## 중요한 타이밍 규칙

```
[진화 ↔ 독백 사이클] ✅ 구현 완료

     ┌─────────────────────────────────────┐
     │              진화 (1시간)            │
     │  └─ 독백에서 관련 통찰 벡터 검색 ✅   │
     └────────────────┬────────────────────┘
                      │ 30분
                      ▼
     ┌─────────────────────────────────────┐
     │         내부 독백 (30분 후)          │
     │  └─ 통찰을 벡터 메모리에 저장        │
     └────────────────┬────────────────────┘
                      │ 30분
                      ▼
                   (반복)

독백 → 진화 연결:
- 진화 전 벡터 검색으로 관련 독백 찾기
- Dreamer에게 "[💭 관련 내부 독백]" 컨텍스트 전달
- 자기 성찰이 진화 방향에 영향
```

---

## 보호해야 할 것들

### 절대 수정 금지
- `main.py` - 심장 (Supervisor)
- `api/keys.py` - 인증 정보
- `overseer.py` - 검증 엔진

### AIN이 자주 망가뜨리는 것들
- 200줄 이상 파일 직접 수정 → 새 모듈로 분리해야 함
- `engine/__init__.py` 믹스인 상속 순서
- `consciousness.py`의 외부 메서드 호출

---

## 빠른 복구 가이드

### 진화 실패 시
```bash
git reset --hard HEAD~1  # 마지막 커밋 롤백
```

### 독백 안 될 때
1. `muse.py`에 `_ask_dreamer()` 있는지 확인
2. `engine/consciousness.py:241` 호출부 확인

### 진화는 되는데 변경 없을 때
1. Dreamer 응답에서 대상 파일 확인
2. `muse.py` fallback 로직 확인 (기본값이 nexus.py인지)

---

## Railway CLI 가이드

### 설치 및 로그인
```bash
# 설치 (macOS)
brew install railway

# 로그인
railway login

# 프로젝트 연결 (ain 디렉토리에서)
railway link
```

### 자주 쓰는 명령어
```bash
# 로그 실시간 확인
railway logs -f

# 환경변수 확인
railway variables

# 환경변수 설정
railway variables set KEY=VALUE

# 배포 상태 확인
railway status

# 수동 배포
railway up

# 서비스 재시작
railway service restart
```

### 볼륨 관련 (벡터 메모리 영속성)
```bash
# 볼륨 목록 확인
railway volume list

# 볼륨 추가 (대시보드에서 권장)
# Settings → Volumes → Add Volume
# Mount Path: /data
# Size: 1GB
```

### 디버깅
```bash
# 컨테이너 쉘 접속
railway shell

# 특정 서비스 로그
railway logs --service <service-name>

# 최근 N줄 로그
railway logs -n 100
```

### Railway 대시보드
- URL: https://railway.app/dashboard
- 프로젝트: ain-lang/ain

---

## Claude Code 권한 설정

### 자동 승인 모드
`.claude/settings.local.json`에서 `defaultMode: "acceptEdits"` 설정:
- 파일 편집: 자동 승인 (allow 확인 없음)
- Bash 명령: `allow` 목록에 있는 명령만 자동 실행

### 현재 허용된 Bash 명령
```
git pull, git add, git commit, git push, git checkout, git fetch
python, python3
ls
railway (모든 하위 명령)
```

### 더 강력한 옵션 (주의)
```bash
# 한 세션만 모든 권한 스킵
claude --dangerously-skip-permissions

# 완전 자동 모드 (settings.json)
"defaultMode": "bypassPermissions"
```

---

## 모델별 프롬프트 튜닝 가이드

### Coder (Claude 4.5 Opus) - 반복 실수 패턴

| 실수 패턴 | 해결 프롬프트 |
|-----------|--------------|
| **diff 형식 사용** | ⛔️ 구체적 예시 필수: "❌ `+ import foo` → ✅ `import foo`" |
| **코드 생략** | "# ... existing" 금지 명시 + 전체 코드 출력 요구 |
| **기존 코드 복사** | "변경사항 없으면 NO_EVOLUTION_NEEDED 출력" 규칙 |
| **대형 파일 수정** | "200줄 이상 파일은 새 모듈로 분리" 강제 |

### 프롬프트 구조 (효과적인 순서)
```
1. 시스템 프롬프트: 역할 + 금지 사항 (예시 포함)
2. 유저 프롬프트:
   - [작성 규칙] - 위반 시 에러 명시
   - [설계도] - Dreamer 의도
   - [참고 코드] - 기존 파일 내용
   - [과거 실패] - error_memory 힌트
   - [재시도 힌트] - 이전 에러 원인
```

### Dreamer (Gemini 3 Pro) - 반복 실수 패턴

| 실수 패턴 | 해결 프롬프트 |
|-----------|--------------|
| **이미 구현된 기능 제안** | "코드에 해당 클래스/함수 있는지 직접 확인" 강제 |
| **환각 (없는 파일 언급)** | "코드 스냅샷에 없으면 없는 것" 명시 |
| **대형 파일 수정 제안** | "200줄 이상 파일은 새 모듈로 분리" 규칙 |

### 에러 기억 시스템 활용
- `error_memory.json`에 패턴별 에러 횟수 기록
- 3회 이상 반복 시 긴급 경고 자동 삽입
- diff 관련 에러는 특별 강화 메시지 추가

---

## 다음 할 일

1. [x] `muse.py`에 `_ask_dreamer()` 메서드 추가 ✅
2. [x] 진화/독백 30분 번갈아 실행 구현 ✅
3. [x] 파일 파싱 fallback 로직 수정 (하이브리드) ✅
4. [x] "변경사항 없음" 반복 시 다음 Step 탐색 ✅
5. [x] 진화 후 로드맵 자동 완료 체크 ✅
6. [x] error_memory 고도화 - 임계값 기반 긴급 경고 ✅
7. [x] Sanitizer diff 변환 로직 강화 ✅
8. [x] 대형 파일 제외 로직을 동적으로 변경 (200줄 기준) ✅
9. [ ] `code_sanitizer.py` 따옴표 치유 로직 개선

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────┐
│                   main.py                       │
│              (불멸의 심장 Supervisor)            │
│         ain_engine.py 프로세스 감시/복구         │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              engine/__init__.py                 │
│   AINCore = _AINCore + 6개 Mixin 상속           │
│   (Sync, Evolution, Handlers, Introspect,       │
│    Consciousness, GoalManager)                  │
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  Muse   │  │  Nexus   │  │ Overseer │
   │ Dreamer │  │  Vector  │  │ Validate │
   │ + Coder │  │  Memory  │  │ + Apply  │
   └─────────┘  └──────────┘  └──────────┘
```

---

*마지막 업데이트: 2026-01-17*
