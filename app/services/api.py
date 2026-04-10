import secrets
import hashlib
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.models import APIKey, User, Conversation
from app.schemas.api import APIKeyCreate, APIKeyResponse
from app.services.chat import ChatService
from uuid import UUID

logger = logging.getLogger(__name__)

class APIService:
    
    @staticmethod
    def generate_key_string() -> str:
        """Generates a secure random API key string."""
        return f"min_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hashes the API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def create_api_key(db: Session, user_id: UUID, data: APIKeyCreate):
        """Generates and stores a new API key."""
        try:
            raw_key = APIService.generate_key_string()
            hashed_key = APIService.hash_key(raw_key)
            prefix = raw_key[:8] # sk_...

            new_key = APIKey(
                user_id=user_id,
                name=data.name,
                prefix=prefix,
                hashed_key=hashed_key,
                is_active="active"
            )

            db.add(new_key)
            db.commit()
            db.refresh(new_key)

            return {
                "id": new_key.id,
                "name": new_key.name,
                "prefix": new_key.prefix,
                "is_active": new_key.is_active,
                "created_at": new_key.created_at,
                "key": raw_key # Return raw key only once
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate API key")

    @staticmethod
    def list_api_keys(db: Session, user_id: UUID):
        """Lists all keys for a user (masked)."""
        try:
            keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
            return keys
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve API keys")

    @staticmethod
    def delete_api_key(db: Session, user_id: UUID, key_id: UUID):
        """Permanently deletes an API key."""
        try:
            key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
            if not key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            db.delete(key)
            db.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete API key")

    @staticmethod
    def block_api_key(db: Session, user_id: UUID, key_id: UUID):
        """Blacklists an API key."""
        try:
            key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
            if not key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            key.is_active = "blocked"
            db.commit()
            return key
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error blocking API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to block API key")

    @staticmethod
    def verify_api_key(db: Session, raw_key: str):
        """Verifies an API key and returns the associated user."""
        try:
            hashed_key = APIService.hash_key(raw_key)
            key_record = db.query(APIKey).filter(APIKey.hashed_key == hashed_key).first()
            
            if not key_record:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            if key_record.is_active != "active":
                raise HTTPException(status_code=403, detail="API key is blocked or inactive")
            
            # Update last used
            key_record.last_used_at = datetime.now()
            db.commit()
            
            return key_record.user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            raise HTTPException(status_code=500, detail="API authentication error")
