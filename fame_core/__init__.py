"""Lightweight core framework components for skills and plugins."""

from .plugin_registry import register_skill, get_registered_skills

__all__ = ["register_skill", "get_registered_skills"]


