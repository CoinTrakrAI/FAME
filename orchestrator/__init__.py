"""
FAME Orchestrator - Production-ready orchestration layer
Coordinates all core modules with safety, sandboxing, and evolution
"""

from orchestrator.brain import Brain
from orchestrator.plugin_loader import load_plugins
from orchestrator.event_bus import EventBus

__all__ = ['Brain', 'load_plugins', 'EventBus']

