# Base image
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Matplotlib이 한글 폰트를 찾을 수 있도록 설정
    MPLCONFIGDIR=/tmp/matplotlib_config

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
# fonts-nanum: 리눅스 환경에서 그래프 한글 깨짐 방지
RUN apt-get update && apt-get install -y \
    build-essential \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# 패키지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 실행 권한 부여
RUN chmod +x needle_test.py entrypoint.sh

# 엔트리포인트 설정
ENTRYPOINT ["./entrypoint.sh"]

# 기본 명령어 (entrypoint.sh에 전달됨)
CMD ["test"]
