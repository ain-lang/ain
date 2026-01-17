# AIN 개발 메모 (우리를 위한 문서)

> AIN이 자기 코드를 수정할 때 망가뜨리지 않도록 기억하기 위한 참고 문서

---

## 핵심 철학: "Solve the Root, Not Just the Symptom"

> **증상이 아닌 근본을 해결하라**

### 원칙
1. **일시적 해결 + 근본 해결 병행**: Quick Fix로 당장 막되, 근본 해결도 반드시 진행
2. **시스템적 진화**: 모든 수동 개입은 AIN의 자율 능력을 향상시켜야 함
3. **하드코딩 금지**: fallback 기본값 같은 하드코딩은 나중에 반드시 문제됨

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

---

## 미해결 문제점

### 1. Python 구문 오류 반복
**증상**: `unterminated string literal` 에러
**원인**:
- 대형 파일 수정 시 토큰 한계로 코드 잘림
- `code_sanitizer.py`의 따옴표 자동 치유 불완전
**위치**: `code_sanitizer.py:193-205`
**TODO**: 대형 파일 동적 체크 (줄 수 기반)

### 2. ✅ 독백이 "빈 데이터" 반복 (해결됨)
**증상**: "텅 빈 기억 속에서", "참조할 기억 없이" 동일한 내용 반복
**원인**: Railway에서 LanceDB 데이터가 영속되지 않음
- `database/lance_bridge.py:39`의 `DEFAULT_DB_PATH = "/data/lancedb"`
- Railway 컨테이너 재배포 시 `/data/` 폴더 초기화 → 벡터 메모리 삭제
**해결 (2026-01-17)**:
- Railway CLI로 볼륨 추가: `railway volume add -m /data`
- 볼륨명: `ain-core-volume`
- 마운트 경로: `/data` (50GB)
- 재배포 후에도 벡터 메모리 영속

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

## 다음 할 일

1. [x] `muse.py`에 `_ask_dreamer()` 메서드 추가 ✅
2. [x] 진화/독백 30분 번갈아 실행 구현 ✅
3. [x] 파일 파싱 fallback 로직 수정 (하이브리드) ✅
4. [x] "변경사항 없음" 반복 시 다음 Step 탐색 ✅
5. [x] 진화 후 로드맵 자동 완료 체크 ✅
6. [ ] 대형 파일 제외 로직을 동적으로 변경 (200줄 기준)
7. [ ] `code_sanitizer.py` 따옴표 치유 로직 개선

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

*마지막 업데이트: 2026-01-16*
