FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app/app
# 로그는 컨테이너 외부로
ENV LOG_DIR=/data/logs
RUN mkdir -p /data/logs

ENV PYTHONPATH=/app

EXPOSE 9000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1", "--loop", "uvloop", "--http", "httptools"]
