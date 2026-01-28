import os
import ipaddress

# 로그 파일을 저장할 디렉토리 경로
LOG_DIR = os.getenv("LOG_DIR", "/data/logs")

# 로그 디렉토리가 존재하지 않으면 자동 생성
os.makedirs(LOG_DIR, exist_ok=True)

# 로컬 실행 시 기본 주소
# Docker 환경에서는 "http://host.docker.internal:8000/v1/chat/completions"
VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    "http://localhost:8000/v1/chat/completions"
)

# vLLM에서 실제로 사용할 LLM 모델 이름
MODEL_NAME = os.getenv("MODEL_NAME", "gemma-3n-E4B-it")

# 로그 분석(analyze) 전용 시스템 프롬프트 파일 경로
ANALYZE_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/analyze_system_prompt.txt"
)

# 일반 대화(chat) 전용 시스템 프롬프트 파일 경로
CHAT_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/chat_system_prompt.txt"
)

# 의사결정(검색 여부 판단 등) 프롬프트 경로
AGENT_DECISION_PROMPT_PATH = os.getenv(
    "CHAT_SYSTEM_PROMPT_PATH",
    "./app/prompts/agent_decision_prompt.txt"
)

# Tavily 검색 결과를 기반으로 답변을 생성할 때 사용하는 시스템 프롬프트
TAVILY_CHAT_SYSTEM_PROMPT_PATH = os.getenv(
    "TAVILY_CHAT_SYSTEM_PROMPT_PATH",
    "./app/prompts/tavily_chat_system_prompt.txt"
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

# Tavily Search API Key ( 실운영 시에는 반드시 환경 변수로 관리 )
TAVILY_API_KEY = "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"
