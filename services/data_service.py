import time
from typing import Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from database import db
from services.analysis import compute_summary

COLLECTION = "data"
SUMMARY_TTL = 60  # 초

_summary_cache = {"value": None, "at": 0.0}


class DataNotFoundError(Exception):
    pass


class DuplicateDateError(Exception):
    pass


def _col():
    return db.collection(COLLECTION)


def _invalidate_cache():
    _summary_cache["value"] = None


def _date_exists(date: str, exclude_id: Optional[str] = None) -> bool:
    query = _col().where(filter=FieldFilter("date", "==", date)).limit(2)
    return any(doc.id != exclude_id for doc in query.stream())


def list_data(limit: int = 50, start_date: Optional[str] = None,
              end_date: Optional[str] = None) -> list[dict]:
    query = _col()
    if start_date:
        query = query.where(filter=FieldFilter("date", ">=", start_date))
    if end_date:
        query = query.where(filter=FieldFilter("date", "<=", end_date))
    query = query.order_by("date", direction=firestore.Query.DESCENDING).limit(limit)
    return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]


def create_data(data: dict) -> dict:
    if _date_exists(data["date"]):
        raise DuplicateDateError(f"{data['date']} 날짜의 데이터가 이미 있습니다.")
    _, ref = _col().add(data)
    _invalidate_cache()
    return {"id": ref.id, **data}


def update_data(doc_id: str, changes: dict) -> dict:
    ref = _col().document(doc_id)
    snap = ref.get()
    if not snap.exists:
        raise DataNotFoundError(f"id '{doc_id}' 데이터를 찾을 수 없습니다.")
    current = snap.to_dict()
    new_date = changes.get("date")
    if new_date and new_date != current["date"] and _date_exists(new_date, exclude_id=doc_id):
        raise DuplicateDateError(f"{new_date} 날짜의 데이터가 이미 있습니다.")
    ref.update(changes)
    _invalidate_cache()
    return {"id": doc_id, **current, **changes}


def delete_data(doc_id: str) -> None:
    ref = _col().document(doc_id)
    if not ref.get().exists:
        raise DataNotFoundError(f"id '{doc_id}' 데이터를 찾을 수 없습니다.")
    ref.delete()
    _invalidate_cache()


def get_summary() -> dict:
    now = time.monotonic()
    if _summary_cache["value"] is not None and now - _summary_cache["at"] < SUMMARY_TTL:
        return _summary_cache["value"]
    records = [
        {"date": d.get("date"), "value": d.get("value"), "memo": d.get("memo", "")}
        for d in (doc.to_dict() for doc in _col().stream())
    ]
    summary = compute_summary(records)
    _summary_cache["value"] = summary
    _summary_cache["at"] = now
    return summary