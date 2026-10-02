from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=1000, description="사용자 질문")
    conversation_id: Optional[str] = Field(
        None, description="이어서 대화할 대화 id (생략하면 새 대화가 만들어집니다)"
    )


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    saved: bool = True