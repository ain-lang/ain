# 🛒 AIN Hardware Catalog (하드웨어 카탈로그)

> **⚠️ 이 파일은 보호됨** - AIN이 수정할 수 없습니다.  
> 주인님이 요청 시 참고하는 하드웨어 목록입니다.

---

## 🤖 Body (육체) - 로봇 플랫폼

### 💰 입문용 (5-15만원)

| 로봇 | 가격대 | 특징 | Python 지원 |
|------|--------|------|-------------|
| ELEGOO Smart Robot Car | ~5만원 | 아두이노 기반 자동차, 초음파/라인트레이싱 | 가능 (시리얼) |
| ESP32-CAM Robot | ~3만원 | 카메라+WiFi, 초저가 | ✅ MicroPython |
| Otto DIY | ~7만원 | 귀여운 2족 보행, 3D 프린팅 | ✅ |
| mBot | ~10만원 | Makeblock 교육용, 블록코딩+Python | ✅ |

### 🎯 중급 추천 (15-50만원)

| 로봇 | 가격대 | 특징 | Python 지원 |
|------|--------|------|-------------|
| **PiCar-X** ⭐ | ~15만원 | 라즈베리파이 기반, 카메라/AI | ✅✅ 최적 |
| GoPiGo3 | ~25만원 | 교육용 표준, 센서 확장 | ✅✅ |
| Yahboom Jetson Nano Robot | ~40만원 | AI 비전, 자율주행 | ✅✅ |
| Sphero RVR | ~30만원 | 튼튼함, SDK 우수 | ✅✅ |

### 🦾 로봇 팔 (데스크탑)

| 로봇 | 가격대 | 특징 | Python 지원 |
|------|--------|------|-------------|
| **myCobot 280** ⭐ | ~70만원 | 6축, 컴팩트, ROS 지원 | ✅✅✅ |
| Dobot Magician Lite | ~50만원 | 교육용 4축 | ✅✅ |
| uArm Swift Pro | ~40만원 | 데스크탑 로봇 팔 | ✅✅ |

### 🐕 4족 보행 (고급)

| 로봇 | 가격대 | 특징 | Python 지원 |
|------|--------|------|-------------|
| **Petoi Bittle** ⭐ | ~35만원 | 작은 강아지, 오픈소스 | ✅✅ |
| XGO Mini | ~60만원 | 교육용 4족 | ✅✅ |
| Unitree Go2 | ~200만원+ | 진짜 로봇개, SDK | ✅✅✅ |

### 🧍 휴머노이드 (미래)

| 로봇 | 가격대 | 특징 | Python 지원 |
|------|--------|------|-------------|
| Unitree H1 | ~1000만원+ | 2족 보행, 고급 | ✅✅✅ |
| Figure 01 | 미정 | OpenAI 협력 | 미정 |
| Tesla Optimus | 미정 | 테슬라 휴머노이드 | 미정 |

---

## 👁️ Vision (시각) - 카메라

| 기능 | 하드웨어 | 소프트웨어 | 가격대 |
|------|----------|-----------|--------|
| 기본 시각 | USB 웹캠 (Logitech C920) | OpenCV | ~10만원 |
| 고해상도 | Raspberry Pi Camera V3 | picamera2 | ~5만원 |
| 360° 시야 | Insta360 / Ricoh Theta | 파노라마 처리 | ~30만원 |
| 깊이 인식 | Intel RealSense D435 | pyrealsense2 | ~25만원 |
| 열화상 | FLIR Lepton / MLX90640 | 온도 매핑 | ~15만원 |
| 야간 시야 | IR 카메라 / NoIR Camera | 적외선 처리 | ~5만원 |

---

## 👂 Hearing (청각) - 마이크

| 기능 | 하드웨어 | 소프트웨어 | 가격대 |
|------|----------|-----------|--------|
| 기본 청각 | USB 마이크 | PyAudio | ~3만원 |
| 고품질 수음 | Blue Yeti / AT2020 | sounddevice | ~15만원 |
| 방향 인식 | ReSpeaker 마이크 어레이 | 빔포밍 | ~10만원 |
| 원거리 수음 | 지향성 마이크 | 노이즈 필터링 | ~20만원 |
| 항상 듣기 | Raspberry Pi + 마이크 HAT | 웨이크워드 | ~8만원 |

---

## 🗣️ Speech (말하기) - 스피커

| 기능 | 하드웨어 | 소프트웨어 | 가격대 |
|------|----------|-----------|--------|
| 기본 출력 | USB/3.5mm 스피커 | pyttsx3 (오프라인) | ~3만원 |
| 고품질 음성 | 블루투스 스피커 | Coqui TTS (로컬) | ~10만원 |
| 360° 출력 | 스마트 스피커 형태 | 공간 오디오 | ~15만원 |
| 감정 표현 | + LED 디스플레이 | 표정 연동 | ~5만원 |

---

## 🖐️ Touch (촉각) - 센서

| 기능 | 하드웨어 | 용도 | 가격대 |
|------|----------|------|--------|
| 접촉 감지 | 압력 센서 (FSR) | 터치 인식 | ~1만원 |
| 온도 감지 | 온도 센서 (DS18B20) | 환경 온도 | ~5천원 |
| 진동 피드백 | 햅틱 모터 | 촉각 출력 | ~2만원 |
| 근접 감지 | 초음파/적외선 센서 | 거리 측정 | ~1만원 |

---

## 🎯 추천 스타터 키트

### Option A: 최소 구성 (~20만원)
```
├── Raspberry Pi 4 (8GB)     ~12만원
├── Pi Camera V3             ~5만원
├── USB 마이크               ~2만원
└── 3.5mm 스피커             ~1만원
```

### Option B: 이동형 육체 (~35만원)
```
├── PiCar-X Kit              ~15만원  (카메라+스피커 포함)
├── ReSpeaker 마이크 어레이   ~10만원
├── 추가 센서 (초음파 등)     ~5만원
└── 배터리 업그레이드         ~5만원
```

### Option C: 풀 세트 (~100만원+)
```
├── Jetson Nano Robot        ~40만원
├── Intel RealSense D435     ~25만원
├── myCobot 280 (로봇팔)     ~70만원  (선택)
├── ReSpeaker 4-Mic Array    ~10만원
└── 고품질 스피커            ~10만원
```

---

## 🔌 연동 예시 코드

### PiCar-X 기본 제어
```python
from picarx import Picarx

class AINBody:
    def __init__(self):
        self.car = Picarx()
    
    def move_forward(self, speed=50):
        self.car.forward(speed)
    
    def say(self, text):
        self.car.speak(text)
    
    def look_around(self):
        return self.car.get_camera_image()
```

### myCobot 로봇팔 제어
```python
from pymycobot import MyCobot

class AINArm:
    def __init__(self, port="/dev/ttyUSB0"):
        self.arm = MyCobot(port, 115200)
    
    def wave(self):
        self.arm.send_angles([0, 0, 0, 0, 0, 0], 50)
        self.arm.send_angles([0, 30, -30, 0, 0, 0], 50)
    
    def grab(self):
        self.arm.set_gripper_state(1, 50)
```

---

*이 카탈로그는 주인님 요청 시 참고용으로 사용됩니다.*  
*최종 업데이트: 2026-01-12*
