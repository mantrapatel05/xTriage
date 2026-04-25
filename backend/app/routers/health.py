from fastapi import APIRouter

from backend.app.config import get_settings


router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
	settings = get_settings()
	return {
		"status": "ok",
		"service": settings.app_name,
		"environment": settings.environment,
		"version": settings.app_version,
	}
