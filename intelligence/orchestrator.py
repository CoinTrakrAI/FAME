#!/usr/bin/env python3
"""
Enhanced Intelligence Orchestrator
Orchestrates all intelligence components with enterprise reliability
"""

import asyncio
from typing import Dict, Any, List
import logging
import numpy as np
from datetime import datetime

from intelligence.reinforcement_trainer import ReinforcementTrainer, TrainingEpisode
from intelligence.vector_memory import VectorMemory
from intelligence.auto_tuner import ContinuousAutoTuner

logger = logging.getLogger(__name__)


class IntelligenceOrchestrator:
    """Orchestrates all intelligence components with enterprise reliability"""
    
    def __init__(self, config_manager=None, intent_classifier=None):
        self.config_manager = config_manager
        self.intent_classifier = intent_classifier
        self.logger = logging.getLogger(__name__)
        
        # Initialize intelligence components
        self.reinforcement_trainer = ReinforcementTrainer()
        self.vector_memory = VectorMemory()
        self.auto_tuner = ContinuousAutoTuner(
            self.reinforcement_trainer, 
            self.vector_memory
        )
        
        # Performance tracking
        self.performance_metrics = {
            'total_interactions': 0,
            'successful_responses': 0,
            'average_confidence': 0.0,
            'learning_velocity': 0.0,
            'success_rate': 0.0
        }
        
        # Auto-tuning task
        self._auto_tuning_task = None
    
    async def initialize(self):
        """Initialize all intelligence components"""
        self.logger.info("Initializing intelligence orchestrator")
        
        # Start auto-tuning in background
        self._auto_tuning_task = asyncio.create_task(self.auto_tuner.start_auto_tuning())
        
        self.logger.info("Intelligence orchestrator initialized")
    
    async def process_interaction(self, 
                                user_input: str, 
                                ai_response: str,
                                context: Dict[str, Any],
                                feedback: str = None) -> Dict[str, Any]:
        """Process a complete interaction through the intelligence layer"""
        
        self.performance_metrics['total_interactions'] += 1
        
        try:
            # 1. Get intent (if classifier available)
            if self.intent_classifier:
                intent_result = await self.intent_classifier.predict_async(user_input)
            else:
                intent_result = {'intent': 'unknown', 'confidence': 0.5}
            
            # 2. Get embedding
            if self.vector_memory.embedding_model:
                embedding = self.vector_memory.embedding_model.encode(user_input)
            else:
                embedding = self.vector_memory._simple_embedding(user_input)
            
            # 3. Retrieve similar experiences
            similar_experiences = await self.vector_memory.retrieve_similar_experiences(
                user_input, n_results=3
            )
            
            # 4. Calculate reward
            reward = self.reinforcement_trainer.calculate_reward(
                feedback or "",
                context.get('conversation_length', 1),
                context.get('engagement_metrics', {})
            )
            
            if reward > 0:
                self.performance_metrics['successful_responses'] += 1
            
            # 5. Create training episode
            state = self._create_state_representation(
                user_input, embedding, intent_result, similar_experiences
            )
            
            episode = TrainingEpisode(
                state=state,
                action=intent_result.get('response_strategy', 0),
                reward=reward,
                next_state=state,  # Simplified
                context=context,
                timestamp=datetime.now()
            )
            
            # 6. Store in memory and train
            await self.vector_memory.store_experience(
                conversation={
                    'user_input': user_input,
                    'ai_response': ai_response,
                    'intent': intent_result.get('intent', 'unknown'),
                    'length': context.get('conversation_length', 1)
                },
                response_strategy=intent_result.get('response_strategy', 0),
                reward=reward,
                embedding=embedding
            )
            
            await self.reinforcement_trainer.record_episode(episode)
            
            # 7. Update performance metrics
            self._update_performance_metrics(intent_result, reward)
            
            return {
                'success': True,
                'reward': reward,
                'similar_experiences_count': len(similar_experiences),
                'learning_applied': True
            }
            
        except Exception as e:
            self.logger.error(f"Intelligence processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_state_representation(self, 
                                   user_input: str,
                                   embedding: np.ndarray,
                                   intent_result: Dict,
                                   similar_experiences: List) -> np.ndarray:
        """Create comprehensive state representation for RL"""
        
        # Basic features
        state_features = []
        
        # Intent confidence
        state_features.append(intent_result.get('confidence', 0.5))
        
        # Embedding (first few dimensions)
        state_features.extend(embedding[:500])  # Use first 500 dimensions
        
        # Experience similarity
        if similar_experiences:
            avg_similarity = np.mean([exp['similarity_score'] for exp in similar_experiences])
            state_features.append(avg_similarity)
        else:
            state_features.append(0.0)
        
        # Context features
        state_features.append(self.performance_metrics['average_confidence'])
        
        # Pad or truncate to fixed size
        target_size = self.reinforcement_trainer.state_dim
        if len(state_features) < target_size:
            state_features.extend([0.0] * (target_size - len(state_features)))
        else:
            state_features = state_features[:target_size]
        
        return np.array(state_features, dtype=np.float32)
    
    def _update_performance_metrics(self, intent_result: Dict, reward: float):
        """Update comprehensive performance metrics"""
        confidence = intent_result.get('confidence', 0.5)
        
        # Update average confidence (exponential moving average)
        alpha = 0.1
        self.performance_metrics['average_confidence'] = (
            alpha * confidence + 
            (1 - alpha) * self.performance_metrics['average_confidence']
        )
        
        # Calculate success rate
        total = self.performance_metrics['total_interactions']
        successful = self.performance_metrics['successful_responses']
        self.performance_metrics['success_rate'] = successful / total if total > 0 else 0.0
        
        # Learning velocity (simplified)
        self.performance_metrics['learning_velocity'] = (
            self.reinforcement_trainer.average_reward * 0.1 +
            self.performance_metrics['success_rate'] * 0.9
        )
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get comprehensive intelligence system summary"""
        memory_count = 0
        if self.vector_memory.collection:
            try:
                memory_count = self.vector_memory.collection.count()
            except:
                memory_count = len(self.vector_memory.memory_store)
        else:
            memory_count = len(self.vector_memory.memory_store)
        
        return {
            'performance_metrics': self.performance_metrics,
            'reinforcement_learning': {
                'total_episodes': self.reinforcement_trainer.total_episodes,
                'average_reward': self.reinforcement_trainer.average_reward,
                'training_cycles': len(self.reinforcement_trainer.episode_memory)
            },
            'vector_memory': {
                'learning_signals': len(self.vector_memory.learning_signals),
                'total_experiences': memory_count
            },
            'auto_tuning': {
                'last_tuning': self.auto_tuner.last_tuning_time.isoformat(),
                'metrics_history_length': len(self.auto_tuner.metrics_history)
            }
        }

