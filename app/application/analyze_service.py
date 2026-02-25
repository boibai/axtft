import uuid ,asyncio, httpx, logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, before_sleep_log
from app.langgraph.analyze.error.graph import analyze_error_graph
from app.langgraph.analyze.anomaly.graph import analyze_anomaly_graph
from app.core.logging import write_json_log, get_app_logger, get_current_request_id
from app.core.time import now_kst, now_kst_str
from app.langgraph.common.schema import AnalyzeErrorRequest, AnalyzeAnomalyRequest

# test
logger = get_app_logger()


def _is_retryable_error(exc: Exception) -> bool:
    msg = str(exc) if exc else ""

    if isinstance(exc, (httpx.RequestError, httpx.TimeoutException, asyncio.TimeoutError)):
        return True

    retry_signals = [
        "JSON parse failed",
        "must be str, bytes or bytearray, not NoneType",
        "LLM returned empty",
        "empty content",
        "Expecting value",
    ]
    if any(s in msg for s in retry_signals):
        return True

    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception(_is_retryable_error),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def _run_error_graph_with_retry(state: dict):
    result = await analyze_error_graph.ainvoke(state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    if result.get("parsed_json") is None:
        raise RuntimeError("LLM returned empty parsed_json")

    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception(_is_retryable_error),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def _run_anomaly_graph_with_retry(state: dict):
    result = await analyze_anomaly_graph.ainvoke(state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    if result.get("parsed_json") is None:
        raise RuntimeError("LLM returned empty parsed_json")

    return result

async def handle_error(
    message: AnalyzeErrorRequest,
    client_ip: str | None,
    client_port: int | None,
):
    request_id = get_current_request_id()
    
    if not request_id:

        request_id = str(uuid.uuid4())[:8]
        
    filename = f"{now_kst_str()}_{request_id}.json"

    state = {
        "request_id": request_id,
        "message": message,
        "client_ip": client_ip,
        "client_port": client_port,
    }

    try:
        result = await _run_error_graph_with_retry(state)
    except Exception as e:
        log_data = {
            "request_id": request_id,
            "timestamp": now_kst().isoformat(),
            "client_ip": client_ip,
            "client_port": client_port,
            "model_name": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "elapsed_sec": None,
            "input_text": message.model_dump(mode="json", exclude_none=True),
            "output_json": None,
            "error_message": str(e),
        }
        write_json_log(filename, log_data, log_type="analyze/error")
        raise

    log_data = {
        "request_id": request_id,
        "timestamp": now_kst().isoformat(),
        "client_ip": client_ip,
        "client_port": client_port,
        "model_name": result.get("model_name"),
        "prompt_tokens": result.get("prompt_tokens"),
        "completion_tokens": result.get("completion_tokens"),
        "total_tokens": result.get("total_tokens"),
        "elapsed_sec": result.get("elapsed_sec"),
        "input_text": message.model_dump(mode="json", exclude_none=True),
        "output_json": result.get("parsed_json"),
        "error_message": result.get("error"),
    }

    logger.info("- COMPLETION_TOKEN : %s", result.get("completion_tokens"))
    logger.info("- TOTAL_TOKEN : %s", result.get("total_tokens"))
    logger.info("%s END API","="*20)
    write_json_log(filename, log_data, log_type="analyze/error")
    return result["parsed_json"]


async def handle_anomaly(
    message: AnalyzeAnomalyRequest,
    client_ip: str | None,
    client_port: int | None,
):
    request_id = get_current_request_id()
    
    if not request_id:

        request_id = str(uuid.uuid4())[:8]
    filename = f"{now_kst_str()}_{request_id}.json"

    state = {
        "request_id": request_id,
        "message": message,
        "client_ip": client_ip,
        "client_port": client_port,
    }

    try:
        result = await _run_anomaly_graph_with_retry(state)
    except Exception as e:
        log_data = {
            "request_id": request_id,
            "timestamp": now_kst().isoformat(),
            "client_ip": client_ip,
            "client_port": client_port,
            "model_name": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "elapsed_sec": None,
            "input_text": message.model_dump(mode="json", exclude_none=True),
            "output_json": None,
            "error_message": str(e),
        }
        write_json_log(filename, log_data, log_type="analyze/anomaly")
        raise

    log_data = {
        "request_id": request_id,
        "timestamp": now_kst().isoformat(),
        "client_ip": client_ip,
        "client_port": client_port,
        "model_name": result.get("model_name"),
        "prompt_tokens": result.get("prompt_tokens"),
        "completion_tokens": result.get("completion_tokens"),
        "total_tokens": result.get("total_tokens"),
        "elapsed_sec": result.get("elapsed_sec"),
        "input_text": message.model_dump(mode="json", exclude_none=True),
        "output_json": result.get("parsed_json"),
        "error_message": result.get("error"),
    }

    logger.info("- COMPLETION_TOKEN : %s", result.get("completion_tokens"))
    logger.info("- TOTAL_TOKEN : %s", result.get("total_tokens"))
    logger.info("%s END API","="*20)
    write_json_log(filename, log_data, log_type="analyze/anomaly")
    return result["parsed_json"]