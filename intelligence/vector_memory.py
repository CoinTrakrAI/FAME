#!/usr/bin/env python3
"""
Vector-Based Long-Term Memory
Enterprise vector memory with semantic search
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

# Try to import optional dependencies
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class VectorMemory:
    """Enterprise vector memory with semantic search and reinforcement learning integration"""
    
    def __init__(self, persist_directory: str = "./vector_memory"):
        self.logger = logging.getLogger(__name__)
        self.persist_directory = persist_directory
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Try loading from HuggingFace cache or download
                import os
                model_name = 'sentence-transformers/all-mpnet-base-v2'
                # Allow model download in container (it has internet access)
                self.embedding_model = SentenceTransformer(model_name, device='cpu')
                self.embedding_dim = 768
                self.logger.info(f"Successfully loaded embedding model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Could not load sentence transformer: {e}. Using fallback embeddings.")
                self.embedding_model = None
                # Use 768 to match ChromaDB expectation even with fallback
                self.embedding_dim = 768
        else:
            self.embedding_model = None
            # Use 768 to match ChromaDB expectation even with fallback
            self.embedding_dim = 768
            self.logger.warning("sentence-transformers not available - using simple embeddings (768-dim)")
        
        # Initialize ChromaDB
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=persist_directory)
                # Explicitly set embedding dimension to 768 for ChromaDB
                self.collection = self.client.get_or_create_collection(
                    name="fame_memory",
                    metadata={"description": "FAME's long-term vector memory", "embedding_dimension": "768"}
                )
                # Ensure collection uses 768 dimensions
                if hasattr(self.collection, 'metadata'):
                    metadata = self.collection.metadata or {}
                    metadata['embedding_dimension'] = '768'
                self.logger.info("ChromaDB initialized with 768-dimension embeddings")
            except Exception as e:
                self.logger.warning(f"Could not initialize ChromaDB: {e}. Using in-memory storage.")
                self.client = None
                self.collection = None
        else:
            self.client = None
            self.collection = None
            self.logger.warning("chromadb not available - using in-memory storage")
        
        # In-memory fallback storage
        self.memory_store = []
        
        # Memory statistics
        self.access_patterns = {}
        self.learning_signals = {}
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """Simple embedding when sentence-transformers not available"""
        # Very simple hash-based embedding - pad/truncate to match expected dimension
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Always create 768-dim embedding to match ChromaDB expectation
        target_dim = 768
        # Repeat hash to fill 768 dimensions
        hash_repeated = (hash_bytes * ((target_dim // len(hash_bytes)) + 1))[:target_dim]
        # Convert to float array
        embedding = np.frombuffer(hash_repeated, dtype=np.uint8).astype(np.float32)
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    
    async def store_experience(self, 
                             conversation: Dict, 
                             response_strategy: int,
                             reward: float,
                             embedding: Optional[np.ndarray] = None):
        """Store conversation experience with vector embedding"""
        
        if embedding is None:
            text_to_embed = f"{conversation['user_input']} {conversation['ai_response']}"
            if self.embedding_model:
                embedding = self.embedding_model.encode(text_to_embed)
            else:
                embedding = self._simple_embedding(text_to_embed)
        
        # Create metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "response_strategy": response_strategy,
            "reward": reward,
            "user_input": conversation['user_input'][:200],  # Truncate for metadata
            "conversation_length": conversation.get('length', 1),
            "intent": conversation.get('intent', 'unknown')
        }
        
        # Store in vector database
        if self.collection:
            try:
                # Ensure embedding is exactly 768 dimensions
                embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                if len(embedding_list) != 768:
                    self.logger.warning(f"Embedding dimension mismatch: {len(embedding_list)} != 768. Adjusting.")
                    # Pad or truncate to 768
                    if len(embedding_list) < 768:
                        embedding_list.extend([0.0] * (768 - len(embedding_list)))
                    else:
                        embedding_list = embedding_list[:768]
                
                self.collection.add(
                    embeddings=[embedding_list],
                    metadatas=[metadata],
                    ids=[f"exp_{datetime.now().timestamp()}"]
                )
            except Exception as e:
                self.logger.error(f"Failed to store in ChromaDB: {e}")
                # Fallback to in-memory
                self.memory_store.append({
                    'embedding': embedding,
                    'metadata': metadata
                })
        else:
            # Fallback to in-memory storage
            self.memory_store.append({
                'embedding': embedding,
                'metadata': metadata
            })
        
        # Update access patterns for reinforcement learning
        self._update_learning_signals(conversation, reward)
    
    async def retrieve_similar_experiences(self, 
                                         query: str, 
                                         n_results: int = 5,
                                         min_reward: float = 0.0) -> List[Dict]:
        """Retrieve similar past experiences using semantic search"""
        
        if self.embedding_model:
            query_embedding = self.embedding_model.encode(query)
        else:
            query_embedding = self._simple_embedding(query)
        
        if self.collection:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=n_results
                )
                
                experiences = []
                if results['embeddings'] and len(results['embeddings'][0]) > 0:
                    for i, (embedding, metadata, id) in enumerate(zip(
                        results['embeddings'][0], 
                        results['metadatas'][0], 
                        results['ids'][0]
                    )):
                        # Filter by reward
                        if metadata.get('reward', 0) >= min_reward:
                            experience = {
                                'id': id,
                                'embedding': np.array(embedding),
                                'metadata': metadata,
                                'similarity_score': self._cosine_similarity(query_embedding, np.array(embedding))
                            }
                            experiences.append(experience)
                
                # Sort by similarity and reward
                experiences.sort(key=lambda x: (
                    x['similarity_score'] * 0.7 + 
                    x['metadata'].get('reward', 0) * 0.3
                ), reverse=True)
                
                return experiences[:n_results]
            except Exception as e:
                self.logger.error(f"Failed to retrieve from ChromaDB: {e}")
        
        # Fallback to in-memory search
        experiences = []
        for item in self.memory_store:
            if item['metadata'].get('reward', 0) >= min_reward:
                similarity = self._cosine_similarity(query_embedding, item['embedding'])
                experiences.append({
                    'id': f"mem_{len(experiences)}",
                    'embedding': item['embedding'],
                    'metadata': item['metadata'],
                    'similarity_score': similarity
                })
        
        experiences.sort(key=lambda x: (
            x['similarity_score'] * 0.7 + 
            x['metadata'].get('reward', 0) * 0.3
        ), reverse=True)
        
        return experiences[:n_results]
    
    def _update_learning_signals(self, conversation: Dict, reward: float):
        """Update reinforcement learning signals based on experience"""
        intent = conversation.get('intent', 'unknown')
        
        if intent not in self.learning_signals:
            self.learning_signals[intent] = {
                'total_reward': 0.0,
                'count': 0,
                'success_rate': 0.0
            }
        
        self.learning_signals[intent]['total_reward'] += reward
        self.learning_signals[intent]['count'] += 1
        self.learning_signals[intent]['success_rate'] = (
            self.learning_signals[intent]['total_reward'] / 
            self.learning_signals[intent]['count']
        )
    
    def get_optimal_strategy(self, intent: str) -> Optional[int]:
        """Get the most successful response strategy for a given intent"""
        if intent in self.learning_signals:
            signals = self.learning_signals[intent]
            if signals['success_rate'] > 0.7:
                # Return the strategy index (simplified)
                return hash(intent) % 10  # Placeholder
        return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

