import asyncio
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import DAILY_REPORT_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens
from app.report.utils import (
    load_and_filter_reports,
    build_llm_input,
    load_system_prompt,
    build_user_prompt_daily,
    build_chat_messages,
    save_daily_report,
    get_yesterday,
)
from app.langgraph.common.llm import call_report_llm
from app.core.logging import get_daily_logger

kst = timezone(timedelta(hours=9))


def parse_args():
    """
    CLI에서 날짜 입력 받기
    ex) --date 2026-04-22
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=False, help="YYYY-MM-DD")
    return parser.parse_args()


def get_target_date(date_str: str | None) -> datetime:
    """
    분석 대상 날짜 결정
    - 입력값 있으면 해당 날짜 사용
    - 없으면 '어제 날짜' 자동 계산
    """
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=kst)

    now = datetime.now(kst)
    return get_yesterday(now)


async def run_with_retry(target_time: datetime, logger, max_retries: int = 3, delay_sec: int = 60):
    """
    daily report 실행 + 실패 시 재시도 로직

    - 최대 max_retries 만큼 반복
    - 실패 시 delay_sec 만큼 대기 후 재시도
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("RUN ATTEMPT %d/%d", attempt, max_retries)
            # 실제 daily report 실행
            result = await run_daily_report(target_time, logger)
            return result

        except Exception:
            # 에러 발생 시 stack trace 로그
            logger.exception("RUN FAILED (attempt %d/%d)", attempt, max_retries)

            # 마지막 시도였다면 종료
            if attempt == max_retries:
                logger.error("ALL RETRIES FAILED")
                raise
            
            # 재시도 전 대기
            logger.info("RETRY AFTER %s sec...", delay_sec)
            await asyncio.sleep(delay_sec)


async def run_daily_report(target_time: datetime, logger) -> dict[str, Any]:
    """
    daily report 생성 핵심 로직

    흐름:
    1. interval 리포트 로드
    2. LLM 입력 텍스트 생성
    3. prompt 구성
    4. LLM 호출
    5. 결과 저장
    """
    logger.info("%s RUN DAILY REPORT", "=" * 20)

    # 날짜 문자열 (YYYY-MM-DD)
    date_str = target_time.strftime("%Y-%m-%d")
    logger.info("- TARGET DATE : %s", date_str)

    # 해당 날짜 interval 리포트 로드 및 필터링
    reports = load_and_filter_reports(date_str)

    # LLM 입력용 텍스트 생성
    llm_input_text_raw = build_llm_input(reports)
    
    # 토큰 제한 (LLM max context 대응)
    llm_input_text = truncate_by_tokens(llm_input_text_raw, max_tokens=8192)

    logger.info("%s INPUT INTERVAL REPORTS", "=" * 20)
    logger.info("\n%s", llm_input_text)

    # system prompt 로드
    system_prompt = load_system_prompt(DAILY_REPORT_SYSTEM_PROMPT_PATH)
    
     # user prompt 생성 (interval 데이터 포함)
    user_prompt = build_user_prompt_daily(
        llm_input=llm_input_text
    )

    # LLM 메시지 구조 생성 (system + user)
    messages = build_chat_messages(system_prompt, user_prompt)

    # LLM 호출 (daily 타입)
    result, metadata = await call_report_llm(messages, type="daily")
    
    # 결과에 날짜 추가
    result["report_date"] = date_str

    logger.info("%s META DATA", "=" * 20)
    logger.info(json.dumps(metadata, ensure_ascii=False, indent=2))

    logger.info("%s LLM RESULT", "=" * 20)
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))

    # 파일 저장
    save_path = save_daily_report(result, date_str)
    logger.info("%s SAVED DATA : %s", "=" * 20, save_path)

    return result


def main() -> None:
    """
    프로그램 진입점
    - CLI 파라미터 처리
    - logger 생성
    - async 실행
    """
    args = parse_args()

    try:
        # 대상 날짜 결정
        target_time = get_target_date(args.date)
        
        # 날짜 기반 logger 생성 (파일 분리 목적)
        logger = get_daily_logger(target_time)

        # async 실행 + retry 포함
        result = asyncio.run(run_with_retry(target_time, logger))
        print(result)

    except Exception as e:
        print(f"FINAL FAILURE: {e}")
        raise


if __name__ == "__main__":
    main()