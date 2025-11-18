#!/usr/bin/env python3
"""
Monte Carlo Tree Search (MCTS) for Decision Making in FAME
Inspired by AlphaGo/AlphaZero architecture
"""

import logging
import random
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NodeState(Enum):
    """State of a decision node"""
    UNEXPLORED = "unexplored"
    EXPLORED = "explored"
    TERMINAL = "terminal"


@dataclass
class MCTSNode:
    """Node in MCTS decision tree"""
    id: str
    state: Any  # State representation
    action: Optional[Any] = None
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    q_value: float = 0.0  # Average action value
    u_value: float = 0.0  # Upper confidence bound
    node_state: NodeState = NodeState.UNEXPLORED
    is_terminal: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCTSDecisionMaker:
    """
    Monte Carlo Tree Search for complex decision making.
    Implements selection, expansion, simulation, and backpropagation.
    """
    
    def __init__(self, simulation_budget: int = 1000, exploration_constant: float = 1.414):
        """
        Initialize MCTS
        
        Args:
            simulation_budget: Number of simulations to run
            exploration_constant: Exploration vs exploitation trade-off (typically sqrt(2))
        """
        self.simulation_budget = simulation_budget
        self.exploration_constant = exploration_constant
        self.nodes: Dict[str, MCTSNode] = {}
        self.root_node_id: Optional[str] = None
        
    def search(self, initial_state: Any, available_actions: List[Any]) -> Any:
        """
        Perform MCTS search to find best action
        
        Args:
            initial_state: Starting state
            available_actions: List of possible actions
            
        Returns:
            Best action based on MCTS search
        """
        # Initialize root node
        root_id = self._create_node(None, initial_state, None)
        self.root_node_id = root_id
        
        # Run simulations
        for _ in range(self.simulation_budget):
            # Selection: Navigate to leaf node
            leaf_id = self._select(root_id)
            
            # Expansion: Add children if not terminal
            if not self.nodes[leaf_id].is_terminal:
                if not self.nodes[leaf_id].children:
                    self._expand(leaf_id, available_actions)
                    
            # Simulation: Rollout from leaf
            simulation_result = self._simulate(leaf_id)
            
            # Backpropagation: Update values up the tree
            self._backpropagate(leaf_id, simulation_result)
            
        # Select best action from root
        best_action = self._best_action(root_id)
        
        logger.debug(f"MCTS completed {self.simulation_budget} simulations, selected action: {best_action}")
        return best_action
    
    def _create_node(self, parent_id: Optional[str], state: Any, 
                    action: Optional[Any]) -> str:
        """Create a new node in the tree"""
        node_id = f"mcts_{id(state)}_{len(self.nodes)}"
        
        node = MCTSNode(
            id=node_id,
            state=state,
            action=action,
            parent_id=parent_id,
            node_state=NodeState.UNEXPLORED
        )
        
        self.nodes[node_id] = node
        
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)
            
        return node_id
    
    def _select(self, node_id: str) -> str:
        """
        Selection phase: Navigate from root to leaf using UCB
        """
        current_id = node_id
        
        while self.nodes[current_id].children:
            # Use UCB1 to select child
            current_id = self._ucb_select(current_id)
            
        return current_id
    
    def _ucb_select(self, node_id: str) -> str:
        """
        Select child using Upper Confidence Bound (UCB1)
        """
        node = self.nodes[node_id]
        
        if not node.children:
            return node_id
            
        best_value = float('-inf')
        best_child = node.children[0]
        
        for child_id in node.children:
            child = self.nodes[child_id]
            
            if child.visits == 0:
                return child_id  # Unvisited nodes have infinite UCB
                
            # UCB1 formula: Q(s,a) + c * sqrt(ln(N(s)) / N(s,a))
            exploitation = child.q_value
            exploration = self.exploration_constant * math.sqrt(
                math.log(node.visits) / child.visits
            )
            ucb_value = exploitation + exploration
            
            child.u_value = ucb_value
            
            if ucb_value > best_value:
                best_value = ucb_value
                best_child = child_id
                
        return best_child
    
    def _expand(self, node_id: str, available_actions: List[Any]):
        """
        Expansion phase: Add children for unexplored actions
        """
        node = self.nodes[node_id]
        
        for action in available_actions:
            # Generate new state from action
            new_state = self._apply_action(node.state, action)
            
            # Create child node
            child_id = self._create_node(node_id, new_state, action)
            self.nodes[child_id].node_state = NodeState.EXPLORED
            
            # Check if terminal
            if self._is_terminal(new_state):
                self.nodes[child_id].is_terminal = True
                self.nodes[child_id].node_state = NodeState.TERMINAL
                
    def _simulate(self, node_id: str) -> float:
        """
        Simulation phase: Random rollout from node to terminal state
        """
        node = self.nodes[node_id]
        current_state = node.state
        
        # Check if already terminal
        if node.is_terminal:
            return self._evaluate_state(current_state)
            
        # Random rollout
        max_simulation_steps = 100
        for _ in range(max_simulation_steps):
            if self._is_terminal(current_state):
                break
                
            # Random action
            actions = self._get_available_actions(current_state)
            if not actions:
                break
                
            action = random.choice(actions)
            current_state = self._apply_action(current_state, action)
            
        return self._evaluate_state(current_state)
    
    def _backpropagate(self, node_id: str, value: float):
        """
        Backpropagation phase: Update values up the tree
        """
        current_id = node_id
        
        while current_id:
            node = self.nodes[current_id]
            node.visits += 1
            node.value += value
            
            # Update Q-value (average)
            if node.visits > 0:
                node.q_value = node.value / node.visits
                
            current_id = node.parent_id
            
    def _best_action(self, node_id: str) -> Any:
        """
        Select best action based on visit counts or Q-values
        """
        node = self.nodes[node_id]
        
        if not node.children:
            return None
            
        best_child = max(
            node.children,
            key=lambda cid: self.nodes[cid].visits
        )
        
        return self.nodes[best_child].action
    
    # Abstract methods to be implemented by specific use cases
    
    def _apply_action(self, state: Any, action: Any) -> Any:
        """Apply action to state, return new state"""
        # Placeholder - implement based on domain
        return state
        
    def _is_terminal(self, state: Any) -> bool:
        """Check if state is terminal"""
        # Placeholder - implement based on domain
        return False
        
    def _get_available_actions(self, state: Any) -> List[Any]:
        """Get available actions for state"""
        # Placeholder - implement based on domain
        return []
        
    def _evaluate_state(self, state: Any) -> float:
        """
        Evaluate terminal state
        Returns value in range [-1, 1] where 1 is best outcome
        """
        # Placeholder - implement based on domain
        return random.uniform(-1, 1)
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about the search"""
        if not self.root_node_id or self.root_node_id not in self.nodes:
            return {}
            
        root = self.nodes[self.root_node_id]
        
        return {
            "simulations": self.simulation_budget,
            "total_nodes": len(self.nodes),
            "root_visits": root.visits,
            "root_value": root.q_value,
            "children_count": len(root.children)
        }

