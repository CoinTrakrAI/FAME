#!/usr/bin/env python3
"""
FAME Autonomous Decision Engine
Enterprise-grade routing and decision-making system
"""

import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class AutonomousDecisionEngine:
    """
    Production-grade decision engine for autonomous AI assistant.
    Handles intent classification, module routing, and response synthesis.
    """
    
    def __init__(self, brain=None):
        self.brain = brain
        self.confidence_threshold_high = 0.8
        self.confidence_threshold_medium = 0.6
        self.confidence_threshold_low = 0.4
        
        # Discover available core modules for reference
        self._discover_core_modules()
    
    def _discover_core_modules(self):
        """Discover all available core modules for routing decisions"""
        try:
            from core.capability_discovery import discover_core_modules
            self.core_modules = discover_core_modules()
        except:
            self.core_modules = {}
        
        # Module priority mapping (higher priority = tried first)
        self.module_priorities = {
            'qa_engine': 100,  # Highest priority for general questions
            'web_scraper': 90,  # High priority for factual/current info
            'enhanced_market_oracle': 85,  # High priority for financial queries
            'trading_skill_plugin': 88,
            'advanced_investor_ai': 80,
            'universal_developer': 75,
            'universal_hacker': 70,
            'consciousness_engine': 60,
            'evolution_engine': 50,
            'enhanced_chat_interface': 40,
        }
        
        # Query type patterns
        self.query_patterns = {
            'factual': {
                'keywords': ['who is', 'who was', 'what is', 'what are', 'when did', 
                           'where is', 'president', 'current', 'today', 'now', 'latest'],
                'confidence_base': 0.85,
                'modules': ['web_scraper', 'qa_engine']
            },
            'financial': {
                'keywords': ['stock', 'price', 'market', 'trading', 'invest', 'crypto',
                           'bitcoin', 'forecast', 'analyze', 'portfolio', 'ticker'],
                'confidence_base': 0.80,
                'modules': ['enhanced_market_oracle', 'trading_skill_plugin', 'advanced_investor_ai', 'autonomous_investor']
            },
            'trading': {
                'keywords': ['trading signal', 'trade', 'buy', 'sell', 'execute trade', 'confirm trade',
                             'cancel trade', 'order', 'entry price', 'stop loss', 'take profit'],
                'confidence_base': 0.83,
                'modules': ['trading_skill_plugin', 'enhanced_market_oracle']
            },
            'technical': {
                'keywords': ['build', 'code', 'create', 'develop', 'program', 'function',
                           'script', 'api', 'architecture', 'design', 'nginx', 'envoy'],
                'confidence_base': 0.75,
                'modules': ['universal_developer', 'qa_engine']
            },
            'security': {
                'keywords': ['hack', 'security', 'vulnerability', 'exploit', 'breach',
                           'ransomware', 'malware', 'cyber', 'incident', 'containment'],
                'confidence_base': 0.70,
                'modules': ['universal_hacker', 'qa_engine']
            },
            'evolution': {
                'keywords': ['evolve', 'self-evolve', 'improve', 'fix bugs', 'upgrade',
                            'self improve', 'optimize', 'enhance'],
                'confidence_base': 0.75,
                'modules': ['qa_engine', 'evolution_engine']
            },
            'general': {
                'keywords': ['hello', 'hi', 'hey', 'greetings', 'how are you', 'what can you do'],
                'confidence_base': 0.90,
                'modules': ['qa_engine', 'consciousness_engine']
            },
            'date_time': {
                'keywords': ['date', 'time', 'today', 'what day', 'what time', 'current date', 'current time'],
                'confidence_base': 0.95,
                'modules': ['qa_engine']
            },
            'personal': {
                'keywords': ['my name', 'who am i', 'what do you know about me', 'remember my'],
                'confidence_base': 0.85,
                'modules': ['qa_engine']
            },
            'self_referential': {
                'keywords': ['can you write', 'can you code', 'can you program', 'can you create', 'can you build',
                           'can you develop', 'do you write', 'do you code', 'can fame', 'does fame',
                           'are you able', 'are you capable', 'can you help me write', 'can you generate code'],
                'confidence_base': 0.95,
                'modules': ['qa_engine']
            }
        }
    
    async def classify_intent(self, query: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify user intent with confidence scoring.
        
        Returns:
            (intent_type, confidence, metadata)
        """
        query_lower = query.lower().strip()
        
        # Normalize common misspellings
        query_lower = query_lower.replace('whos', 'who is').replace('whos the', 'who is the')
        
        # Score each query type
        scores = {}
        metadata = {}
        
        for intent_type, pattern in self.query_patterns.items():
            score = 0.0
            keyword_matches = []
            
            # Count keyword matches
            for keyword in pattern['keywords']:
                # Use word boundaries for better matching
                if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                    keyword_matches.append(keyword)
                    score += 1.0
            
            # Calculate confidence: base confidence + (match ratio * 0.2)
            if keyword_matches:
                match_ratio = len(keyword_matches) / len(pattern['keywords'])
                confidence = pattern['confidence_base'] + (match_ratio * 0.15)
                confidence = min(confidence, 0.95)  # Cap at 95%
                
                scores[intent_type] = confidence
                metadata[intent_type] = {
                    'keywords_matched': keyword_matches,
                    'match_ratio': match_ratio
                }
        
        # Select best intent
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            intent_type, confidence = best_intent
            
            return intent_type, confidence, {
                'intent_type': intent_type,
                'confidence': confidence,
                'metadata': metadata.get(intent_type, {}),
                'all_scores': scores
            }
        
        # Default to general if no match
        return 'general', 0.5, {'intent_type': 'general', 'confidence': 0.5}
    
    def select_modules(self, intent_type: str, confidence: float, query: str) -> List[Tuple[str, float]]:
        """
        Select modules to execute based on intent and confidence.
        
        Returns:
            List of (module_name, priority_score) tuples
        """
        # Get modules for this intent type
        pattern = self.query_patterns.get(intent_type, self.query_patterns['general'])
        candidate_modules = pattern.get('modules', ['qa_engine'])
        
        # Calculate priority scores
        module_scores = []
        for module_name in candidate_modules:
            base_priority = self.module_priorities.get(module_name, 50)
            # Boost priority based on confidence
            priority_score = base_priority + (confidence * 20)
            module_scores.append((module_name, priority_score))
        
        # Sort by priority (highest first)
        module_scores.sort(key=lambda x: x[1], reverse=True)
        
        # For high confidence, use only top module
        if confidence >= self.confidence_threshold_high:
            return module_scores[:1]
        # For medium confidence, try top 2
        elif confidence >= self.confidence_threshold_medium:
            return module_scores[:2]
        # For low confidence, try top 3
        else:
            return module_scores[:3]
    
    async def route_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main routing function - orchestrates the entire decision process.
        
        Args:
            query: Query dictionary with 'text' and optional metadata
        
        Returns:
            Response dictionary with routing information
        """
        query_text = query.get('text', '').strip()
        if not query_text:
            return {
                'error': True,
                'response': 'Empty query received.',
                'confidence': 0.0
            }
        
        # Step 1: Classify intent
        intent_type, confidence, intent_metadata = await self.classify_intent(query_text)
        
        # Step 2: Select modules
        selected_modules = self.select_modules(intent_type, confidence, query_text)
        
        # Step 3: Add module descriptions from discovered modules
        module_details = {}
        for mod_name, priority in selected_modules:
            if mod_name in self.core_modules:
                mod_info = self.core_modules[mod_name]
                module_details[mod_name] = {
                    'priority': priority,
                    'description': mod_info.get('description', 'Core functionality module'),
                    'name': mod_info.get('name', mod_name)
                }
            else:
                module_details[mod_name] = {
                    'priority': priority,
                    'description': 'Core functionality module',
                    'name': mod_name
                }
        
        # Step 4: Build routing response
        routing_info = {
            'intent_type': intent_type,
            'confidence': confidence,
            'selected_modules': [mod[0] for mod in selected_modules],
            'module_priorities': {mod[0]: mod[1] for mod in selected_modules},
            'module_details': module_details,  # Include module descriptions
            'metadata': intent_metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Routing query: intent={intent_type}, confidence={confidence:.2f}, modules={routing_info['selected_modules']}")
        
        return routing_info
    
    async def synthesize_responses(self, responses: List[Dict[str, Any]], 
                                   query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize multiple module responses into a single coherent answer.
        
        Args:
            responses: List of response dictionaries from modules
            query: Original query
        
        Returns:
            Synthesized response dictionary
        """
        if not responses:
            # No responses - try AutonomousResponseEngine as fallback
            try:
                from core.autonomous_response_engine import get_autonomous_engine
                import asyncio
                
                engine = get_autonomous_engine()
                query_text = query.get('text', '')
                
                if query_text:
                    # Generate autonomous response
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            engine.generate_response(query_text, None)
                        )
                        if result and isinstance(result, dict):
                            response_text = result.get('response', '')
                            if response_text and len(response_text) > 10:
                                return {
                                    'response': response_text,
                                    'confidence': result.get('confidence', 0.6),
                                    'source': 'autonomous_response_engine',
                                    'sources': ['autonomous_engine']
                                }
                    finally:
                        loop.close()
            except Exception as e:
                logger.debug(f"AutonomousResponseEngine fallback in synthesize failed: {e}")
            
            return {
                'error': True,
                'response': "I couldn't process that request. Could you please rephrase?",
                'confidence': 0.0
            }
        
        # Filter successful responses
        successful = [r for r in responses if 'error' not in r or not r.get('error')]
        
        if not successful:
            # All failed - try AutonomousResponseEngine as fallback
            try:
                from core.autonomous_response_engine import get_autonomous_engine
                import asyncio
                
                engine = get_autonomous_engine()
                query_text = query.get('text', '')
                
                if query_text:
                    # Generate autonomous response
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            engine.generate_response(query_text, None)
                        )
                        if result and isinstance(result, dict):
                            response_text = result.get('response', '')
                            if response_text and len(response_text) > 10:
                                return {
                                    'response': response_text,
                                    'confidence': result.get('confidence', 0.6),
                                    'source': 'autonomous_response_engine',
                                    'sources': ['autonomous_engine']
                                }
                    finally:
                        loop.close()
            except Exception as e:
                logger.debug(f"AutonomousResponseEngine fallback in synthesize failed: {e}")
            
            # Return helpful error if fallback also failed
            return {
                'error': True,
                'response': "I encountered an error processing your request. Please try again or rephrase your question.",
                'confidence': 0.0,
                'raw_responses': responses
            }
        
        # If only one response, return it directly
        if len(successful) == 1:
            result = successful[0]
            # Ensure 'response' key exists
            if 'response' not in result:
                if 'text' in result:
                    result['response'] = result['text']
                elif 'answer' in result:
                    result['response'] = result['answer']
                elif 'content' in result:
                    result['response'] = result['content']
                else:
                    result['response'] = str(result)
            return result
        
        # Multiple responses - synthesize
        # Prioritize by confidence if available
        responses_with_confidence = []
        for r in successful:
            conf = r.get('confidence', 0.5)
            responses_with_confidence.append((conf, r))
        
        responses_with_confidence.sort(key=lambda x: x[0], reverse=True)
        
        # Use highest confidence response as primary
        primary_confidence, primary_response = responses_with_confidence[0]
        
        # Combine if confidence is high enough
        if primary_confidence >= self.confidence_threshold_high:
            final_response = primary_response.copy()
            final_response['synthesized'] = True
            final_response['sources'] = [r[1].get('source', 'unknown') for r in responses_with_confidence[:3]]
            return final_response
        
        # Medium/low confidence - combine information
        combined_text = []
        for conf, resp in responses_with_confidence[:2]:
            response_text = resp.get('response') or resp.get('text') or resp.get('answer', '')
            if response_text:
                combined_text.append(response_text)
        
        return {
            'response': '\n\n'.join(combined_text),
            'confidence': primary_confidence,
            'synthesized': True,
            'sources': [r[1].get('source', 'unknown') for r in responses_with_confidence[:2]]
        }
    
    def get_confidence_level(self, confidence: float) -> str:
        """Get human-readable confidence level"""
        if confidence >= self.confidence_threshold_high:
            return "high"
        elif confidence >= self.confidence_threshold_medium:
            return "medium"
        elif confidence >= self.confidence_threshold_low:
            return "low"
        else:
            return "very_low"
    
    def should_ask_clarification(self, confidence: float) -> bool:
        """Determine if clarification should be requested"""
        return confidence < self.confidence_threshold_medium


# Singleton instance
_decision_engine: Optional[AutonomousDecisionEngine] = None


def get_decision_engine(brain=None) -> AutonomousDecisionEngine:
    """Get or create decision engine instance"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AutonomousDecisionEngine(brain)
    return _decision_engine

