from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer, StringConstraints


def _to_utc_iso(value: datetime) -> str:
    # SQLite はタイムゾーン情報を保持しないため、UTC として明示して返す
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


# 日時は常に「タイムゾーン付きの ISO 8601（UTC）」で返す
UtcDatetime = Annotated[datetime, PlainSerializer(_to_utc_iso, return_type=str)]


# 入力文字列の制約：前後の空白を除去したうえで 1 文字以上・上限文字数以下
UserName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
RoomName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
MessageContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]


class ORMModel(BaseModel):
    """SQLAlchemy モデルから変換できるスキーマの基底クラス。"""

    model_config = ConfigDict(from_attributes=True)
