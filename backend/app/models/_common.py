from datetime import UTC, datetime


def utcnow() -> datetime:
    """作成日時などの既定値。DB には UTC で保存する。"""
    return datetime.now(UTC)
