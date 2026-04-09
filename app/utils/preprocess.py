import httpx
from app.core.config import PREPROCESS_ERROR_URL

async def preprocess_error_async(index_name: str, date: str, filename: str) -> dict:
    payload = {
        "index_name": index_name,
        "date": date,
        "filename": filename,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(PREPROCESS_ERROR_URL, json=payload)

        # 디버깅용
        print(resp.status_code)
        print(resp.text)

        resp.raise_for_status()
        return resp.json()