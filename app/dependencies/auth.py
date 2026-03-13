from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.connect import get_db
from app.database.models import User
from app.core.security import decode_token


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):

    token = request.cookies.get("session")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(
        User.email == payload.get("sub")
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user