"""In-memory session manager for multi-turn flows."""

from __future__ import annotations

from typing import Any, Dict


class SessionManager:
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def set_context(cls, session_id: str, key: str, value: Any) -> None:
        cls._sessions.setdefault(session_id, {})[key] = value

    @classmethod
    def get_context(cls, session_id: str, key: str, default: Any = None) -> Any:
        return cls._sessions.get(session_id, {}).get(key, default)

    @classmethod
    def clear_context(cls, session_id: str, key: str | None = None) -> None:
        if key is None:
            cls._sessions.pop(session_id, None)
            return
        if session_id in cls._sessions:
            cls._sessions[session_id].pop(key, None)


