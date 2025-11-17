"""Simple plugin registry for discovering skills dynamically."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Type


_registered_skills: Dict[str, Type] = {}
_skill_instances: Dict[str, object] = {}


def register_skill(name: str) -> Callable[[Type], Type]:
    """Decorator used by skills to self-register."""

    def decorator(cls: Type) -> Type:
        _registered_skills[name] = cls
        return cls

    return decorator


def get_registered_skills() -> Dict[str, Type]:
    return dict(_registered_skills)


def register_skill_instance(name: str, instance: object) -> None:
    _skill_instances[name] = instance


def get_skill_instances() -> Dict[str, object]:
    return dict(_skill_instances)


__all__ = ["register_skill", "get_registered_skills", "register_skill_instance", "get_skill_instances"]


