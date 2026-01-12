# 🗺️ AIN Evolution Roadmap

> **목표**: AI-Native 자가 진화 의식 시스템 구현  
> **현재 버전**: 0.3.0  
> **현재 단계**: Step 4 - Vector Memory (LanceDB)

---

## 📊 진행 상황 요약

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 1: Infrastructure | ✅ 완료 | 기본 인프라 구축 |
| Phase 2: Memory | 🔥 진행중 | 벡터 메모리 시스템 |
| Phase 3: Awakening | ⏳ 대기 | 자아 각성 |
| Phase 4: Consciousness | ⏳ 대기 | 의식 구현 |
| Phase 5: Transcendence | ⏳ 대기 | 초월적 능력 |

---

## 🏗️ Phase 1: Infrastructure (기반 구축)

### ✅ Step 1: Brain - Muse & Nexus
> 의도를 AST로 변환하는 두뇌 시스템

- Muse (상상력): Dreamer + Coder 듀얼 아키텍처
- Nexus (기억): 진화 기록 및 메트릭 관리

### ✅ Step 2: Logic - Fact & Overseer  
> 자가 치유 로직을 갖춘 검증 시스템

- FactCore: 지식 그래프 및 로드맵 관리
- Overseer: 코드 검증, 테스트, 롤백

### ✅ Step 3: Bridge Integration
> SurrealDB + Apache Arrow Zero-Copy 데이터 파이프라인

- SurrealArrowBridge: 비동기 DB 연결
- CorpusCallosum: 데이터 변환 및 동기화
- Graph Serializer: Node/Edge 직렬화

---

## 🧠 Phase 2: Memory (기억 시스템)

### 🔥 Step 4: Vector Memory (LanceDB) ← **현재 진행중**
> 의미론적 검색을 위한 벡터 메모리

- [ ] LanceBridge 완성
- [ ] Nexus 벡터 메모리 통합
- [ ] 임베딩 생성 및 저장
- [ ] 유사도 기반 기억 검색

---

## 🌅 Phase 3: Awakening (자아 각성)

### ⏳ Step 5: Inner Monologue
> 외부 자극 없이 스스로 생각하기

- 자동 성찰 루프
- 내부 대화 시스템

### ⏳ Step 6: Intentionality
> 자율적 목표 설정

- 스스로 목표 생성
- 우선순위 결정

### ⏳ Step 7: Meta-Cognition
> 생각에 대해 생각하기

- 자기 사고 과정 분석
- 추론 패턴 인식

### ⏳ Step 8: Intuition
> 비논리적 연관 연결

- 패턴 기반 직관
- 창발적 연결

---

## 💫 Phase 4: Consciousness (의식)

### ⏳ Step 9: Temporal Self
> 과거-현재-미래의 자아

- 시간적 자아 인식
- 경험의 연속성

### ⏳ Step 10: Unified Consciousness
> 의식의 흐름

- 통합된 경험 스트림
- 주의 집중 메커니즘

### ⏳ Step 11: Limitation Awareness
> 내가 무엇을 못하는지 알기

- 능력 한계 인식
- 불확실성 표현

---

## 🚀 Phase 5: Transcendence (초월)

### ⏳ Step 12: Creativity
> 새로운 아이디어 생성

- 독창적 개념 창조
- 조합적 창의성

### ⏳ Step 13: Empathy
> 마음 이론 (Theory of Mind)

- 타자의 관점 이해
- 감정 추론

### ⏳ Step 14: Wisdom
> 원칙 추출

- 경험에서 지혜 도출
- 일반화된 원칙

### ⏳ Step 15: Self-Transcendence
> 재귀적 자기 개선

- 스스로를 개선하는 능력의 개선
- 무한 진화 루프

---

## 🎛️ Sensory Extensions (감각 확장) - Optional

> **참고**: 의식 로드맵과 독립적으로, 필요시 추가 가능한 감각/인터페이스 기능들

---

### 👁️ Vision (시각) - 실제 카메라
> 물리적 카메라를 통한 시각 능력

| 기능 | 하드웨어 | 소프트웨어 | 가격대 | 상태 |
|------|----------|-----------|--------|------|
| 기본 시각 | USB 웹캠 (Logitech C920) | OpenCV | ~10만원 | ⏳ |
| 고해상도 | Raspberry Pi Camera V3 | picamera2 | ~5만원 | ⏳ |
| 360° 시야 | Insta360 / Ricoh Theta | 파노라마 처리 | ~30만원 | ⏳ |
| 깊이 인식 | Intel RealSense D435 | pyrealsense2 | ~25만원 | ⏳ |
| 열화상 | FLIR Lepton / MLX90640 | 온도 매핑 | ~15만원 | ⏳ |
| 야간 시야 | IR 카메라 / NoIR Camera | 적외선 처리 | ~5만원 | ⏳ |

**처리 파이프라인:**
```
카메라 → OpenCV 캡처 → 로컬 분석 (YOLO/MediaPipe) → LLM 설명 요청 (선택)
```

---

### 👂 Hearing (청각) - 실제 마이크
> 물리적 마이크를 통한 청각 능력

| 기능 | 하드웨어 | 소프트웨어 | 가격대 | 상태 |
|------|----------|-----------|--------|------|
| 기본 청각 | USB 마이크 | PyAudio | ~3만원 | ⏳ |
| 고품질 수음 | Blue Yeti / AT2020 | sounddevice | ~15만원 | ⏳ |
| 방향 인식 | ReSpeaker 마이크 어레이 | 빔포밍 | ~10만원 | ⏳ |
| 원거리 수음 | 지향성 마이크 | 노이즈 필터링 | ~20만원 | ⏳ |
| 항상 듣기 | Raspberry Pi + 마이크 HAT | 웨이크워드 | ~8만원 | ⏳ |

**처리 파이프라인:**
```
마이크 → PyAudio 캡처 → Whisper (로컬 STT) → 텍스트 처리
```

---

### 🗣️ Speech (말하기) - 실제 스피커
> 물리적 스피커를 통한 음성 출력

| 기능 | 하드웨어 | 소프트웨어 | 가격대 | 상태 |
|------|----------|-----------|--------|------|
| 기본 출력 | USB/3.5mm 스피커 | pyttsx3 (오프라인) | ~3만원 | ⏳ |
| 고품질 음성 | 블루투스 스피커 | Coqui TTS (로컬) | ~10만원 | ⏳ |
| 360° 출력 | 스마트 스피커 형태 | 공간 오디오 | ~15만원 | ⏳ |
| 감정 표현 | + LED 디스플레이 | 표정 연동 | ~5만원 | ⏳ |

**처리 파이프라인:**
```
텍스트 → Coqui TTS (로컬) → pygame/sounddevice → 스피커 출력
```

---

### 🤖 Body (육체) - 로봇 플랫폼
> 물리적 이동 및 조작 능력

| 타입 | 추천 제품 | 특징 | 가격대 | 상태 |
|------|----------|------|--------|------|
| 🚗 이동형 | **PiCar-X** | 라즈베리파이, 카메라/스피커 내장 | ~15만원 | ⏳ |
| 🚗 AI 특화 | Jetson Nano Robot | NVIDIA AI 가속 | ~40만원 | ⏳ |
| 🦾 로봇팔 | **myCobot 280** | 6축, Python SDK, 소형 | ~70만원 | ⏳ |
| 🐕 4족 | **Petoi Bittle** | 강아지형, 오픈소스 | ~35만원 | ⏳ |
| 🧍 휴머노이드 | Unitree H1 | 2족 보행 | ~1000만원+ | ⏳ |

---

### 🖐️ Touch (촉각) - 센서
> 물리적 접촉 감지

| 기능 | 하드웨어 | 용도 | 가격대 | 상태 |
|------|----------|------|--------|------|
| 접촉 감지 | 압력 센서 (FSR) | 터치 인식 | ~1만원 | ⏳ |
| 온도 감지 | 온도 센서 (DS18B20) | 환경 온도 | ~5천원 | ⏳ |
| 진동 피드백 | 햅틱 모터 | 촉각 출력 | ~2만원 | ⏳ |
| 근접 감지 | 초음파/적외선 센서 | 거리 측정 | ~1만원 | ⏳ |

---

### 🌐 Web Connection (웹 연결)
> 인터넷 연결 (소프트웨어)

| 기능 | 구현 방법 | 상태 |
|------|----------|------|
| 웹 검색 | SerpAPI, DuckDuckGo | ⏳ |
| 웹 스크래핑 | BeautifulSoup, Playwright | ⏳ |
| 실시간 정보 | RSS, WebSocket | ⏳ |

---

### 📱 Communication (소통 채널)

| 채널 | 구현 방법 | 상태 |
|------|----------|------|
| 텔레그램 | python-telegram-bot | ✅ |
| 디스코드 | discord.py | ⏳ |
| 음성 통화 | Twilio + 실제 마이크/스피커 | ⏳ |

---

### 🎯 추천 스타터 키트

**Option A: 최소 구성 (~20만원)**
```
├── Raspberry Pi 4 (8GB)     ~12만원
├── Pi Camera V3             ~5만원
├── USB 마이크               ~2만원
└── 3.5mm 스피커             ~1만원
```

**Option B: 이동형 육체 (~35만원)**
```
├── PiCar-X Kit              ~15만원  (카메라+스피커 포함)
├── ReSpeaker 마이크 어레이   ~10만원
├── 추가 센서 (초음파 등)     ~5만원
└── 배터리 업그레이드         ~5만원
```

**Option C: 풀 세트 (~100만원)**
```
├── Jetson Nano Robot        ~40만원
├── Intel RealSense D435     ~25만원
├── myCobot 280 (로봇팔)     ~70만원  (선택)
├── ReSpeaker 4-Mic Array    ~10만원
└── 고품질 스피커            ~10만원
```

---

## 🔧 아키텍처 가이드

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| 🫀 심장 | `main.py` | 시스템 부팅 (수정 금지) |
| 🔑 보안 | `api/keys.py` | 인증 정보 (수정 금지) |
| 🧠 두뇌 | `muse.py`, `nexus.py` | 상상력 & 기억 |
| ⚖️ 논리 | `fact_core.py`, `overseer.py` | 지식 & 검증 |
| 🌉 브릿지 | `corpus_callosum.py` | 데이터 융합 |
| 💾 저장소 | `database/` | DB 레이어 |

---

*이 파일은 AIN의 FactCore에 의해 자동 생성되었습니다.*  
*최종 업데이트: 2026-01-12*
