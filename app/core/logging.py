import json, os
from typing import Dict

from app.core.config import LOG_DIR

def write_json_log(
    filename: str,
    data: Dict,
    log_type: str,
):
    dir_path = os.path.join(LOG_DIR, log_type)
    os.makedirs(dir_path, exist_ok=True)

    path = os.path.join(dir_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
