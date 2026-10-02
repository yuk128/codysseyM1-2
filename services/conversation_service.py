from datetime import datetime, timezone

from google.cloud import firestore

from database import db

COLLECTION = "conversations"
DEFAULT_TITLE = "새 대화"


class ConversationNotFoundError(Exception):
    pass


def _col():
    return db.collection(COLLECTION)


def _make_title(title: str, messages: list[dict]) -> str:
    if title != DEFAULT_TITLE:
        return title
    for m in messages:
        if m["role"] == "user":
            text = " ".join(m["content"].split())
            return text[:30] + ("…" if len(text) > 30 else "")
    return title


def create_conversation(title: str, messages: list[dict]) -> dict:
    doc = {
        "title": _make_title(title, messages),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages,
        "message_count": len(messages),
    }
    _, ref = _col().add(doc)
    return {"id": ref.id, **doc}


def list_conversations(limit: int = 50) -> list[dict]:
    query = (
        _col()
        .select(["title", "created_at", "message_count"])
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [{"id": d.id, **d.to_dict()} for d in query.stream()]


def get_conversation(conv_id: str) -> dict:
    snap = _col().document(conv_id).get()
    if not snap.exists:
        raise ConversationNotFoundError(f"id '{conv_id}' 대화를 찾을 수 없습니다.")
    data = snap.to_dict()
    data.setdefault("messages", [])
    return {"id": snap.id, **data}


def delete_conversation(conv_id: str) -> None:
    ref = _col().document(conv_id)
    if not ref.get().exists:
        raise ConversationNotFoundError(f"id '{conv_id}' 대화를 찾을 수 없습니다.")
    ref.delete()

def append_messages(conv_id: str, new_messages: list[dict]) -> int:
    ref = _col().document(conv_id)
    snap = ref.get()
    if not snap.exists:
        raise ConversationNotFoundError(f"id '{conv_id}' 대화를 찾을 수 없습니다.")
    messages = snap.to_dict().get("messages", []) + new_messages
    ref.update({"messages": messages, "message_count": len(messages)})
    return len(messages)