from pydantic import Field
from typing import Literal
from pydantic import BaseModel
class ChatMessage(BaseModel):
    """历史消息：用户/助手"""
    role: Literal["user","assistant"]
    content: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=1,description="用户问题")
    history: list[ChatMessage] = Field(default_factory=list)