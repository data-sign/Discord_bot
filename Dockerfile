FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요 파일 복사
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN echo "✅ Installed packages:" && pip list

# 디스코드 봇 실행
CMD ["python", "run.py"]
