#!/usr/bin/env python3
"""
Reinforcement Learning with Contextual Memory
Enterprise-grade RL for continuous adaptation
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import deque
import asyncio
from datetime import datetime

# Try to import torch, but make it optional
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

logger = logging.getLogger(__name__)


@dataclass
class TrainingEpisode:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    context: Dict
    timestamp: datetime


if TORCH_AVAILABLE:
    class ContextAwarePolicyNetwork(nn.Module):
        """Neural network for context-aware response policy"""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
            super().__init__()
            self.context_encoder = nn.Sequential(
                nn.Linear(state_dim, hidden_dim),
                nn.ReLU(),
                nn.LayerNorm(hidden_dim),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU()
            )
            
            self.policy_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, action_dim),
                nn.Softmax(dim=-1)
            )
            
            self.value_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1)
            )
        
        def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            context_embedding = self.context_encoder(state)
            action_probs = self.policy_head(context_embedding)
            state_value = self.value_head(context_embedding)
            return action_probs, state_value
else:
    class ContextAwarePolicyNetwork:
        """Placeholder when torch not available"""
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, *args):
            return None, None


class ReinforcementTrainer:
    """Enterprise-grade reinforcement learning with continuous adaptation"""
    
    def __init__(self, model_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.episode_memory = deque(maxlen=10000)  # Circular buffer
        self.training_batch_size = 32
        self.learning_rate = 0.001
        self.gamma = 0.99  # Discount factor
        
        # Initialize policy network
        self.state_dim = 512  # Embedding dimension
        self.action_dim = 10  # Response strategies
        
        if TORCH_AVAILABLE:
            self.policy_net = ContextAwarePolicyNetwork(self.state_dim, self.action_dim)
            self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        else:
            self.policy_net = None
            self.optimizer = None
            self.logger.warning("PyTorch not available - RL training will be limited")
        
        # Training state
        self.total_episodes = 0
        self.average_reward = 0.0
        self.convergence_threshold = 0.01
        
    async def record_episode(self, episode: TrainingEpisode):
        """Record a training episode for later learning"""
        self.episode_memory.append(episode)
        self.total_episodes += 1
        
        # Trigger learning if we have enough data
        if len(self.episode_memory) >= self.training_batch_size and TORCH_AVAILABLE:
            await self._train_batch()

    async def train_from_events(self, events: List[Dict], rewards: List[float]) -> Dict[str, float]:
        """Encode events into episodes and perform training."""
        if not events:
            return {"status": "skipped", "events": 0}
        if TORCH_AVAILABLE:
            for event, reward in zip(events, rewards):
                state = self._encode_event(event)
                next_state = state
                episode = TrainingEpisode(
                    state=state,
                    action=int(event.get("action_index", 0)),
                    reward=float(reward),
                    next_state=next_state,
                    context=event,
                    timestamp=datetime.utcnow(),
                )
                await self.record_episode(episode)
        avg_reward = float(np.mean(rewards))
        self.average_reward = 0.95 * self.average_reward + 0.05 * avg_reward
        return {"status": "updated", "events": len(events), "avg_reward": avg_reward}

    def _encode_event(self, event: Dict) -> np.ndarray:
        """Project event metrics into a fixed-size state vector."""
        state = np.zeros(self.state_dim, dtype=np.float32)
        state[0] = float(event.get("confidence", 0.0))
        state[1] = float(event.get("score", 0.0))
        trade = event.get("trade") or {}
        state[2] = float(trade.get("roi", 0.0))
        state[3] = float(event.get("latency_ms", 0.0)) / 1000.0
        state[4] = 1.0 if event.get("feedback_type") == "explicit" else 0.0
        return state

    async def _train_batch(self):
        """Train on a batch of episodes using PPO"""
        if not TORCH_AVAILABLE or len(self.episode_memory) < self.training_batch_size:
            return
            
        batch = np.random.choice(len(self.episode_memory), self.training_batch_size, replace=False)
        batch_episodes = [self.episode_memory[i] for i in batch]
        
        try:
            states = torch.FloatTensor([ep.state for ep in batch_episodes])
            actions = torch.LongTensor([ep.action for ep in batch_episodes])
            rewards = torch.FloatTensor([ep.reward for ep in batch_episodes])
            next_states = torch.FloatTensor([ep.next_state for ep in batch_episodes])
            
            # Calculate advantages
            with torch.no_grad():
                _, current_values = self.policy_net(states)
                _, next_values = self.policy_net(next_states)
                advantages = rewards + self.gamma * next_values - current_values
            
            # Policy gradient update
            action_probs, values = self.policy_net(states)
            action_log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)))
            
            # PPO loss
            policy_loss = -(action_log_probs * advantages).mean()
            value_loss = nn.MSELoss()(values, rewards.unsqueeze(1))
            
            total_loss = policy_loss + 0.5 * value_loss
            
            self.optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 0.5)
            self.optimizer.step()
            
            # Update average reward
            batch_avg_reward = rewards.mean().item()
            self.average_reward = 0.95 * self.average_reward + 0.05 * batch_avg_reward
            
            self.logger.info(f"RL training - Avg Reward: {self.average_reward:.3f}, Loss: {total_loss.item():.3f}")
            
        except Exception as e:
            self.logger.error(f"RL training failed: {e}")
    
    def get_response_strategy(self, state: np.ndarray, context: Dict) -> int:
        """Get optimal response strategy using current policy"""
        if not TORCH_AVAILABLE or self.policy_net is None:
            # Fallback: simple strategy based on state
            return hash(str(state[:10])) % self.action_dim
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            action_probs, _ = self.policy_net(state_tensor)
            action = torch.multinomial(action_probs, 1).item()
            return action
    
    def calculate_reward(self, user_feedback: str, conversation_length: int, 
                        engagement_metrics: Dict) -> float:
        """Calculate reward from multiple signals"""
        reward = 0.0
        
        # Explicit feedback
        if user_feedback == "positive":
            reward += 2.0
        elif user_feedback == "negative":
            reward -= 1.0
        
        # Engagement-based rewards
        if conversation_length > 3:  # Longer conversations are better
            reward += 0.5
        
        # Response time penalty (faster is better)
        if engagement_metrics.get('response_time', 10) < 2.0:
            reward += 0.3
        
        # Success metric (if user got what they wanted)
        if engagement_metrics.get('task_success', False):
            reward += 1.5
            
        return np.clip(reward, -2.0, 3.0)  # Bound rewards

