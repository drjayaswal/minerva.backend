from fastapi import APIRouter
from app.schemas.base import APIResponse

router = APIRouter(prefix="/health", tags=["Chat"])

@router.get("/", response_model=APIResponse)
async def get_health_status():
        return APIResponse(
            success=True,
            message="Minerva Healthy!",
            data=None
        )