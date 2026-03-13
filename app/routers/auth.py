from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.connect import get_db
from app.schemas.auth import ConnectRequest
from app.schemas.base import APIResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/connect", response_model=APIResponse)
async def connect_user(
    payload: ConnectRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    try:

        user = AuthService.authenticate_user(
            db,
            payload.email,
            payload.password
        )

        if not user:
            user = AuthService.create_user(
                db,
                payload.email,
                payload.password
            )

        token = AuthService.generate_token(user)
        response.set_cookie(
                key="session",
                value=token,
                httponly=True,
                secure=True,
                samesite="none",
                max_age=86400
            )
        return APIResponse(
            success=True,
            message="Connected!",
            data={
                "token": token,
                "email": user.email,
                "id": str(user.id)
            }
        )

    except HTTPException as e:
        raise e

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Authentication service unavailable"
        )