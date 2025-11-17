"""
Lightweight multi-agent reinforcement learner used by the live intelligence trainer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)


@dataclass
class MultiAgentConfig:
    state_dim: int = 512
    action_dim: int = 3
    hidden_dim: int = 64
    agents: Tuple[str, ...] = ("intraday", "swing", "risk")
    learning_rates: Dict[str, float] = field(default_factory=lambda: {"intraday": 1e-3, "swing": 5e-4, "risk": 5e-4})
    device: str = "cpu"


class _Policy(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.network(state)


class MultiAgentRLSystem:
    """Maintains simple policy/value networks per agent and performs supervised-style updates."""

    def __init__(self, config: MultiAgentConfig) -> None:
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else "cpu")
        self.policies: Dict[str, _Policy] = {}
        self.optimizers: Dict[str, optim.Optimizer] = {}

        for agent in config.agents:
            policy = _Policy(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
            lr = config.learning_rates.get(agent, 1e-3)
            optimiser = optim.Adam(policy.parameters(), lr=lr)
            for group in optimiser.param_groups:
                group["original_lr"] = lr
            self.policies[agent] = policy
            self.optimizers[agent] = optimiser

        logger.info("MultiAgentRLSystem initialised with agents: %s", ", ".join(self.policies))

    async def train_cycle(self, market_data: Dict[str, Any], experiences: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        losses: Dict[str, float] = {}
        count: Dict[str, int] = {}
        for experience in experiences:
            state: torch.Tensor = experience["state"].to(self.device)
            reward = torch.tensor(experience["reward"], dtype=torch.float32, device=self.device)
            agent = self._assign_agent(experience)
            policy = self.policies[agent]
            optimiser = self.optimizers[agent]

            optimiser.zero_grad()
            logits = policy(state)
            target = self._reward_to_target(reward, logits.shape[-1])
            loss = nn.MSELoss()(logits, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
            optimiser.step()

            losses[agent] = losses.get(agent, 0.0) + float(loss.item())
            count[agent] = count.get(agent, 0) + 1

        averaged: Dict[str, float] = {}
        for agent in self.policies:
            if count.get(agent):
                averaged[agent] = losses.get(agent, 0.0) / max(1, count.get(agent, 1))
            else:
                averaged[agent] = 0.0
        averaged["experiences"] = sum(count.values())
        averaged["market_snapshot"] = market_data.get("timestamp")
        return averaged

    def _assign_agent(self, experience: Dict[str, Any]) -> str:
        intent = experience.get("metadata", {}).get("event_type", "")
        if "risk" in intent:
            return "risk" if "risk" in self.policies else next(iter(self.policies))
        if "swing" in intent or "long" in intent:
            return "swing" if "swing" in self.policies else next(iter(self.policies))
        return "intraday" if "intraday" in self.policies else next(iter(self.policies))

    @staticmethod
    def _reward_to_target(reward: torch.Tensor, action_dim: int) -> torch.Tensor:
        base = torch.zeros(action_dim, dtype=torch.float32, device=reward.device)
        scaled = torch.clamp(reward, -1.0, 1.0)
        base += scaled
        return base

