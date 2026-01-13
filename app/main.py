from fastapi import FastAPI
from app.api.analyze import router as analyze_router
from app.api.chat import router as chat_router
from app.middleware.ip_whitelist import ip_whitelist_middleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Woongjin Error Log Analyze API")

app.middleware("http")(ip_whitelist_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(chat_router)
