from datetime import date as _date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _check_date(v: str) -> str:
    try:
        _date.fromisoformat(v)
    except ValueError:
        raise ValueError("date는 YYYY-MM-DD 형식의 실제 날짜여야 합니다.")
    return v


class DataCreate(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2024-12-31"])
    value: float = Field(..., ge=-60, le=60, description="평균기온(°C)")
    memo: str = Field("", max_length=200, description="메모")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return _check_date(v)


class DataUpdate(BaseModel):
    date: Optional[str] = None
    value: Optional[float] = Field(None, ge=-60, le=60)
    memo: Optional[str] = Field(None, max_length=200)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        return _check_date(v) if v is not None else v


class DataOut(DataCreate):
    id: str