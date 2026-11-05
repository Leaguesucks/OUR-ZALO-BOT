"""Minimal documented event fields. Unknown fields are accepted for forward compatibility."""

from pydantic import BaseModel, Field


class Chat(BaseModel):
    id: str


class Sender(BaseModel):
    id: str
    is_bot: bool = False


class Message(BaseModel):
    message_id: str
    chat: Chat
    sender: Sender | None = Field(default=None, alias="from")
    text: str | None = None


class Update(BaseModel):
    event_name: str
    message: Message | None = None
