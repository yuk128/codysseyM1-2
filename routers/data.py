from typing import Annotated, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from schemas.data import DataCreate, DataOut, DataUpdate
from services import data_service
from services.data_service import DataNotFoundError, DuplicateDateError

router = APIRouter(prefix="/api/data", tags=["data"])

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

DocId = Annotated[
    str,
    Path(
        description=(
            "수정/삭제할 데이터의 id. "
            "POST로 새로 만든 데이터는 응답의 id 값을, "
            "처음 업로드한 기존 데이터는 날짜(예: 2024-12-31)가 id입니다."
        ),
        examples=["2024-12-31"],
    ),
]

CREATE_EXAMPLES = {
    "normal": {
        "summary": "✅ 정상 예시 (201 Created)",
        "description": "아직 없는 날짜라서 정상적으로 추가됩니다.",
        "value": {"date": "2025-01-01", "value": -3.2, "memo": "테스트"},
    },
    "duplicate": {
        "summary": "⚠️ 이미 있는 날짜 (409 Conflict)",
        "description": "2024-12-31은 이미 들어 있는 날짜라서 거절됩니다.",
        "value": {"date": "2024-12-31", "value": 1.0, "memo": "중복 테스트"},
    },
    "out_of_range": {
        "summary": "❌ 값 범위 초과 (422 검증 실패)",
        "description": "기온은 -60 ~ 60 사이여야 하므로 999는 거절됩니다.",
        "value": {"date": "2025-01-02", "value": 999, "memo": "범위 테스트"},
    },
    "bad_date": {
        "summary": "❌ 날짜 형식 오류 (422 검증 실패)",
        "description": "실제로 존재하지 않는 날짜라서 거절됩니다.",
        "value": {"date": "2025-13-45", "value": 5.0, "memo": "날짜 테스트"},
    },
}

UPDATE_EXAMPLES = {
    "memo_only": {
        "summary": "✅ 메모만 수정",
        "value": {"memo": "수정됨"},
    },
    "value_and_memo": {
        "summary": "✅ 기온과 메모 수정",
        "value": {"value": -1.5, "memo": "값도 수정"},
    },
    "empty": {
        "summary": "❌ 빈 본문 (400)",
        "description": "바꿀 필드가 하나도 없으면 거절됩니다.",
        "value": {},
    },
}


@router.get(
    "/summary",
    summary="데이터 요약 조회",
    description=(
        "저장된 전체 데이터의 **기간, 개수, 평균/최고/최저, 최근 추세**를 계산해 돌려줍니다.\n\n"
        "AI 챗봇이 이 결과를 시스템 프롬프트에 넣어 대답합니다. "
        "(60초 동안 캐시되며, 데이터를 추가/수정/삭제하면 바로 갱신됩니다.)"
    ),
)
def get_summary():
    return data_service.get_summary()


@router.get(
    "",
    response_model=list[DataOut],
    summary="데이터 목록 조회 (최신순)",
    description=(
        "날짜 기준 **최신순**으로 데이터를 조회합니다.\n\n"
        "- `limit`: 가져올 개수 (기본 50, 최대 1000)\n"
        "- `start_date`, `end_date`: 기간 필터 (YYYY-MM-DD, 선택)"
    ),
)
def list_data(
    limit: int = Query(50, ge=1, le=1000, description="가져올 개수"),
    start_date: Optional[str] = Query(None, pattern=DATE_PATTERN, description="시작 날짜 (예: 2024-12-01)"),
    end_date: Optional[str] = Query(None, pattern=DATE_PATTERN, description="종료 날짜 (예: 2024-12-31)"),
):
    return data_service.list_data(limit, start_date, end_date)


@router.post(
    "",
    response_model=DataOut,
    status_code=status.HTTP_201_CREATED,
    summary="새 데이터 추가",
    description=(
        "새 기온 데이터를 한 건 추가합니다.\n\n"
        "**사용법:** 아래 Request body 위의 **Examples 드롭다운**에서 케이스를 고른 뒤 Execute를 누르세요. "
        "성공하면 응답의 `id`를 복사해 두었다가 수정/삭제에서 사용합니다."
    ),
    responses={
        409: {"description": "같은 날짜의 데이터가 이미 있음"},
        422: {"description": "입력값 검증 실패 (날짜 형식, 값 범위 등)"},
    },
)
def create_data(payload: Annotated[DataCreate, Body(openapi_examples=CREATE_EXAMPLES)]):
    try:
        return data_service.create_data(payload.model_dump())
    except DuplicateDateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/{doc_id}",
    response_model=DataOut,
    summary="데이터 수정",
    description=(
        "id에 해당하는 데이터를 수정합니다. **바꾸고 싶은 필드만** 보내면 됩니다.\n\n"
        "**사용법:** `doc_id`에 id를 붙여 넣고, Examples 드롭다운에서 예시를 고른 뒤 Execute."
    ),
    responses={
        400: {"description": "수정할 필드가 없음"},
        404: {"description": "해당 id의 데이터가 없음"},
        409: {"description": "바꾸려는 날짜가 이미 다른 데이터에 있음"},
    },
)
def update_data(
    doc_id: DocId,
    payload: Annotated[DataUpdate, Body(openapi_examples=UPDATE_EXAMPLES)],
):
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")
    try:
        return data_service.update_data(doc_id, changes)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateDateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete(
    "/{doc_id}",
    summary="데이터 삭제",
    description=(
        "id에 해당하는 데이터를 삭제합니다.\n\n"
        "**주의:** 되돌릴 수 없습니다. 테스트할 때는 직접 추가한 테스트 데이터의 id만 사용하세요."
    ),
    responses={404: {"description": "해당 id의 데이터가 없음"}},
)
def delete_data(doc_id: DocId):
    try:
        data_service.delete_data(doc_id)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"deleted": doc_id}