"""Skill discovery helpers."""

from __future__ import annotations

from typing import List, Type

from fame_core.plugin_registry import get_registered_skills
from fame_core.skills.base import Skill


def discover_skills() -> List[Type[Skill]]:
    """Return all registered skills."""

    return list(get_registered_skills().values())


__all__ = ["discover_skills"]


