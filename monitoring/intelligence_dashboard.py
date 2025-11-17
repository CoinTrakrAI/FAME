#!/usr/bin/env python3
"""
Intelligence Dashboard
Real-time monitoring for the intelligence system
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IntelligenceDashboard:
    """Real-time dashboard for monitoring intelligence system"""
    
    def __init__(self, intelligence_orchestrator):
        self.orchestrator = intelligence_orchestrator
        self.logger = logging.getLogger(__name__)
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get comprehensive learning metrics"""
        if not self.orchestrator:
            return {
                'error': 'Intelligence orchestrator not available'
            }
        
        summary = self.orchestrator.get_intelligence_summary()
        
        return {
            'reinforcement_learning': {
                'episodes_trained': summary['reinforcement_learning']['total_episodes'],
                'average_reward': summary['reinforcement_learning']['average_reward'],
                'learning_velocity': summary['performance_metrics']['learning_velocity'],
                'training_cycles': summary['reinforcement_learning']['training_cycles']
            },
            'vector_memory': {
                'experiences_stored': summary['vector_memory']['total_experiences'],
                'intent_coverage': summary['vector_memory']['learning_signals'],
                'success_rates': {
                    intent: signals.get('success_rate', 0.0)
                    for intent, signals in self.orchestrator.vector_memory.learning_signals.items()
                }
            },
            'auto_tuning': {
                'last_tuning': summary['auto_tuning']['last_tuning'],
                'metrics_history_length': summary['auto_tuning']['metrics_history_length'],
                'performance_trend': self._calculate_performance_trend()
            },
            'performance': summary['performance_metrics']
        }
    
    def _calculate_performance_trend(self) -> float:
        """Calculate performance trend from metrics history"""
        if not self.orchestrator or not self.orchestrator.auto_tuner:
            return 0.0
        
        metrics_history = self.orchestrator.auto_tuner.metrics_history
        if len(metrics_history) < 2:
            return 0.0
        
        recent = metrics_history[-5:] if len(metrics_history) >= 5 else metrics_history
        if len(recent) < 2:
            return 0.0
        
        trend = recent[-1].response_quality - recent[0].response_quality
        return trend
    
    def get_intelligence_status(self) -> Dict[str, Any]:
        """Get overall intelligence system status"""
        if not self.orchestrator:
            return {
                'status': 'unavailable',
                'message': 'Intelligence orchestrator not initialized'
            }
        
        summary = self.orchestrator.get_intelligence_summary()
        
        # Determine overall status
        avg_reward = summary['reinforcement_learning']['average_reward']
        success_rate = summary['performance_metrics']['success_rate']
        
        if avg_reward > 1.0 and success_rate > 0.7:
            status = 'excellent'
        elif avg_reward > 0.5 and success_rate > 0.5:
            status = 'good'
        elif avg_reward > 0.0:
            status = 'learning'
        else:
            status = 'initializing'
        
        return {
            'status': status,
            'total_interactions': summary['performance_metrics']['total_interactions'],
            'average_reward': avg_reward,
            'success_rate': success_rate,
            'learning_velocity': summary['performance_metrics']['learning_velocity'],
            'last_update': datetime.now().isoformat()
        }

