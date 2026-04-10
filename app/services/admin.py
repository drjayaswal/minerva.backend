from app.database.models import APIKey
from sqlalchemy import func
import logging
from sqlalchemy.orm import Session

from app.core.config import enviroment_variables
from app.database.models import Conversation, Message, User

logger = logging.getLogger(__name__)
envs = enviroment_variables()


class AdminService:

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

        all_keys = db.query(APIKey).all()
        key_data = [
            {
                "id": str(k.id),
                "user_id": str(k.user_id),
                "name": k.name,
                "prefix": k.prefix,
                "is_active": k.is_active,
                "created_at": k.created_at,
                "last_used_at": k.last_used_at
            }
            for k in all_keys
        ]

        total_messages = db.query(func.count(Message.id)).scalar()

        return {
            "users": user_data,
            "conversations": conversation_data,
            "stats": {
                "total_users": len(user_data),
                "total_conversations": len(conversation_data),
                "total_messages": total_messages
            },
            "keys": key_data,
            "keys_stats": {
                "total_keys": len(key_data),
            }
        }