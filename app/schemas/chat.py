from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    prompt: str


class ConversationRequest(BaseModel):
    title: Optional[str] = None
    id: Optional[str] = None


class MessageResponse(BaseModel):
    id: Optional[str]
    role: str
    content: str
    created_at: Optional[datetime]


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[datetime]
    messages: List[MessageResponse] = []