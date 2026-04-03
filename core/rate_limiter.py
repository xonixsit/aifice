"""
Groq rate limiter — enforces requests-per-minute limits to avoid 429 errors.
Wraps the model so every agent call goes through the limiter automatically.

Groq free tier limits:
  llama-3.1-8b-instant    : 6000 RPM
  llama-3.3-70b-versatile : 30 RPM
  mixtral-8x7b-32768      : 30 RPM
"""
import time
import threading
from collections import deque
from loguru import logger

# Limits per model (requests per minute)
MODEL_RPM_LIMITS = {
    "llama-3.1-8b-instant":     6000,
    "llama-3.3-70b-versatile":  30,
    "mixtral-8x7b-32768":       30,
    "gemma2-9b-it":             30,
}
DEFAULT_RPM = 30  # safe fallback


class RateLimiter:
    def __init__(self, rpm: int):
        self.rpm = rpm
        self.min_interval = 60.0 / rpm          # seconds between requests
        self.window = deque()                    # timestamps of recent requests
        self._lock = threading.Lock()

    def wait(self):
        """Block until it's safe to make another request."""
        with self._lock:
            now = time.time()
            # Remove timestamps older than 60 seconds
            while self.window and now - self.window[0] > 60:
                self.window.popleft()

            if len(self.window) >= self.rpm:
                # Window is full — wait until oldest request expires
                wait_time = 60 - (now - self.window[0]) + 0.1
                logger.info(f"[RateLimiter] RPM limit reached. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                now = time.time()
                while self.window and now - self.window[0] > 60:
                    self.window.popleft()

            self.window.append(time.time())


# ── Rate-limited model wrapper ─────────────────────────────────────────────

class RateLimitedModel:
    """Wraps any Strands model with automatic rate limiting."""

    def __init__(self, model, model_id: str):
        self._model = model
        rpm = MODEL_RPM_LIMITS.get(model_id, DEFAULT_RPM)
        self._limiter = RateLimiter(rpm)
        logger.info(f"[RateLimiter] Model '{model_id}' limited to {rpm} RPM")

    def __getattr__(self, name):
        return getattr(self._model, name)

    def __call__(self, *args, **kwargs):
        self._limiter.wait()
        # Retry up to 3 times on 429
        for attempt in range(3):
            try:
                return self._model(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = (attempt + 1) * 10
                    logger.warning(f"[RateLimiter] 429 received, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise
