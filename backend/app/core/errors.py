"""ドメイン例外。

サービス層は HTTP を知らず、これらの例外を送出するだけにする。
HTTP ステータスへの変換は main.py の例外ハンドラで一括して行う。
"""


class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class UnauthorizedError(AppError):
    """ログインしていない・トークンが無効"""

    status_code = 401


class ForbiddenError(AppError):
    """権限がない（未参加のルーム・他人のメッセージなど）"""

    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    """一意であるべき値の重複（同名のルームなど）"""

    status_code = 409


class PayloadTooLargeError(AppError):
    status_code = 413


class UnsupportedMediaTypeError(AppError):
    status_code = 415
