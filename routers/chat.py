from typing import Annotated

from fastapi import APIRouter, Body, HTTPException

from schemas.chat import ChatRequest, ChatResponse
from services import chat_service
from services.ai_service import AIServiceError
from services.conversation_service import ConversationNotFoundError

router = APIRouter(prefix="/api/chat", tags=["chat"])

EXAMPLES = {
    "new": {
        "summary": "✅ 새 대화 시작",
        "description": "conversation_id를 생략하면 새 대화가 만들어지고 자동 저장됩니다.",
        "value": {"message": "가장 추웠던 날은 언제였어?"},
    },
    "follow_up": {
        "summary": "✅ 이어서 대화 (id 필요)",
        "description": "이전 응답의 conversation_id를 아래에 붙여 넣으세요.",
        "value": {"message": "그럼 가장 더웠던 날은?", "conversation_id": "여기에_이전_응답의_conversation_id"},
    },
    "empty": {
        "summary": "❌ 빈 메시지 (422)",
        "value": {"message": "   "},
    },
}


@router.post(
    "",
    response_model=ChatResponse,
    summary="AI 비서와 대화 (데이터 요약 반영)",
    description=(
        "저장된 기온 데이터의 요약을 시스템 프롬프트에 넣고 Gemini에게 질문합니다. "
        "대화는 자동 저장되며, 응답의 `conversation_id`로 이어서 대화할 수 있습니다.\n\n"
        "※ AI 호출은 몇 초 걸릴 수 있습니다."
    ),
    responses={
        404: {"description": "conversation_id에 해당하는 대화가 없음"},
        422: {"description": "메시지가 비어 있거나 너무 김"},
        429: {"description": "AI 무료 사용 한도 초과"},
        502: {"description": "AI 서버 오류 또는 빈 응답"},
    },
)
def chat(payload: Annotated[ChatRequest, Body(openapi_examples=EXAMPLES)]):
    try:
        return chat_service.chat(payload.message, payload.conversation_id)
    except ConversationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AIServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)