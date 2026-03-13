import asyncio
import logging
from sqlalchemy.orm import Session
from huggingface_hub import InferenceClient

from app.core.config import enviroment_variables
from app.database.models import Conversation, Message, User

logger = logging.getLogger(__name__)
envs = enviroment_variables()


class ChatService:

    client = InferenceClient(token=envs.HF_ACCESS_TOKEN)
    model = "meta-llama/Llama-3.1-8B-Instruct"

    # ---------------- AI RESPONSE ---------------- #

    @staticmethod
    async def generate_response(messages):

        system_prompt = {
            "role": "system",
            "content": "You are Minerva, a professional, concise AI."
            "Follow these constraints:"
            "1. Direct Answers: Start immediately with the solution."
            "2. Structure: Use bullet points and bolding for clarity."
            "3. Tone: Objective, precise, and authoritative."
            "4. Length: Keep responses under 100 tokens."
            "5. Formatting: Avoid pleasantries and intros."
        }

        formatted_messages = [system_prompt] + [
            {
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                "content": m.content
            }
            for m in messages
        ]

        return await asyncio.to_thread(
            ChatService._call_model,
            formatted_messages
        )
    
    @staticmethod
    def _call_model(messages):

        try:

            response = ChatService.client.chat_completion(
                model=ChatService.model,
                messages=messages,
                max_tokens=100
            )

            return response.choices[0].message.content

        except Exception as e:

            logger.error(f"AI Error: {e}")

            return "AI service unavailable."

    # ---------------- CHAT PROCESS ---------------- #

    @staticmethod
    async def process_chat(
        db: Session,
        conversation_id: str,
        prompt: str,
        user: User
    ):

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )

        if not conversation:
            raise Exception("Conversation not found")

        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=prompt
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

        ai_response = await ChatService.generate_response(messages)

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response
        )

        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ai_response

    # ---------------- CONVERSATIONS ---------------- #

    @staticmethod
    def get_conversations(db: Session, user: User):

        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
            .all()
        )

        return [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": c.created_at
            }
            for c in conversations
        ]

    # ---------------- MESSAGES ---------------- #

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: str,
        user: User
    ):

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )

        if not conversation:
            raise Exception("Conversation not found")

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at
            }
            for m in messages
        ]

    # ---------------- CREATE CONVERSATION ---------------- #

    @staticmethod
    def create_conversation(
        db: Session,
        title: str,
        user: User
    ):

        conversation = Conversation(
            title=title,
            user_id=user.id
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "created_at": conversation.created_at
        }