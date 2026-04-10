from app.services.admin import AdminService
from sqlalchemy.orm import Session
from app.database.models import User
from app.database.connect import get_db
from app.schemas.base import APIResponse
from app.dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/verify", response_model=APIResponse)
async def is_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  
    return APIResponse(
        success=True,
        message="Admin data retrieved successfully",
        data=current_user.email == "mrdhruv.professional@gmail.com"
    )

@router.get("/", response_model=APIResponse)
async def get_admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if not current_user.email == "mrdhruv.professional@gmail.com":
            raise HTTPException(
                status_code=403,
                detail="Unauthorized"
            )

        data = AdminService.get_admin_dashboard_data(db)

        return APIResponse(
            success=True,
            message="Admin data retrieved successfully",
            data=data
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve admin data"
        )
