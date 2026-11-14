"""画像ファイルの保存・削除。

ローカルディスクに保存し、/uploads で静的配信する。ファイル名は推測不能な UUID。
本番ではこのモジュールをオブジェクトストレージ（S3 等）向けに差し替えればよい。
"""

import uuid
from pathlib import Path

from app.config import get_settings
from app.errors import PayloadTooLargeError, UnsupportedMediaTypeError

# 先頭バイト列（マジックナンバー）で判定する。Content-Type はクライアント申告なので信用しない。
_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
]


def detect_image_extension(data: bytes) -> str | None:
    for signature, ext in _SIGNATURES:
        if data.startswith(signature):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def upload_dir() -> Path:
    path = get_settings().upload_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(data: bytes) -> str:
    """検証して保存し、ファイル名を返す。"""
    if len(data) > get_settings().max_image_bytes:
        raise PayloadTooLargeError("Image is too large")
    ext = detect_image_extension(data)
    if ext is None:
        raise UnsupportedMediaTypeError("Only JPEG, PNG, GIF and WebP images are supported")
    filename = f"{uuid.uuid4().hex}{ext}"
    (upload_dir() / filename).write_bytes(data)
    return filename


def delete_image(filename: str) -> None:
    (upload_dir() / filename).unlink(missing_ok=True)
