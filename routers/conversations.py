from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from schemas.conversation import ConversationCreate, ConversationOut, ConversationSummary
from services import conversation_service
from services.conversation_service import ConversationNotFoundError

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

ConvId = Annotated[str, Path(description="대화 id (저장 시 응답으로 받은 id)")]

CREATE_EXAMPLES = {
    "with_messages": {
        "summary": "✅ 메시지가 있는 대화 (제목 자동 생성)",
        "value": {
            "messages": [
                {"role": "user", "content": "가장 추웠던 날은 언제야?"},
                {"role": "assistant", "content": "2023년 1월 24일에 평균 -14.9°C로 가장 추웠어요."},
            ]
        },
    },
    "with_title": {
        "summary": "✅ 제목을 직접 지정",
        "value": {
            "title": "기온 질문 모음",
            "messages": [{"role": "user", "content": "여름 평균 기온 알려줘"}],
        },
    },
    "bad_role": {
        "summary": "❌ 잘못된 role (422)",
        "value": {"messages": [{"role": "admin", "content": "안녕"}]},
    },
}


@router.post(
    "",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
    summary="대화 저장",
    description="대화를 저장합니다. 제목을 생략하면 첫 사용자 메시지 앞 30자로 자동 생성됩니다.",
    responses={422: {"description": "입력값 검증 실패 (role, content 등)"}},
)
def create_conversation(
    payload: Annotated[ConversationCreate, Body(openapi_examples=CREATE_EXAMPLES)],
):
    return conversation_service.create_conversation(
        payload.title, [m.model_dump() for m in payload.messages]
    )


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="대화 목록 조회 (최신순)",
    description="메시지 본문은 포함하지 않고 id, 제목, 생성 시각, 메시지 개수만 돌려줍니다. 본문은 상세 조회를 사용하세요.",
)
def list_conversations(limit: int = Query(50, ge=1, le=1000, description="가져올 개수")):
    return conversation_service.list_conversations(limit)


@router.get(
    "/{conv_id}",
    response_model=ConversationOut,
    summary="대화 불러오기 (전체 메시지 포함)",
    responses={404: {"description": "해당 id의 대화가 없음"}},
)
def get_conversation(conv_id: ConvId):
    try:
        return conversation_service.get_conversation(conv_id)
    except ConversationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{conv_id}",
    summary="대화 삭제",
    responses={404: {"description": "해당 id의 대화가 없음"}},
)
def delete_conversation(conv_id: ConvId):
    try:
        conversation_service.delete_conversation(conv_id)
    except ConversationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"deleted": conv_id}