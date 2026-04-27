import asyncio, json, argparse
from datetime import datetime, timezone, timedelta
from typing import Any
from app.langgraph.common.llm import call_report_llm
from app.langgraph.common.utils import truncate_by_tokens
from app.report.utils import (
    get_last_10min_window,
    fetch_logs,
    build_log_llm_input,
    build_metric_queries,
    fetch_metric_time_map,
    aggregate_metrics,
    get_valid_metric_names,
    build_metric_llm_input,
    load_system_prompt,
    build_user_prompt_interval,
    build_chat_messages,
    save_interval_report
)

from app.core.config import (
    INTERVAL_REPORT_SYSTEM_PROMPT_PATH,
)
from app.core.logging import get_interval_logger

kst = timezone(timedelta(hours=9))

def parse_args():
    """
    CLI 파라미터
    --start, --end 직접 지정 가능
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, required=False)
    parser.add_argument("--end", type=str, required=False)
    return parser.parse_args()

async def run_with_retry(start_time, end_time, logger, max_retries: int = 3, delay_sec: int = 60):
    """
    interval report 실행 + retry 로직

    - 최대 3번 재시도
    - 실패 시 delay_sec 만큼 대기
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("RUN ATTEMPT %d/%d", attempt, max_retries)
            result = await run_interval_report(start_time, end_time, logger)
            return result

        except Exception:
            logger.exception("RUN FAILED (attempt %d/%d)", attempt, max_retries)

            if attempt == max_retries:
                logger.error("ALL RETRIES FAILED")
                raise

            logger.info("RETRY AFTER %s sec...", delay_sec)
            await asyncio.sleep(delay_sec)
            
async def run_interval_report(start_time, end_time, logger) -> dict[str, Any]:
    
    """
    interval report 생성 핵심 로직

    흐름:
    1. 로그 수집
    2. 메트릭 수집 및 집계
    3. LLM 입력 생성
    4. LLM 호출
    5. 결과 저장
    """

    # 기준 시간 (end 기준으로 로그 조회 등에서 사용)
    now = end_time 
    
    logger.info("%s RUN INTERVAL REPORT","=" * 20 )
    logger.info("- START TIME : %s", start_time)
    logger.info("- END TIME : %s", end_time)

    # ------------------------
    # 1. 로그 수집
    # ------------------------
    try :
        logs = fetch_logs(now=now, start_time=start_time, end_time=end_time)
    except Exception as e :
        # 로그 수집 실패해도 전체 파이프라인은 계속 진행
        logger.error(e)
        logs = ""
    
    # 로그 → LLM 입력용 텍스트 + 토큰 제한
    log_llm_input = truncate_by_tokens(build_log_llm_input(logs), max_tokens=8192)
    
    # ------------------------
    # 2. 메트릭 수집 및 가공
    # ------------------------
    # metric 쿼리 생성
    queries = build_metric_queries()
    metric_names = list(queries.keys())

    # 시계열 데이터 조회 (1초 단위)
    time_map = fetch_metric_time_map(
        queries=queries,
        start_time=start_time,
        end_time=end_time,
        step="1s",
    )

    # 10초 단위로 집계
    aggregated_map = aggregate_metrics(
        time_map=time_map,
        metric_names=metric_names,
        bucket_seconds=10,
    )

    # 데이터 품질 기준으로 metric 필터링 (null 비율 기준)
    valid_metric_names = get_valid_metric_names(
        aggregated_map=aggregated_map,
        metric_names=metric_names,
        null_ratio_threshold=0.8,
    )

    # metric → LLM 입력 텍스트 생성
    metric_llm_input = build_metric_llm_input(
        aggregated_map=aggregated_map,
        valid_metric_names=valid_metric_names,
        min_non_null_ratio=0.7,
    )
    
    # ------------------------
    # 3. 프롬프트 구성
    # ------------------------
    system_prompt = load_system_prompt(INTERVAL_REPORT_SYSTEM_PROMPT_PATH)
    
    logger.info("%s LOG INPUT","=" * 20 )
    logger.info(log_llm_input)
    
    logger.info("%s METRIC INPUT","=" * 20 )
    logger.info(metric_llm_input) 
    
    # user prompt 생성 (로그 + 메트릭 함께 전달)
    user_prompt = build_user_prompt_interval(
        metric_llm_input=metric_llm_input,
        log_llm_input=log_llm_input
    )
    
    # LLM 메시지 구조 생성
    messages = build_chat_messages(system_prompt, user_prompt)

    # ------------------------
    # 4. LLM 호출
    # ------------------------
    result, metadata = await call_report_llm(messages, type="interval")
    
    # 시간 구간 정보 추가
    result["timeWindow"] = {
        "start": start_time.strftime("%H:%M:%S"),
        "end": end_time.strftime("%H:%M:%S"),
    }
    
    logger.info("%s META DATA","=" * 20 )
    logger.info(json.dumps(metadata, ensure_ascii=False, indent=2))

    logger.info("%s LLM RESULT","=" * 20 )
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    
    # ------------------------
    # 5. 결과 저장
    # ------------------------
    save_path = save_interval_report(result, start_time, end_time)
    logger.info(f"{"=" * 20 } SAVED DATA : {save_path}")

    return result


def main() -> None:
    """
    프로그램 진입점

    - CLI 입력 처리
    - 기본 15분 window 설정
    - logger 생성
    - async 실행
    """
    args = parse_args()

    # start/end 직접 입력한 경우
    if args.start and args.end:
        start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=kst)
        end_time = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S").replace(tzinfo=kst)
        
    else:
        # 기본: 최근 10분 window 자동 계산
        now = datetime.now(kst)
        start_time, end_time = get_last_10min_window(now)

    # interval 단위 logger 생성
    logger = get_interval_logger(start_time, end_time)

    try:
        # retry 포함 실행
        result = asyncio.run(run_with_retry(start_time, end_time, logger))
        print(result)
    except Exception as e:
        logger.error("FINAL FAILURE: %s", str(e))


if __name__ == "__main__":
    main()