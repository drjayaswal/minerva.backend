from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    is_active: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIKeyFullResponse(APIKeyResponse):
    key: str

class APIKeyChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[UUID] = None
