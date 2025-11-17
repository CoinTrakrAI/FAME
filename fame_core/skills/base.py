"""Minimal skill base class for trading integration."""

from __future__ import annotations

from typing import Dict


class Skill:
    """Base class for conversational skills."""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    def __init__(self) -> None:
        self.intents = []

    async def initialize(self):  # pragma: no cover - optional override
        return self

    async def handle(self, intent: str, entities: Dict, context: Dict) -> Dict:
        raise NotImplementedError


