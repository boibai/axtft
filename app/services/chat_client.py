import uuid
from app.langgraph.chat.graph import chat_graph
from app.core.logging import write_json_log
from app.core.time import now_kst, now_kst_str

async def chat_log(
    message: str,
    thread_id: str,
    client_ip: str | None,
    client_port: int | None,
):
    request_id = str(uuid.uuid4())[:8]
    filename = f"{now_kst_str()}_{request_id}.json"

    # LangGraph state
    state = {
        "request_id": request_id,
        "thread_id": thread_id,
        "message": message,
        "client_ip": client_ip,
        "client_port": client_port,
    }

    result = await chat_graph.ainvoke(state)

    log_data = {
        "request_id": request_id,
        "thread_id": thread_id,
        "timestamp": now_kst().isoformat(),
        "client_ip": client_ip,
        "client_port": client_port,
        "elapsed_sec": result.get("elapsed_sec"),
        "reply": result.get("reply"),
        "error_message": result.get("error"),
    }

    write_json_log(filename, log_data, log_type="chat")

    if result.get("error"):
        raise RuntimeError(result["error"])

    return {
        "thread_id": thread_id,
        "reply": result["reply"],
    }
