import uuid ,asyncio, httpx, logging, json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, before_sleep_log
from app.langgraph.analyze.error.graph import analyze_error_graph
from app.langgraph.analyze.anomaly.graph import analyze_anomaly_graph
from app.core.logging import write_json_data, get_app_logger, get_current_request_id
from app.core.time import now_kst, now_kst_str
from app.langgraph.common.schema import AnalyzeErrorRequest, AnalyzeAnomalyRequest, AnalyzeErrorMessageRequest
from app.utils.preprocess import preprocess_error_async

logger = get_app_logger()

def _is_retryable_error(exc: Exception) -> bool:
    msg = str(exc) if exc else ""

    if isinstance(exc, (httpx.RequestError, httpx.TimeoutException, asyncio.TimeoutError)):
        return True

    retry_signals = [
    ]
    if any(s in msg for s in retry_signals):
        return True

    return False


@retry(
    # 최대 3번까지 재시도 (처음 1회 + 재시도 2회)
    stop=stop_after_attempt(3),
    
    # 재시도 간 대기 시간: 지수 증가 방식
    # 1초 → 2초 → 4초 (최대 4초까지 제한)
    wait=wait_exponential(multiplier=1, min=1, max=4),
    
    # _is_retryable_error 함수가 True를 반환하는 예외에 대해서만 재시도
    # (예: 네트워크 에러, 타임아웃 등)
    retry=retry_if_exception(_is_retryable_error),
    
    # 모든 재시도 실패 시 마지막 예외를 다시 발생시킴 (숨기지 않음)
    reraise=True,

    # 재시도 전에 로그 출력 (WARNING 레벨)
    # → 어떤 에러로 재시도하는지 로그로 확인 가능
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
        data = {
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
        write_json_data(filename, data, data_type="analyze/error")

        raise

    data = {
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
    write_json_data(filename, data, data_type="analyze/error")
    return result["parsed_json"]


async def handle_anomaly(
    message: AnalyzeAnomalyRequest,
    client_ip: str | None,
    client_port: int | None,
):
    request_id = get_current_request_id()
    
    logger.info("- INPUT:\n%s",json.dumps(message.model_dump(), indent=2, ensure_ascii=False, default=str))
    
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
        data = {
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
        write_json_data(filename, data, data_type="analyze/anomaly")
        raise

    data = {
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
    logger.info(
        "- OUTPUT:\n%s",
        json.dumps(result["parsed_json"], indent=2, ensure_ascii=False)
    )
    logger.info("- TOTAL_TOKEN : %s", result.get("total_tokens"))
    logger.info("%s END API","="*20)
    write_json_data(filename, data, data_type="analyze/anomaly")
    return result["parsed_json"]



## 임시
async def handle_error2(
    message: AnalyzeErrorMessageRequest,
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
        data = {
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
        write_json_data(filename, data, data_type="analyze/error")
        
        raise

    data = {
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
    write_json_data(filename, data, data_type="analyze/error")
    date_str = filename.split("_")[0] 
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    await preprocess_error_async(index_name="error",date=date,filename=filename.split(".json")[0])
    return result["parsed_json"]