from .bugs import router as bugs_router
from .health import router as health_router
from .metrics import router as metrics_router
from .triage import router as triage_router

__all__ = [
	"bugs_router",
	"health_router",
	"metrics_router",
	"triage_router",
]
