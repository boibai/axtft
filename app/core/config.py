import os
import ipaddress
from dotenv import load_dotenv

load_dotenv()

# 로그 파일을 저장할 디렉토리 경로
LOG_DIR = os.getenv("LOG_DIR", "/data/logs")

# 로그 디렉토리가 존재하지 않으면 자동 생성
os.makedirs(LOG_DIR, exist_ok=True)

# 로컬 실행 시 기본 주소
# Docker 환경에서는 "http://host.docker.internal:8000/v1/chat/completions"
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL")

# vLLM에서 실제로 사용할 LLM 모델 이름
MODEL_NAME = os.getenv("MODEL_NAME")

# 로그 분석(analyze) 전용 시스템 프롬프트 파일 경로
ANALYZE_ERROR_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/analyze_error_system_prompt.txt"
)

ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/analyze_anomaly_system_prompt.txt"
)

# IP 화이트리스트 기능 활성화 여부
ENABLE_IP_WHITELIST = (
    os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true"
)

# 허용할 IP 또는 네트워크 목록
ALLOWED_NETWORKS = [
    ipaddress.ip_network(net.strip())
    for net in os.getenv(
        "ALLOWED_NETWORKS",
        "0.0.0.0"
    ).split(",")
]

# Redis
REDIS_URL = os.getenv("REDIS_URL")

# Metric Fields
METRIC_FIELDS = [
    "timestamp",
    "http_error_rate",
    "latency_p95",
    "latency_p99",
    "service_status",
    "cpu_usage",
    "memory_usage",
    "throughput",
    "db_connection_pool",
    "disk_usage",
]

# Log Fields
LOG_FIELDS = [
    "timestamp",
    #"service",
    #"pid",
    #"thread",
    "level",
    "logger",
    "message",
]