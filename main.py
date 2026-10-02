from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.api_core.exceptions import GoogleAPICallError

import database  # noqa: F401  (앱 시작 시 Firebase 초기화)
from config import ALLOWED_ORIGINS
from routers import conversations, data

DESCRIPTION = """
서울 일별 기온 데이터를 저장·조회하고, 이 데이터를 바탕으로 대화하는 **AI 비서 API**입니다.

## 이 화면 사용법
1. 사용할 API를 클릭해 펼칩니다. (입력 칸은 이미 켜져 있습니다)
2. 값이 필요하면 **Request body 위의 Examples 드롭다운**에서 예시를 고르거나 직접 수정합니다.
3. **Execute**를 누르고, 아래 **Server response**의 코드와 Response body를 확인합니다.

## 응답 코드 읽는 법
| 코드 | 의미 |
|---|---|
| 200 / 201 | 성공 |
| 400 | 요청 내용이 비어 있음 |
| 404 | 해당 id의 데이터가 없음 |
| 409 | 같은 날짜의 데이터가 이미 있음 |
| 422 | 입력값 검증 실패 (형식·범위 오류) |
| 503 | 데이터베이스 연결 문제 |

## 추천 테스트 순서
`GET /api/data/summary` → `POST` (정상) → `POST` (중복) → `PUT` → `DELETE`
"""

app = FastAPI(
    title="서울 기온 AI 비서 API",
    description=DESCRIPTION,
    version="0.1.0",
    openapi_tags=[
        {"name": "data", "description": "기온 데이터 관리 (추가·조회·수정·삭제·요약)"},
    ],
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)


@app.exception_handler(GoogleAPICallError)
async def firestore_error_handler(request: Request, exc: GoogleAPICallError):
    return JSONResponse(
        status_code=503,
        content={"detail": "데이터베이스 요청에 실패했습니다. 잠시 후 다시 시도해 주세요."},
    )


@app.get("/", summary="서버 상태 확인")
def root():
    return {"status": "ok"}


@app.get("/health", summary="헬스 체크")
def health():
    return {"status": "healthy"}