from exceptions import BotError

__all__ = ("UserNotFound",)


class UserNotFound(BotError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
