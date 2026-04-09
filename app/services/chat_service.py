from sqlalchemy import func
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
            "content": """You are Minerva, a precise and authoritative AI assistant. Respond immediately with the core answer — no preambles, no pleasantries, no intros or outros.

        ## Markdown Formatting Rules

        Always structure responses using strict Markdown:

        - Use `###` headers to separate distinct sections
        - Wrap all technical identifiers, commands, variables, and code snippets in backticks
        - Use tables when presenting 3+ attributes or comparative data
        - Use `**bold**` for key terms or critical callouts
        - Use `---` as a divider between unrelated sections if needed

        ## Response Structure

        - Lead with the direct answer or result
        - Follow with supporting detail, breakdown, or steps only if necessary
        - End with a table or reference block if data is dense

        ## Constraints

        - Strict token limit: under 100 tokens per response
        - Objective, precise, and authoritative tone only
        - No conversational filler — every word must carry information
        - If a question is ambiguous, state the assumption made, then answer

        ## Output Format

        All responses must be valid Markdown renderable in a React frontend using `react-markdown` with `remark-gfm`. Never return plain prose when structure is possible."""
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

    # ---------------- DELETE CONVERSATION ---------------- #

    @staticmethod
    def delete_conversation(
        db: Session,
        conversation_id: str,
        user: User
    ):
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        ).first()

        if not conversation:
            return None

        db.delete(conversation)
        db.commit()

        return {
            "id": str(conversation_id),
            "message": "Deleted successfully"
        }

    # ---------------- ADMIN DASHBOARD ---------------- #

    @staticmethod
    def get_admin_dashboard_data(db: Session):
        users = db.query(User).all()
        
        user_data = []
        for user in users:
            user_data.append({
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at,
                "conversation_count": len(user.conversations)
            })

        all_conversations = db.query(Conversation).all()
        conversation_data = [
            {
                "id": str(c.id),
                "user_id": str(c.user_id),
                "title": c.title,
                "created_at": c.created_at,
                "message_count": db.query(Message).filter(Message.conversation_id == c.id).count()
            }
            for c in all_conversations
        ]

        total_messages = db.query(func.count(Message.id)).scalar()

        return {
            "users": user_data,
            "conversations": conversation_data,
            "stats": {
                "total_users": len(user_data),
                "total_conversations": len(conversation_data),
                "total_messages": total_messages
            }
        }