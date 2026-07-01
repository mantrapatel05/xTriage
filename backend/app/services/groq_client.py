import random
import threading
import time
from dataclasses import dataclass

from groq import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Groq,
    GroqError,
    PermissionDeniedError,
    RateLimitError,
)
from backend.app.config import get_settings

class GroqClientUnavailable(RuntimeError):
    """Raised when every configured Groq key is unavailable or exhausted."""

@dataclass
class _ClientSlot:
    client: Groq
    cooldown_until: float = 0.0
    disabled: bool = False


class GroqClientPool:
    """Thread-safe Groq client pool with shared key rotation and cooldowns."""
    def __init__(self):
        settings = get_settings()
        keys = settings.groq_api_keys
        if not keys:
            raise ValueError("No GROQ_API_KEY, GROQ_API_KEYS, or GROQ_API_KEY_1..5 found in .env")

        self._slots = [_ClientSlot(client=Groq(api_key=key)) for key in keys]
        self._lock = threading.Lock()
        self._next_index = 0
        self._max_cooldown = settings.groq_max_cooldown_wait_seconds

    @property
    def key_count(self) -> int:
        return len(self._slots)

    def _next_slot(self) -> tuple[int, _ClientSlot, float]:
        """Return the next available slot, or the soonest cooldown wait."""
        with self._lock:
            now = time.monotonic()
            soonest_cooldown: float | None = None

            for offset in range(len(self._slots)):
                index = (self._next_index + offset) % len(self._slots)
                slot = self._slots[index]
                if slot.disabled:
                    continue
                if slot.cooldown_until <= now:
                    self._next_index = (index + 1) % len(self._slots)
                    return index, slot, 0.0
                soonest_cooldown = (
                    slot.cooldown_until
                    if soonest_cooldown is None
                    else min(soonest_cooldown, slot.cooldown_until)
                )

            if soonest_cooldown is None:
                raise GroqClientUnavailable("All configured Groq API keys are invalid or forbidden.")

            return -1, self._slots[0], max(soonest_cooldown - now, 0.25)

    def _cooldown(self, index: int, seconds: float) -> None:
        if index < 0:
            return
        with self._lock:
            self._slots[index].cooldown_until = max(
                self._slots[index].cooldown_until,
                time.monotonic() + seconds,
            )

    def _disable(self, index: int) -> None:
        if index < 0:
            return
        with self._lock:
            self._slots[index].disabled = True

    def _retry_after_seconds(self, error: RateLimitError) -> float:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", {}) or {}
        retry_after = headers.get("retry-after") or headers.get("Retry-After")

        if retry_after:
            try:
                return max(float(retry_after), 1.0)
            except ValueError:
                pass

        return 60.0

    def chat_completions_create(self, **kwargs):
        """
        Call Groq chat completions through one shared key pool.

        Rate-limited keys are cooled down and skipped, transient failures rotate
        to another key, and invalid keys are disabled for the current process.
        """
        max_attempts = max(12, self.key_count * 4)
        last_error = None

        for attempt in range(max_attempts):
            index, slot, wait_seconds = self._next_slot()
            if wait_seconds > 0:
                if wait_seconds > self._max_cooldown:
                    raise GroqClientUnavailable(
                        f"All Groq keys need {wait_seconds:.0f}s cooldown (daily quota likely exhausted). "
                        f"Max wait is {self._max_cooldown}s. Try again later or add keys from a different Groq org."
                    ) from last_error
                sleep_seconds = min(wait_seconds + random.uniform(0, 0.25), 30.0)
                print(f"  [GroqClient] All keys cooling down; waiting {sleep_seconds:.1f}s...")
                time.sleep(sleep_seconds)
                continue

            try:
                return slot.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                last_error = e
                cooldown = self._retry_after_seconds(e)
                if cooldown > self._max_cooldown:
                    print(f"  [GroqClient] Key {index + 1} needs {cooldown:.0f}s cooldown (daily quota hit). Failing fast.")
                    raise GroqClientUnavailable(
                        f"Groq daily token quota exhausted. Retry-After: {cooldown:.0f}s. "
                        f"Add a key from a different Groq org or wait for quota reset."
                    ) from e
                self._cooldown(index, cooldown)
                print(f"  [GroqClient] Key {index + 1} rate limited; cooling for {cooldown:.0f}s and rotating...")
                continue
            except (AuthenticationError, PermissionDeniedError) as e:
                last_error = e
                self._disable(index)
                print(f"  [GroqClient] Key {index + 1} rejected by Groq; disabling it for this process...")
                continue
            except BadRequestError:
                raise
            except (APIConnectionError, APITimeoutError, APIStatusError, APIError, GroqError) as e:
                last_error = e
                backoff = min(2 ** min(attempt, 4), 16) + random.uniform(0, 0.5)
                self._cooldown(index, backoff)
                print(f"  [GroqClient] Key {index + 1} transient error; rotating after {backoff:.1f}s cooldown...")
                continue

        raise GroqClientUnavailable(
            f"Groq API unavailable after {max_attempts} attempts across {self.key_count} key(s). "
            f"Last error: {last_error}"
        ) from last_error


_shared_pool: GroqClientPool | None = None
_shared_pool_lock = threading.Lock()


def get_groq_client() -> GroqClientPool:
    global _shared_pool
    with _shared_pool_lock:
        if _shared_pool is None:
            _shared_pool = GroqClientPool()
        return _shared_pool


GroqClient = GroqClientPool
