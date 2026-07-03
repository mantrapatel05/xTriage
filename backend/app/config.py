from dataclasses import dataclass
from functools import lru_cache
import os


def parse_bool(value: str | None, default: bool = False) -> bool:
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
	if not value:
		return default
	items = tuple(item.strip() for item in value.split(",") if item.strip())
	return items or default


def parse_int(value: str | None, default: int) -> int:
	if value is None:
		return default
	try:
		return int(value.strip())
	except ValueError:
		return default


def unique(values: list[str]) -> tuple[str, ...]:
	seen: set[str] = set()
	unique_values: list[str] = []
	for value in values:
		if value in seen:
			continue
		seen.add(value)
		unique_values.append(value)
	return tuple(unique_values)


@dataclass(frozen=True)
class Settings:
	app_name: str = "Bug Triage Agent"
	app_version: str = "0.1.0"
	environment: str = "development"
	debug: bool = False
	log_level: str = "INFO"
	cors_origins: tuple[str, ...] = (
		"http://localhost:5173",
		"http://127.0.0.1:5173",
		"http://localhost:5174",
		"http://127.0.0.1:5174",
		"http://localhost:3000",
	)
	groq_api_keys: tuple[str, ...] = ()
	groq_multi_api_keys: tuple[str, ...] = ()
	groq_single_api_keys: tuple[str, ...] = ()
	groq_model: str = "llama-3.1-8b-instant"
	groq_max_completion_tokens: int = 220
	groq_prompt_description_chars: int = 2500
	groq_max_cooldown_wait_seconds: int = 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	keys = []
	for i in range(1, 6):
		key = os.getenv(f"GROQ_API_KEY_{i}")
		if key:
			keys.append(key.strip())
	for key in parse_csv(os.getenv("GROQ_API_KEYS"), default=()):
		keys.append(key)
	# fallback to single GROQ_API_KEY if numbered ones aren't set
	if not keys:
		single = os.getenv("GROQ_API_KEY")
		if single:
			keys.append(single.strip())
	all_keys = unique(keys)

	multi_keys = parse_csv(os.getenv("GROQ_MULTI_API_KEYS"), default=())
	if not multi_keys:
		multi_keys = all_keys[:3] if len(all_keys) >= 3 else all_keys

	single_keys = parse_csv(os.getenv("GROQ_SINGLE_API_KEYS"), default=())
	if not single_keys:
		single_keys = all_keys[-2:] if len(all_keys) >= 2 else all_keys

	return Settings(
		app_name=os.getenv("APP_NAME", "Bug Triage Agent"),
		app_version=os.getenv("APP_VERSION", "0.1.0"),
		environment=os.getenv("APP_ENV", "development"),
		debug=parse_bool(os.getenv("DEBUG"), default=False),
		log_level=os.getenv("LOG_LEVEL", "INFO"),
		cors_origins=parse_csv(
			os.getenv("CORS_ORIGINS"),
			default=(
				"http://localhost:5173",
				"http://127.0.0.1:5173",
				"http://localhost:5174",
				"http://127.0.0.1:5174",
				"http://localhost:3000",
			),
		),
		groq_api_keys=all_keys,
		groq_multi_api_keys=unique(list(multi_keys)),
		groq_single_api_keys=unique(list(single_keys)),
		groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
		groq_max_completion_tokens=parse_int(os.getenv("GROQ_MAX_COMPLETION_TOKENS"), 220),
		groq_prompt_description_chars=parse_int(os.getenv("GROQ_PROMPT_DESCRIPTION_CHARS"), 2500),
		groq_max_cooldown_wait_seconds=parse_int(os.getenv("GROQ_MAX_COOLDOWN_WAIT_SECONDS"), 20),
	)
