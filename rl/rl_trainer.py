#!/usr/bin/env python3
"""
FAME AGI - Real Reinforcement Learning Loop
PPO-lite adaptive policy with Q-value updates and self-correction
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PolicyWeights:
    """Policy weights for different actions"""
    response_length: float = 0.5
    search_depth: float = 0.5
    tool_usage: float = 0.5
    memory_write: float = 0.5
    hallucination_penalty: float = -0.3
    confidence_threshold: float = 0.6


class RLTrainer:
    """
    Real RL trainer with PPO-lite policy updates.
    Adapts behavior based on reward signals.
    """
    
    def __init__(self, config: Dict[str, Any], memory: Optional[Any] = None, reasoner: Optional[Any] = None):
        self.config = config
        self.memory = memory
        self.reasoner = reasoner
        
        # Policy weights
        self.policy = PolicyWeights()
        
        # Q-value storage (state-action pairs)
        self.q_values: Dict[str, float] = {}
        
        # Experience buffer
        self.experience_buffer = deque(maxlen=10000)
        
        # Learning parameters
        self.learning_rate = config.get("rl", {}).get("learning_rate", 0.01)
        self.gamma = 0.95  # Discount factor
        self.epsilon = 0.1  # Exploration rate
        
        # Reward statistics
        self.reward_history = deque(maxlen=1000)
        self.avg_reward = 0.0
        
        # Load saved policy
        self._load_policy()
    
    def update(self, interaction: Dict[str, Any], reward: float):
        """
        Update policy based on interaction and reward.
        Implements Q-learning with policy gradient.
        """
        # Store experience
        state = self._extract_state(interaction)
        action = self._extract_action(interaction)
        next_state = state  # Simplified
        
        experience = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "timestamp": interaction.get("timestamp", 0)
        }
        
        self.experience_buffer.append(experience)
        self.reward_history.append(reward)
        
        # Update average reward
        self.avg_reward = np.mean(list(self.reward_history))
        
        # Q-value update
        state_action_key = f"{state}_{action}"
        current_q = self.q_values.get(state_action_key, 0.0)
        
        # Q-learning update
        max_next_q = max([
            self.q_values.get(f"{next_state}_{a}", 0.0)
            for a in self._get_available_actions()
        ], default=0.0)
        
        new_q = current_q + self.learning_rate * (
            reward + self.gamma * max_next_q - current_q
        )
        self.q_values[state_action_key] = new_q
        
        # Policy gradient update (PPO-lite)
        self._update_policy_weights(reward, interaction)
        
        # Periodic policy save
        if len(self.experience_buffer) % 100 == 0:
            self._save_policy()
    
    def _update_policy_weights(self, reward: float, interaction: Dict[str, Any]):
        """Update policy weights based on reward"""
        # Positive reward = increase weights, negative = decrease
        
        # Response length adjustment
        response_len = len(str(interaction.get("response", "")))
        if reward > 0:
            if 50 < response_len < 500:  # Good length range
                self.policy.response_length += self.learning_rate * 0.1
            else:
                self.policy.response_length -= self.learning_rate * 0.05
        else:
            self.policy.response_length -= self.learning_rate * 0.1
        
        # Search depth adjustment
        search_depth = interaction.get("metrics", {}).get("web_scrapes", 0)
        if reward > 0 and search_depth > 0:
            self.policy.search_depth += self.learning_rate * 0.1
        elif reward < 0 and search_depth > 3:
            self.policy.search_depth -= self.learning_rate * 0.1
        
        # Tool usage adjustment
        tools_used = interaction.get("metrics", {}).get("tools_used", 0)
        if reward > 0 and tools_used > 0:
            self.policy.tool_usage += self.learning_rate * 0.1
        
        # Hallucination penalty
        confidence = interaction.get("confidence", 0.5)
        if reward < 0 and confidence > 0.8:
            # High confidence but negative reward = likely hallucination
            self.policy.hallucination_penalty -= self.learning_rate * 0.2
        
        # Clamp weights
        self.policy.response_length = max(0.0, min(1.0, self.policy.response_length))
        self.policy.search_depth = max(0.0, min(1.0, self.policy.search_depth))
        self.policy.tool_usage = max(0.0, min(1.0, self.policy.tool_usage))
        self.policy.memory_write = max(0.0, min(1.0, self.policy.memory_write))
        self.policy.hallucination_penalty = max(-1.0, min(0.0, self.policy.hallucination_penalty))
    
    def get_action(self, state: str) -> str:
        """Select action based on current policy (epsilon-greedy)"""
        if np.random.random() < self.epsilon:
            # Exploration: random action
            actions = self._get_available_actions()
            return np.random.choice(actions)
        
        # Exploitation: best Q-value action
        best_action = None
        best_q = float('-inf')
        
        for action in self._get_available_actions():
            q_key = f"{state}_{action}"
            q_value = self.q_values.get(q_key, 0.0)
            if q_value > best_q:
                best_q = q_value
                best_action = action
        
        return best_action or "default"
    
    def get_policy_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get policy-based decision for current context"""
        return {
            "response_length": self._sample_length(),
            "search_depth": int(self.policy.search_depth * 5),
            "use_tools": self.policy.tool_usage > 0.5,
            "confidence_threshold": self.policy.confidence_threshold,
            "hallucination_check": abs(self.policy.hallucination_penalty) > 0.2
        }
    
    def _sample_length(self) -> int:
        """Sample response length based on policy"""
        base_length = 200
        length_factor = self.policy.response_length
        return int(base_length * (0.5 + length_factor))
    
    def _extract_state(self, interaction: Dict[str, Any]) -> str:
        """Extract state representation from interaction"""
        query = str(interaction.get("query", ""))[:50]
        intent = interaction.get("intent", "unknown")
        return f"{intent}_{len(query)}"
    
    def _extract_action(self, interaction: Dict[str, Any]) -> str:
        """Extract action from interaction"""
        sources = interaction.get("sources", [])
        if sources:
            return sources[0]
        return "default"
    
    def _get_available_actions(self) -> List[str]:
        """Get list of available actions"""
        return ["memory", "web", "llm_cloud", "llm_local", "fusion", "default"]
    
    def _load_policy(self):
        """Load saved policy weights"""
        policy_file = Path(self.config.get("memory", {}).get("data_dir", "./fame_data")) / "rl_policy.json"
        if policy_file.exists():
            try:
                with open(policy_file, 'r') as f:
                    data = json.load(f)
                    self.policy = PolicyWeights(**data.get("policy", {}))
                    self.q_values = data.get("q_values", {})
                    logger.info("RL policy loaded")
            except Exception as e:
                logger.error(f"Failed to load RL policy: {e}")
    
    def _save_policy(self):
        """Save policy weights"""
        policy_file = Path(self.config.get("memory", {}).get("data_dir", "./fame_data")) / "rl_policy.json"
        try:
            data = {
                "policy": {
                    "response_length": self.policy.response_length,
                    "search_depth": self.policy.search_depth,
                    "tool_usage": self.policy.tool_usage,
                    "memory_write": self.policy.memory_write,
                    "hallucination_penalty": self.policy.hallucination_penalty,
                    "confidence_threshold": self.policy.confidence_threshold
                },
                "q_values": self.q_values,
                "avg_reward": self.avg_reward
            }
            with open(policy_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("RL policy saved")
        except Exception as e:
            logger.error(f"Failed to save RL policy: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RL training statistics"""
        return {
            "avg_reward": self.avg_reward,
            "experience_count": len(self.experience_buffer),
            "q_values_count": len(self.q_values),
            "policy": {
                "response_length": self.policy.response_length,
                "search_depth": self.policy.search_depth,
                "tool_usage": self.policy.tool_usage,
                "hallucination_penalty": self.policy.hallucination_penalty
            }
        }

