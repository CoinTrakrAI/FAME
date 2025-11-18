#!/usr/bin/env python3
"""
Graph Reasoning Networks for FAME
Multi-hop reasoning over knowledge graphs with attention mechanisms
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in knowledge graph"""
    id: str
    content: str
    embeddings: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    neighbors: List[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Edge in knowledge graph"""
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphReasoner:
    """
    Graph Reasoning Networks for multi-hop reasoning.
    Implements attention mechanisms for graph traversal.
    """
    
    def __init__(self, embedding_dim: int = 768, max_hops: int = 3):
        """
        Initialize Graph Reasoner
        
        Args:
            embedding_dim: Dimension of node embeddings
            max_hops: Maximum hops for reasoning
        """
        self.embedding_dim = embedding_dim
        self.max_hops = max_hops
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.attention_mechanisms = MultiHeadAttention(embedding_dim)
        
    def add_node(self, node_id: str, content: str, 
                 embeddings: Optional[np.ndarray] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> GraphNode:
        """Add node to knowledge graph"""
        node = GraphNode(
            id=node_id,
            content=content,
            embeddings=embeddings,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node
        return node
    
    def add_edge(self, source_id: str, target_id: str, 
                relation: str, weight: float = 1.0,
                metadata: Optional[Dict[str, Any]] = None) -> GraphEdge:
        """Add edge to knowledge graph"""
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError(f"Nodes must exist before adding edge")
            
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            weight=weight,
            metadata=metadata or {}
        )
        
        self.edges.append(edge)
        self.nodes[source_id].neighbors.append(target_id)
        
        return edge
    
    def retrieve_initial_facts(self, query: str) -> List[str]:
        """
        Retrieve initial facts/nodes relevant to query
        
        Args:
            query: Query string
            
        Returns:
            List of node IDs
        """
        # Simple retrieval - in production would use semantic search
        relevant_nodes = []
        
        query_lower = query.lower()
        for node_id, node in self.nodes.items():
            if any(word in node.content.lower() for word in query_lower.split()):
                relevant_nodes.append(node_id)
                
        return relevant_nodes[:10]  # Limit to top 10
    
    def graph_attention_step(self, current_nodes: List[str], 
                           query: str) -> List[str]:
        """
        One step of graph attention reasoning
        
        Args:
            current_nodes: Current set of nodes being considered
            query: Original query
            
        Returns:
            New set of nodes after attention step
        """
        next_nodes: Set[str] = set()
        
        for node_id in current_nodes:
            if node_id not in self.nodes:
                continue
                
            node = self.nodes[node_id]
            
            # Get neighbors
            neighbors = node.neighbors
            
            # Apply attention to neighbors
            if neighbors:
                attention_scores = self._compute_attention_scores(
                    node_id, neighbors, query
                )
                
                # Select top-k neighbors based on attention
                top_k = min(5, len(neighbors))
                top_indices = np.argsort(attention_scores)[-top_k:]
                
                for idx in top_indices:
                    next_nodes.add(neighbors[idx])
        
        return list(next_nodes)
    
    def _compute_attention_scores(self, current_id: str, 
                                 neighbor_ids: List[str],
                                 query: str) -> np.ndarray:
        """
        Compute attention scores for neighbors
        """
        if not neighbor_ids:
            return np.array([])
            
        # Simplified attention - in production would use learned attention
        scores = []
        
        for neighbor_id in neighbor_ids:
            neighbor = self.nodes[neighbor_id]
            
            # Simple scoring based on content similarity
            score = 0.5
            
            # Boost if relation type is relevant
            for edge in self.edges:
                if edge.source_id == current_id and edge.target_id == neighbor_id:
                    if edge.relation in query.lower():
                        score += 0.3
                    score += edge.weight * 0.2
                    
            scores.append(score)
            
        return np.array(scores)
    
    def multi_hop_reasoning(self, query: str, max_hops: Optional[int] = None) -> Dict[str, Any]:
        """
        Multi-hop reasoning over knowledge graph
        
        Args:
            query: Query to reason about
            max_hops: Maximum hops (defaults to self.max_hops)
            
        Returns:
            Reasoning result with answer and path
        """
        max_hops = max_hops or self.max_hops
        
        # Step 1: Retrieve initial facts
        current_nodes = self.retrieve_initial_facts(query)
        
        reasoning_path = [current_nodes.copy()]
        
        # Step 2: Multi-hop reasoning
        for hop in range(max_hops):
            if not current_nodes:
                break
                
            # Graph attention step
            next_nodes = self.graph_attention_step(current_nodes, query)
            
            if not next_nodes:
                break
                
            current_nodes = next_nodes
            reasoning_path.append(current_nodes.copy())
            
            logger.debug(f"Hop {hop + 1}: Expanded to {len(current_nodes)} nodes")
        
        # Step 3: Synthesize answer
        answer = self.synthesize_answer(current_nodes, query, reasoning_path)
        
        return {
            "query": query,
            "answer": answer,
            "reasoning_path": reasoning_path,
            "final_nodes": current_nodes,
            "num_hops": len(reasoning_path) - 1
        }
    
    def synthesize_answer(self, nodes: List[str], query: str,
                         reasoning_path: List[List[str]]) -> str:
        """
        Synthesize final answer from reasoning path
        """
        if not nodes:
            return "I couldn't find enough information to answer this query."
        
        # Collect content from nodes in reasoning path
        all_content = []
        for node_ids in reasoning_path:
            for node_id in node_ids[:3]:  # Limit per hop
                if node_id in self.nodes:
                    all_content.append(self.nodes[node_id].content)
        
        # Simple synthesis - in production would use LLM
        synthesized = " ".join(all_content[:5])  # First 5 relevant pieces
        
        if not synthesized:
            synthesized = "Based on the knowledge graph, I found related information but cannot synthesize a complete answer."
            
        return synthesized[:500]  # Limit length


class MultiHeadAttention:
    """Simplified multi-head attention for graph reasoning"""
    
    def __init__(self, embedding_dim: int, num_heads: int = 4):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        
    def forward(self, query: np.ndarray, key: np.ndarray, 
               value: np.ndarray) -> np.ndarray:
        """
        Multi-head attention forward pass
        Simplified version - full implementation would include learned weights
        """
        # Placeholder - in production would use learned attention
        # This is a simplified version
        attention_scores = np.dot(query, key.T) / np.sqrt(self.head_dim)
        attention_weights = self._softmax(attention_scores)
        output = np.dot(attention_weights, value)
        return output
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax function"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

