import uuid
from app.langgraph.analyze.graph import analyze_graph
from app.core.logging import write_json_log
from app.core.time import now_kst, now_kst_str

async def handle_analyze_request(
    message: str,
    client_ip: str | None,
    client_port: int | None,
):
    request_id = str(uuid.uuid4())[:8]
    filename = f"{now_kst_str()}_{request_id}.json"

    state = {
        "request_id": request_id,
        "message": message,
        "client_ip": client_ip,
        "client_port": client_port,
    }

    result = await analyze_graph.ainvoke(state)

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
        "input_text": message,
        "output_json": result.get("parsed_json"),
        "error_message": result.get("error"),
    }

    write_json_log(filename, log_data, log_type="analyze")

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["parsed_json"]
