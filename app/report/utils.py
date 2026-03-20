import re, requests, math, os, json, glob
from dateutil.parser import parse
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from collections import defaultdict
from app.core.config import (
    LOG_SERVER,
    METRIC_SERVER,
    ELS_PW,
    ELS_ID
)

kst = timezone(timedelta(hours=9))

def save_interval_report(result: dict, start_time: datetime, end_time: datetime):
    
    date_str = start_time.strftime("%Y-%m-%d")
    base_dir = f"./data/report/interval/{date_str.split("-")[0]}/{date_str.split("-")[1]}/{date_str.split("-")[2]}"

    os.makedirs(base_dir, exist_ok=True)

    filename = f"{start_time.strftime('%H%M')}_{end_time.strftime('%H%M')}.json"
    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return file_path

def save_daily_report(result: dict, date: str):
    base_dir = f"./data/report/daily/{date.split("-")[0]}/{date.split("-")[1]}"
    os.makedirs(base_dir, exist_ok=True)
    filename = f"{date.split("-")[2]}.json"
    file_path = os.path.join(base_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return file_path

def safe_get(d, *keys, default=None):
    current = d
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def parse_log_message(message: str) -> dict:
    if not message:
        return {
            "log_time": None,
            "log_level": None,
            "pid": None,
            "thread": None,
            "logger": None,
            "log_text": None,
        }

    pattern = re.compile(
        r"^-\[(?P<log_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\]\s+"
        r"\[(?P<log_level>[A-Z]+)\]\s+"
        r"\[(?P<pid>\d+)\]\s+---\s+"
        r"\[(?P<thread>[^\]]+)\]\s+"
        r"(?P<logger>[^:]+)\s+:\s+"
        r"(?P<log_text>.*)$"
    )

    match = pattern.match(message.strip())
    if not match:
        return {
            "log_time": None,
            "log_level": None,
            "pid": None,
            "thread": None,
            "logger": None,
            "log_text": message,
        }

    return match.groupdict()

def format_logs_for_llm(log_rows):
    lines = []

    for row in log_rows:
        log_time = row.get("log_time")

        if isinstance(log_time, datetime):
            time_str = log_time.strftime("%H:%M:%S")
        else:
            time_str = ""

        line = (
            f'{time_str}|'
            f'{row.get("log_level", "")}|'
            f'{row.get("thread", "")}|'
            f'{row.get("logger", "")}|'
            f'{row.get("log_text", "")}'
        )

        lines.append(line.strip())

    return "\n".join(lines)

def get_last_15min_window(now):
    minute = (now.minute // 10) * 10
    end_time = now.replace(minute=minute, second=0, microsecond=0)
    start_time = end_time - timedelta(minutes=10)
    return start_time, end_time

def get_yesterday(now):
    yesterday = now - timedelta(days=1)
    target_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    return target_date

def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def get_log_index_date(now: datetime) -> str:
    return now.strftime("%Y.%m.%d")


def build_log_query() -> dict[str, Any]:
    return {
        "query": {
            "match_all": {}
        }
    }


def build_metric_queries() -> dict[str, str]:
    return {
        "http_error_rate": """
            sum(rate(http_server_requests_seconds_count{status=~"5.."}[1m]))
            /
            clamp_min(sum(rate(http_server_requests_seconds_count[1m])), 1e-9)
        """,
        "latency_p95": """
            histogram_quantile(
                0.95,
                sum by (le) (rate(http_server_requests_seconds_bucket[1m]))
            ) * 1000
        """,
        "latency_p99": """
            histogram_quantile(
                0.99,
                sum by (le) (rate(http_server_requests_seconds_bucket[1m]))
            ) * 1000
        """,
        "throughput": """
            sum(rate(http_server_requests_seconds_count[1m]))
        """,
        "service_status": """
            max(up)
        """,
        "cpu_pressure": """
            (
                clamp_max(avg(system_cpu_usage), 1) * 0.7
            )
            +
            (
                clamp_max(avg(system_load_average_1m) / clamp_min(avg(system_cpu_count), 1), 1) * 0.3
            )
        """,
        "memory_pressure": """
            (
                clamp_max(
                    1 - (
                        sum(node_memory_MemAvailable_bytes)
                        /
                        clamp_min(sum(node_memory_MemTotal_bytes), 1)
                    ),
                    1
                ) * 0.5
            )
            +
            (
                clamp_max(
                    sum(jvm_memory_used_bytes{area="heap"})
                    /
                    clamp_min(sum(jvm_memory_max_bytes{area="heap"}), 1),
                    1
                ) * 0.5
            )
        """,
        "db_pool_pressure": """
            (
                (
                    sum(hikaricp_connections_active)
                    /
                    clamp_min(sum(hikaricp_connections_max), 1)
                ) * 0.6
            )
            +
            (
                clamp_max(sum(hikaricp_connections_pending) / 10, 1) * 0.3
            )
            +
            (
                clamp_max(sum(rate(hikaricp_connections_timeout_total[1m])) / 1, 1) * 0.1
            )
        """,
        "web_pressure": """
            (
                clamp_max(
                    sum(tomcat_threads_busy_threads)
                    /
                    clamp_min(sum(tomcat_threads_config_max_threads), 1),
                    1
                ) * 0.7
            )
            +
            (
                clamp_max(
                    sum(tomcat_connections_current_connections)
                    /
                    clamp_min(sum(tomcat_connections_config_max_connections), 1),
                    1
                ) * 0.3
            )
        """,
        "disk_pressure": """
            (
                clamp_max(
                    1 - (
                        sum(node_filesystem_free_bytes{fstype!~"tmpfs|overlay", mountpoint="/"})
                        /
                        clamp_min(sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay", mountpoint="/"}), 1)
                    ),
                    1
                ) * 0.8
            )
            +
            (
                clamp_max(sum(node_disk_io_now) / 10, 1) * 0.2
            )
        """,
        "network_pressure": """
            (
                clamp_max(sum(rate(node_netstat_Tcp_RetransSegs[1m])) / 1, 1) * 0.5
            )
            +
            (
                clamp_max(sum(rate(node_network_receive_drop_total[1m])) / 0.1, 1) * 0.25
            )
            +
            (
                clamp_max(sum(rate(node_network_transmit_drop_total[1m])) / 0.1, 1) * 0.25
            )
        """,
    }


def normalize_log_time(log_time: Any, tz: timezone) -> datetime | None:
    if log_time is None:
        return None

    if isinstance(log_time, str):
        try:
            log_time = parse(log_time)
        except Exception:
            return None

    if not isinstance(log_time, datetime):
        return None

    if log_time.tzinfo is None:
        return log_time.replace(tzinfo=tz)

    return log_time.astimezone(tz)


def fetch_logs(
    now: datetime,
    start_time: datetime,
    end_time: datetime,
) -> list[dict[str, Any]]:
    index_date = get_log_index_date(now)
    url = f"{LOG_SERVER}/logstash-{index_date}/_search"

    response = requests.get(
        url,
        headers={"Content-Type": "application/json"},
        json=build_log_query(),
        auth=HTTPBasicAuth(ELS_ID, ELS_PW),
        timeout=30,
    )
    response.raise_for_status()
    response_data = response.json()
    hits = response_data.get("hits", {}).get("hits", [])

    rows: list[dict[str, Any]] = []

    for hit in hits:
        source = hit.get("_source", {})
        message = source.get("message")
        parsed = parse_log_message(message)

        log_time = normalize_log_time(parsed.get("log_time"), kst)
        if log_time is None:
            continue

        if not (start_time <= log_time < end_time):
            continue

        rows.append(
            {
                "log_time": log_time,
                "log_level": parsed.get("log_level"),
                "pid": parsed.get("pid"),
                "thread": parsed.get("thread"),
                "logger": parsed.get("logger"),
                "log_text": parsed.get("log_text"),
                "log_offset": safe_get(source, "log", "offset"),
            }
        )

    return sorted(
        rows,
        key=lambda x: (
            x["log_time"],
            x["log_offset"] or 0,
        ),
    )


def build_log_llm_input(logs: list[dict[str, Any]]) -> str:
    header = "time|level|thread|logger|message"
    return header + "\n" + format_logs_for_llm(logs)


def fetch_metric_time_map(
    queries: dict[str, str],
    start_time: datetime,
    end_time: datetime,
    step: str = "1s",
) -> defaultdict[float, dict[str, float | None]]:
    time_map: defaultdict[float, dict[str, float | None]] = defaultdict(dict)

    for metric_name, query in queries.items():
        params = {
            "query": " ".join(query.split()),
            "start": start_time.timestamp(),
            "end": end_time.timestamp(),
            "step": step,
        }

        try:
            res = requests.get(
                f"{METRIC_SERVER}/api/v1/query_range",
                params=params,
                timeout=30,
            )
            res.raise_for_status()
            payload = res.json()
        except Exception as e:
            print(f"[REQUEST ERROR] {metric_name}: {e}")
            continue

        if payload.get("status") != "success":
            print(f"[PROMETHEUS ERROR] {metric_name}: {payload}")
            continue

        results = payload.get("data", {}).get("result", [])

        for series in results:
            for ts, value in series.get("values", []):
                ts_float = float(ts)

                try:
                    val = float(value)
                    if math.isnan(val) or math.isinf(val):
                        val = None
                except (TypeError, ValueError):
                    val = None

                time_map[ts_float][metric_name] = val

    return time_map


def aggregate_metrics(
    time_map: defaultdict[float, dict[str, float | None]],
    metric_names: list[str],
    bucket_seconds: int = 10,
) -> defaultdict[int, dict[str, float | None]]:
    bucket_map: defaultdict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for ts, row in time_map.items():
        bucket_ts = int(ts // bucket_seconds) * bucket_seconds

        for metric_name in metric_names:
            val = row.get(metric_name)
            if val is not None:
                bucket_map[bucket_ts][metric_name].append(val)

    aggregated_map: defaultdict[int, dict[str, float | None]] = defaultdict(dict)

    max_metrics = {"http_error_rate", "latency_p95", "latency_p99"}

    for bucket_ts, metric_dict in bucket_map.items():
        for metric_name in metric_names:
            values = metric_dict.get(metric_name, [])
            if not values:
                aggregated_map[bucket_ts][metric_name] = None
            elif metric_name in max_metrics:
                aggregated_map[bucket_ts][metric_name] = max(values)
            else:
                aggregated_map[bucket_ts][metric_name] = sum(values) / len(values)

    return aggregated_map


def get_valid_metric_names(
    aggregated_map: defaultdict[int, dict[str, float | None]],
    metric_names: list[str],
    null_ratio_threshold: float = 0.8,
) -> list[str]:
    always_keep = {"http_error_rate", "latency_p95", "latency_p99", "throughput", "service_status"}
    valid_metric_names: list[str] = []

    for metric_name in metric_names:
        total = len(aggregated_map)
        null_count = sum(
            1
            for ts in aggregated_map
            if aggregated_map[ts].get(metric_name) is None
        )
        null_ratio = null_count / total if total > 0 else 1

        if metric_name in always_keep or null_ratio < null_ratio_threshold:
            valid_metric_names.append(metric_name)

    return valid_metric_names


def build_metric_llm_input(
    aggregated_map: defaultdict[int, dict[str, float | None]],
    valid_metric_names: list[str],
    min_non_null_ratio: float = 0.7,
) -> str:
    lines: list[str] = []
    lines.append("|".join(["timestamp"] + valid_metric_names))

    for ts in sorted(aggregated_map.keys()):
        row_values: list[Any] = []
        non_null_count = 0

        for metric_name in valid_metric_names:
            val = aggregated_map[ts].get(metric_name)
            row_values.append(val)
            if val is not None:
                non_null_count += 1

        ratio = non_null_count / len(valid_metric_names) if valid_metric_names else 0
        if ratio < min_non_null_ratio:
            continue

        values = [datetime.fromtimestamp(ts, tz=kst).strftime("%H:%M:%S")]

        for val in row_values:
            if isinstance(val, float):
                values.append(f"{val:.3f}")
            elif val is None:
                values.append("null")
            else:
                values.append(str(val))

        lines.append("|".join(values))

    return "\n".join(lines)


def load_system_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_user_prompt_interval(metric_llm_input: str, log_llm_input: str) -> str:
    return f"""Analyze the following information.

METRIC_INPUT_START
{metric_llm_input}
METRIC_INPUT_END

LOG_INPUT_START
{log_llm_input}
LOG_INPUT_END
"""

def build_user_prompt_daily(llm_input: str) -> str:
    return f"""
Analyze the following daily events and generate a report.

{llm_input}
"""

def build_chat_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_time(t: str) -> datetime:
    return datetime.strptime(t, "%H:%M:%S")


def load_and_filter_reports(
    date_str: str,
    root_path: str = "./data/report/interval",
    exclude_low: bool = True,
) -> List[Dict[str, Any]]:
    base_path = f"{root_path}/{date_str.split("-")[0]}/{date_str.split("-")[1]}/{date_str.split("-")[2]}"
    json_files = glob.glob(f"{base_path}/*.json")

    data_list: List[Dict[str, Any]] = []

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data_list.append(data)
        except Exception as e:
            print(f"읽기 실패: {file_path} → {e}")

    filtered: List[Dict[str, Any]] = []

    for item in data_list:
        try:
            level = item.get("level")
            time_window = item.get("timeWindow", {})
            start_time = time_window.get("start")

            if not start_time:
                continue

            if exclude_low and level == "low":
                continue

            filtered.append(
                {
                    "level": level,
                    "summary": item.get("summary"),
                    "start": start_time,
                    "end": time_window.get("end"),
                    "events": item.get("events", []),
                }
            )
        except Exception as e:
            print(f"파싱 실패: {e}")

    filtered_sorted = sorted(filtered, key=lambda x: parse_time(x["start"]))
    return filtered_sorted


def build_llm_input(data):
    lines = []

    for item in data:
        line = (
            f"[{item['start']} ~ {item['end']}] "
            f"level={item['level']} | "
            f"{item['summary']}"
        )
        lines.append(line)

        # 이벤트도 포함 (있으면)
        for ev in item.get("events", []):
            ev_line = (
                f"  - ({ev.get('start_time')} ~ {ev.get('end_time')}) "
                f"{ev.get('summary')}"
            )
            lines.append(ev_line)

    return "\n".join(lines)