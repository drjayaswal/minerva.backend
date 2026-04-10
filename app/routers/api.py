from sqlalchemy.orm import Session
from app.database.models import User
from app.database.connect import get_db
from app.schemas.base import APIResponse
from app.schemas.api import APIKeyCreate, APIKeyResponse, APIKeyChatRequest
from app.schemas.chat import ChatRequest, ConversationRequest
from app.services.api import APIService
from app.services.chat import ChatService
from app.dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Header, status
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["API Keys & External Access"])

async def get_api_key_user(
    x_api_key: str = Header(..., alias="X-API-Key", description="Professional API Key for external access"),
    db: Session = Depends(get_db)
):
    return APIService.verify_api_key(db, x_api_key)

@router.post("/keys", response_model=APIResponse)
async def generate_api_key(
    data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        new_key_data = APIService.create_api_key(db, current_user.id, data)
        return APIResponse(
            success=True,
            message="API Key generated successfully. Please store it securely as it won't be shown again.",
            data=new_key_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "Failed to generate API key"
        )

@router.get("/keys", response_model=APIResponse)
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        keys = APIService.list_api_keys(db, current_user.id)
        return APIResponse(
            success=True,
            message="API keys retrieved successfully",
            data=[APIKeyResponse.model_validate(k) for k in keys]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )

@router.delete("/keys/{key_id}", response_model=APIResponse)
async def delete_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        APIService.delete_api_key(db, current_user.id, key_id)
        return APIResponse(
            success=True,
            message="API Key revoked and deleted successfully",
            data={"id": str(key_id)}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the API key"
        )

@router.patch("/keys/{key_id}/block", response_model=APIResponse)
async def block_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        key = APIService.block_api_key(db, current_user.id, key_id)
        return APIResponse(
            success=True,
            message="API Key has been blocked",
            data=APIKeyResponse.model_validate(key)
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block API key"
        )

@router.post("/chat/v1", response_model=APIResponse)
async def chat_legacy(
    request: APIKeyChatRequest,
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        if not request.conversation_id:
            conv = ChatService.create_conversation(db, "API Integration Chat", api_user)
            conv_id = conv["id"]
        else:
            conv_id = str(request.conversation_id)

        response = await ChatService.process_chat(
            db,
            conv_id,
            request.prompt,
            api_user
        )

        return APIResponse(
            success=True,
            message="Chat completed successfully",
            data={
                "response": response,
                "conversation_id": conv_id
            }
        )
    except Exception as e:
        logger.error(f"External API Chat Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) or "Chat processing failed"
        )

@router.post("/chat/{conversation_id}", response_model=APIResponse)
async def chat_via_api_key(
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        response = await ChatService.process_chat(
            db,
            conversation_id,
            payload.prompt,
            api_user
        )

        return APIResponse(
            success=True,
            message="Response generated successfully",
            data={"response": response}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"API Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Chat service unavailable")

@router.get("/chat/conversations", response_model=APIResponse)
async def get_api_conversations(
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        conversations = ChatService.get_conversations(db, api_user)
        return APIResponse(
            success=True,
            message="Conversations fetched",
            data={"conversations": conversations}
        )
    except Exception as e:
        logger.error(f"API Conversation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@router.get("/chat/{conversation_id}/messages", response_model=APIResponse)
async def get_api_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        messages = ChatService.get_messages(db, conversation_id, api_user)
        return APIResponse(
            success=True,
            message="Messages fetched",
            data={"messages": messages}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"API Message Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.post("/chat/conversations/new", response_model=APIResponse)
async def create_api_conversation(
    payload: ConversationRequest,
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        conversation = ChatService.create_conversation(db, payload.title or "New API Chat", api_user)
        return APIResponse(
            success=True,
            message="Conversation created",
            data={"conversation": conversation}
        )
    except Exception as e:
        logger.error(f"API Create Conversation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@router.post("/chat/conversations/delete", response_model=APIResponse)
async def delete_api_conversation(
    payload: ConversationRequest,
    db: Session = Depends(get_db),
    api_user: User = Depends(get_api_key_user)
):
    try:
        result = ChatService.delete_conversation(db, payload.id, api_user)
        return APIResponse(
            success=True,
            message="Conversation deleted",
            data={"conversation": result}
        )
    except Exception as e:
        logger.error(f"API Delete Conversation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


