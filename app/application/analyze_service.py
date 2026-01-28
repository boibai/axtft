import uuid
from app.langgraph.analyze.graph import analyze_graph
from app.core.logging import write_json_log
from app.core.time import now_kst, now_kst_str

# /analyze API에서 전달된 분석 요청을 처리하는 서비스 레이어 함수
async def handle_analyze_request(
    message: str,
    client_ip: str | None,
    client_port: int | None,
):
    
    # 단일 분석 요청을 식별하기 위한 request_id 생성 ( 추후 실제 요청 id로 전환 )
    request_id = str(uuid.uuid4())[:8]
    
    # 분석 로그 파일명 생성 ( 시간 + request_id 조합으로 로그 추적 및 충돌 방지 )
    filename = f"{now_kst_str()}_{request_id}.json"

    # LangGraph로 전달할 상태(state) 객체
    state = {
        "request_id": request_id,
        "message": message,
        "client_ip": client_ip,
        "client_port": client_port,
    }
    
    # LangGraph 분석 워크플로우 실행 (비동기)
    result = await analyze_graph.ainvoke(state)

    # log로 남길 데이터
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

    # 분석 결과 및 메타데이터를 JSON 파일로 저장
    write_json_log(filename, log_data, log_type="analyze")

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["parsed_json"]
