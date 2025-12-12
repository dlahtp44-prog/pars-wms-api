# 1. 안정적인 Python 3.12를 기반 이미지로 사용합니다.
FROM python:3.12-slim

# 2. Pillow 빌드에 필요한 시스템 종속성을 설치합니다.
# apt-get은 Docker 빌드 단계에서 실행되어 Read-only 오류를 피합니다.
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리를 설정합니다.
WORKDIR /app

# 4. requirements.txt 파일을 복사하고 Python 패키지를 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 코드를 복사합니다.
COPY . .

# 6. 서버 실행 명령어 (Procfile에 uvicorn 실행 명령이 있을 경우 이를 참조합니다.)
# 프로젝트의 'run_server.bat' 파일이나 일반적인 FastAPI 실행 명령을 사용합니다.
# Procfile이 있다면 Start Command를 'gunicorn main:app'으로 설정하거나, Dockerfile에 uvicorn 명령을 사용합니다.
# Procfile이 있는 것으로 보이므로, 여기서는 uvicorn 명령을 사용하겠습니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
