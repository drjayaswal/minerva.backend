from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.models import User
from app.utility.hashing import hash_password, verify_password
from app.core.security import create_access_token


class AuthService:

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        try:
            user = db.query(User).filter(User.email == email).first()

            if not user:
                return None

            if not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect password"
                )

            return user

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Authentication failed"
            )


    @staticmethod
    def create_user(db: Session, email: str, password: str):
        try:

            existing_user = db.query(User).filter(User.email == email).first()

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User already exists"
                )

            new_user = User(
                email=email,
                hashed_password=hash_password(password)
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return new_user

        except HTTPException:
            raise

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to create user"
            )


    @staticmethod
    def generate_token(user):
        try:
            return create_access_token({
                "sub": user.email
            })

        except Exception:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate token"
            )