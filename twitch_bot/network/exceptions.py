from twitch_bot.exceptions import BotError

__all__ = ("CogExistsError", "CogNotFound", "RequestError", "HTTPError")


class CogExistsError(BotError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Cog {name} already exists")


class CogNotFound(BotError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Cog {name} doesn't exist")


class RequestError(BotError):
    def __init__(self, message: str = "Failed to create request") -> None:
        super().__init__(message)


class HTTPError(RequestError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = code
