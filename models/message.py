from .user import Chatter
from dataclasses import dataclass


@dataclass(repr=True, slots=True)
class Message:
    id: str
    author: Chatter
    content: str
