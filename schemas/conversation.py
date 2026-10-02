from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ConversationCreate(BaseModel):
    title: str = Field("새 대화", min_length=1, max_length=100)
    messages: list[Message] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[Message]