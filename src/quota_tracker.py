from datetime import datetime
from collections import deque
import config

class QuotaTracker:
    """
    Tracks API calls in a rolling 60-second window.
    In-memory only. Resets when the app restarts.
    """
    def __init__(self):
        self._timestamps: deque = deque()

    def record_call(self) -> None:
        """Record that one API call was just made."""
        now = datetime.now().timestamp()
        self._timestamps.append(now)
        self._purge_old()

    def calls_in_last_minute(self) -> int:
        self._purge_old()
        return len(self._timestamps)

    def session_total(self) -> int:
        return sum(1 for _ in self._timestamps)  # all calls since app start

    def is_near_limit(self) -> bool:
        return self.calls_in_last_minute() >= (config.PER_MINUTE_LIMIT - 5)

    def _purge_old(self) -> None:
        now = datetime.now().timestamp()
        while self._timestamps and (now - self._timestamps[0]) > 60:
            self._timestamps.popleft()
