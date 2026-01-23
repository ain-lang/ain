# AIN 확정 진화용 Dockerfile - Python + Mojo (pip)
FROM python:3.11-slim

# 1. 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Python 종속성 설치 (Mojo, LanceDB 포함)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. LanceDB 데이터 디렉토리 생성 (Volume 마운트 포인트)
RUN mkdir -p /data/lancedb

# 5. 소스 코드 복사
COPY . .

# 6. 설치 확인
RUN python -c "import lancedb; print('✅ LanceDB OK')" || echo "⚠️ LanceDB import failed"
RUN mojo --version && echo "✅ Mojo OK" || echo "⚠️ Mojo CLI not in PATH"

# 7. AIN 실행
CMD ["python", "main.py"]
