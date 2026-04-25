from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.routers.bugs import router as bugs_router
from backend.app.routers.health import router as health_router
from backend.app.routers.metrics import router as metrics_router
from backend.app.routers.triage import router as triage_router
from backend.app.utils.logger import configure_logging, logger


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
	app.state.started_at = datetime.now(timezone.utc)
	logger.info("starting %s", settings.app_name)
	yield
	logger.info("stopping %s", settings.app_name)


app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
	debug=settings.debug,
	lifespan=lifespan,
)

app.state.settings = settings

if settings.cors_origins:
	app.add_middleware(
		CORSMiddleware,
		allow_origins=list(settings.cors_origins),
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

app.include_router(health_router)
app.include_router(triage_router)
app.include_router(bugs_router)
app.include_router(metrics_router)


@app.get("/")
async def root() -> dict[str, str]:
	return {"message": "Bug Triage Agent API", "status": "ready"}
