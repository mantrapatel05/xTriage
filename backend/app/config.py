from dataclasses import dataclass
from functools import lru_cache
import os


def _parse_bool(value: str | None, default: bool = False) -> bool:
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
	if not value:
		return default
	items = tuple(item.strip() for item in value.split(",") if item.strip())
	return items or default


@dataclass(frozen=True)
class Settings:
	app_name: str = "Bug Triage Agent"
	app_version: str = "0.1.0"
	environment: str = "development"
	debug: bool = False
	log_level: str = "INFO"
	cors_origins: tuple[str, ...] = ("http://localhost:5173",)
	gemini_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings(
		app_name=os.getenv("APP_NAME", "Bug Triage Agent"),
		app_version=os.getenv("APP_VERSION", "0.1.0"),
		environment=os.getenv("APP_ENV", "development"),
		debug=_parse_bool(os.getenv("DEBUG"), default=False),
		log_level=os.getenv("LOG_LEVEL", "INFO"),
		cors_origins=_parse_csv(
			os.getenv("CORS_ORIGINS"),
			default=("http://localhost:5173",),
		),
		gemini_api_key=os.getenv("GEMINI_API_KEY"),
	)
