import os
import ipaddress

# Logging
LOG_DIR = os.getenv("LOG_DIR", "/data/logs")
os.makedirs(LOG_DIR, exist_ok=True)

# vLLM
VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    "http://host.docker.internal:8000/v1/chat/completions" # "http://localhost:8000/v1/chat/completions" / "http://host.docker.internal:8000/v1/chat/completions"
)
MODEL_NAME = os.getenv("MODEL_NAME", "gemma-3n-E4B-it")

# Prompt
ANALYZE_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/analyze_system_prompt.txt"
)

CHAT_SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "./app/prompts/chat_system_prompt.txt"
)

# IP Whitelist
ENABLE_IP_WHITELIST = (
    os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true"
)
ALLOWED_NETWORKS = [
    ipaddress.ip_network(net.strip())
    for net in os.getenv(
        "ALLOWED_NETWORKS",
        "1.232.105.101"
    ).split(",")
]



