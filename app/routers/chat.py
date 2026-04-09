from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connect import get_db
from app.schemas.chat import ChatRequest, ConversationRequest
from app.schemas.base import APIResponse
from app.dependencies.auth import get_current_user
from app.database.models import User
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/{conversation_id}", response_model=APIResponse)
async def chat(
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        response = await ChatService.process_chat(
            db,
            conversation_id,
            payload.prompt,
            current_user
        )

        return APIResponse(
            success=True,
            message="Response generated successfully",
            data={"response": response}
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        print("CHAT ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Chat service unavailable"
        )


@router.get("/conversations", response_model=APIResponse)
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        conversations = ChatService.get_conversations(
            db,
            current_user
        )

        return APIResponse(
            success=True,
            message="Conversations fetched",
            data={"conversations": conversations}
        )

    except Exception as e:
        print("CONVERSATION ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch conversations"
        )


@router.get("/{conversation_id}/messages", response_model=APIResponse)
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        messages = ChatService.get_messages(
            db,
            conversation_id,
            current_user
        )

        return APIResponse(
            success=True,
            message="Messages fetched",
            data={"messages": messages}
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        print("MESSAGE ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch messages"
        )


@router.post("/conversations/new", response_model=APIResponse)
async def create_conversation(
    payload: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        conversation = ChatService.create_conversation(
            db,
            payload.title,
            current_user
        )

        return APIResponse(
            success=True,
            message="Conversation created",
            data={"conversation": conversation}
        )

    except Exception as e:
        print("CREATE CONVERSATION ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation"
        )

@router.post("/conversations/delete", response_model=APIResponse)
async def delete_conversation(
    payload: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        conversation = ChatService.delete_conversation(
            db,
            payload.id,
            current_user
        )

        return APIResponse(
            success=True,
            message="Conversation deleted",
            data={"conversation": conversation}
        )

    except Exception as e:
        print("DELETE CONVERSATION ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation"
        )