from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS
import database  # noqa: F401  (앱 시작 시 Firebase 초기화)

app = FastAPI(title="서울 기온 AI 비서 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}