import logging
from typing import Optional

from google.api_core.exceptions import GoogleAPICallError

from services import ai_service, conversation_service, data_service

logger = logging.getLogger(__name__)


def chat(message: str, conversation_id: Optional[str] = None) -> dict:
    # 이어서 대화하는 경우: 이전 메시지 불러오기 (없는 id면 NotFound 발생)
    history = []
    if conversation_id:
        conv = conversation_service.get_conversation(conversation_id)
        history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"]]

    # 1) 데이터 요약 조회 -> 2) 시스템 프롬프트 삽입 -> 3) Gemini 호출
    summary = data_service.get_summary()
    reply = ai_service.generate_reply(summary, history, message)

    # 4) 대화 자동 저장 (실패해도 답변은 돌려준다)
    new_messages = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    saved = True
    try:
        if conversation_id:
            conversation_service.append_messages(conversation_id, new_messages)
        else:
            created = conversation_service.create_conversation("새 대화", new_messages)
            conversation_id = created["id"]
    except GoogleAPICallError:
        logger.exception("대화 저장 실패")
        saved = False

    return {"reply": reply, "conversation_id": conversation_id, "saved": saved}