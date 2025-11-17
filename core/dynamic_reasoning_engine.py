#!/usr/bin/env python3
"""
FAME Dynamic Reasoning Engine
Provides true dynamic understanding and response generation using LLM reasoning
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import LLM libraries
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DynamicReasoningEngine:
    """Dynamic reasoning engine that thinks about questions and generates responses"""
    
    def __init__(self):
        self.openai_client = None
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if OPENAI_AVAILABLE and self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("OpenAI client initialized for dynamic reasoning")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        # Cache for reasoning results
        self.reasoning_cache = {}
    
    def _reason_about_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Think about the question and determine how to answer it
        
        Returns reasoning structure with:
        - question_type: What kind of question is this?
        - intent: What is the user really asking?
        - best_sources: Which modules/sources should answer this?
        - reasoning: Why these sources?
        - answer_approach: How should we answer?
        """
        # Use LLM if available for reasoning
        if self.openai_client:
            try:
                return self._llm_reasoning(question, context)
            except Exception as e:
                logger.warning(f"LLM reasoning failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based reasoning
        return self._rule_based_reasoning(question, context)
    
    def _llm_reasoning(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use LLM to reason about the question"""
        
        # Build context about FAME's capabilities
        capabilities = ""
        if context and 'available_modules' in context:
            capabilities = f"Available modules: {', '.join(context['available_modules'][:10])}"
        
        prompt = f"""You are FAME (Fully Autonomous Meta-Evolving AI). Analyze this question and determine how to answer it.

Question: "{question}"

{capabilities}

Think about:
1. What is the user really asking? (intent)
2. What type of question is this? (factual, technical, about FAME, conversational, etc.)
3. Which sources/modules should be used? (knowledge_base, web_search, core_modules, etc.)
4. How should we answer? (direct answer, search and synthesize, use specific module, etc.)

Respond in JSON format:
{{
    "question_type": "factual|technical|self_referential|conversational|capability|general",
    "intent": "what the user is really asking",
    "best_sources": ["source1", "source2"],
    "reasoning": "why these sources",
    "answer_approach": "direct|search|module|synthesize",
    "is_about_fame": true/false,
    "requires_search": true/false,
    "requires_knowledge_base": true/false
}}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv('FAME_LLM_MODEL', 'gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "You are a reasoning engine. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            reasoning = json.loads(result_text)
            
            logger.info(f"LLM Reasoning: {reasoning.get('intent')} -> {reasoning.get('best_sources')}")
            return reasoning
            
        except Exception as e:
            logger.error(f"LLM reasoning error: {e}")
            return self._rule_based_reasoning(question, context)
    
    def _rule_based_reasoning(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Rule-based reasoning fallback"""
        question_lower = question.lower()
        
        # Determine question type
        question_type = "general"
        is_about_fame = False
        requires_search = False
        requires_kb = False
        best_sources = []
        
        # Check if question is about FAME
        fame_indicators = ['you', 'your', 'fame', 'can you', 'do you', 'are you', 'what are you', 'who are you']
        if any(indicator in question_lower for indicator in fame_indicators):
            question_type = "self_referential"
            is_about_fame = True
            best_sources = ['qa_engine', 'capability_discovery']
        
        # Check if it's a capability question
        capability_indicators = ['can you', 'could you', 'would you', 'what can you', 'what could you']
        if any(indicator in question_lower for indicator in capability_indicators):
            question_type = "capability"
            is_about_fame = True
            best_sources = ['qa_engine', 'capability_discovery']
        
        # Check if it's conversational
        conversational_indicators = ['thank', 'thanks', 'great', 'good job', 'appreciate', 'you\'re doing']
        if any(indicator in question_lower for indicator in conversational_indicators):
            question_type = "conversational"
            best_sources = ['qa_engine']
        
        # Check if it's factual
        factual_indicators = ['who is', 'what is', 'when did', 'where is', 'current', 'today']
        if any(indicator in question_lower for indicator in factual_indicators) and not is_about_fame:
            question_type = "factual"
            requires_search = True
            best_sources = ['web_scraper', 'web_search']
        
        # Check if it's technical
        technical_indicators = ['how to', 'how do', 'build', 'create', 'code', 'program', 'script']
        if any(indicator in question_lower for indicator in technical_indicators) and not is_about_fame:
            question_type = "technical"
            best_sources = ['universal_developer', 'qa_engine']
            requires_kb = True
        
        # Check if it's security-related
        security_indicators = ['security', 'hack', 'vulnerability', 'penetration', 'cyber']
        if any(indicator in question_lower for indicator in security_indicators):
            question_type = "technical"
            best_sources = ['universal_hacker', 'knowledge_base', 'qa_engine']
            requires_kb = True
        
        return {
            "question_type": question_type,
            "intent": question,
            "best_sources": best_sources if best_sources else ['qa_engine'],
            "reasoning": f"Rule-based analysis: {question_type} question",
            "answer_approach": "synthesize" if len(best_sources) > 1 else "direct",
            "is_about_fame": is_about_fame,
            "requires_search": requires_search,
            "requires_knowledge_base": requires_kb
        }
    
    async def generate_dynamic_response(self, question: str, available_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a dynamic response based on reasoning about the question
        
        Args:
            question: User's question
            available_data: Available data from modules/sources
            
        Returns:
            Dynamic response dictionary
        """
        # Step 1: Reason about the question
        context = {
            'available_modules': available_data.get('modules', []) if available_data else []
        }
        reasoning = self._reason_about_question(question, context)
        
        # Step 2: If we have LLM, use it for dynamic generation (for any question, not just FAME)
        if self.openai_client:
            # Use LLM to generate dynamic response
            try:
                llm_result = await self._generate_llm_response(question, reasoning, available_data)
                if llm_result.get('response'):
                    return llm_result
            except Exception as e:
                logger.debug(f"LLM generation failed: {e}, falling back to rule-based")
        
        # Step 3: If it's about FAME but no LLM, generate rule-based response
        if reasoning.get('is_about_fame'):
            return self._generate_rule_based_fame_response(question, reasoning, available_data)
        
        # Step 4: Otherwise, synthesize from available data
        if available_data and available_data.get('responses'):
            return self._synthesize_from_data(question, reasoning, available_data['responses'])
        
        # Step 5: Fallback - return reasoning for further processing
        return {
            "response": None,  # Signal to continue with normal flow
            "reasoning": reasoning,
            "source": "reasoning_engine"
        }
    
    async def _generate_llm_response(self, question: str, reasoning: Dict[str, Any], 
                                    available_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate dynamic response using LLM"""
        
        # Build context about FAME
        fame_context = ""
        if available_data and 'capabilities' in available_data:
            capabilities = available_data['capabilities']
            if capabilities:
                fame_context = f"\nFAME's capabilities: {', '.join(capabilities[:5])}"
        
        if available_data and 'modules' in available_data:
            modules = available_data['modules']
            if modules:
                fame_context += f"\nAvailable modules: {', '.join(modules[:10])}"
        
        # Determine if this is about FAME or general question
        is_about_fame = reasoning.get('is_about_fame', False)
        
        if is_about_fame:
            prompt = f"""You are FAME (Fully Autonomous Meta-Evolving AI). Answer this question naturally and dynamically, as if you're a human-like AI assistant.

Question: "{question}"

{fame_context}

Reasoning about the question:
- Type: {reasoning.get('question_type')}
- Intent: {reasoning.get('intent')}
- Best sources: {', '.join(reasoning.get('best_sources', []))}

Answer the question:
1. Be conversational and natural (like Alexa or Siri)
2. Use first person ("I can...", "I am...", "I have...")
3. Be specific about capabilities if asked
4. Don't repeat templated responses - answer dynamically based on the actual question
5. Think about what the user is really asking and provide a thoughtful, relevant answer
6. If you don't know something specific, say so honestly

Generate a natural, dynamic response:"""
        else:
            # General question - use reasoning to help answer
            prompt = f"""You are FAME (Fully Autonomous Meta-Evolving AI). Answer this question thoughtfully.

Question: "{question}"

{fame_context}

Reasoning about the question:
- Type: {reasoning.get('question_type')}
- Intent: {reasoning.get('intent')}
- Best sources: {', '.join(reasoning.get('best_sources', []))}

Answer the question:
1. Be conversational and natural
2. Use first person when appropriate
3. Think about what the user is really asking
4. Provide a thoughtful, relevant answer
5. If you don't know something specific, say so honestly

Generate a natural, dynamic response:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv('FAME_LLM_MODEL', 'gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "You are FAME, a helpful AI assistant. Answer naturally and dynamically."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            dynamic_response = response.choices[0].message.content.strip()
            
            return {
                "response": dynamic_response,
                "source": "dynamic_reasoning_engine",
                "reasoning": reasoning,
                "confidence": 0.85,
                "type": reasoning.get('question_type', 'general')
            }
            
        except Exception as e:
            logger.error(f"LLM response generation error: {e}")
            return {
                "response": None,
                "reasoning": reasoning,
                "source": "reasoning_engine"
            }
    
    def _synthesize_from_data(self, question: str, reasoning: Dict[str, Any], 
                              responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize response from available data"""
        # Combine responses intelligently
        combined_text = []
        sources = []
        
        for resp in responses:
            if isinstance(resp, dict):
                if 'response' in resp:
                    combined_text.append(resp['response'])
                if 'source' in resp:
                    sources.append(resp['source'])
        
        if combined_text:
            return {
                "response": "\n\n".join(combined_text[:3]),  # Limit to top 3
                "source": "synthesized",
                "sources": sources,
                "reasoning": reasoning,
                "confidence": 0.75
            }
        
        return {
            "response": None,
            "reasoning": reasoning,
            "source": "reasoning_engine"
        }
    
    def _generate_rule_based_fame_response(self, question: str, reasoning: Dict[str, Any], 
                                          available_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate rule-based response about FAME when LLM unavailable"""
        question_lower = question.lower()
        
        # Get capabilities
        capabilities_text = ""
        if available_data and 'capabilities' in available_data:
            capabilities = available_data['capabilities'][:3]
            if capabilities:
                capabilities_text = f" I specialize in: {', '.join(capabilities)}."
        
        # Get modules
        modules_text = ""
        if available_data and 'modules' in available_data:
            modules = available_data['modules'][:5]
            if modules:
                modules_text = f" I have access to {len(modules)} core modules including {', '.join(modules[:3])}."
        
        # Generate contextual response based on question
        if 'what makes you' in question_lower or 'special' in question_lower or 'unique' in question_lower:
            response = f"I'm FAME (Fully Autonomous Meta-Evolving AI), and what makes me special is my ability to dynamically discover and use 34+ core modules simultaneously.{capabilities_text}{modules_text} I can write code, analyze markets, perform security testing, and much more - all in parallel. Unlike static assistants, I actually think about your questions and generate responses based on what I currently know about myself and my capabilities."
        elif 'who are you' in question_lower:
            response = f"I'm FAME (Fully Autonomous Meta-Evolving AI), a fully autonomous AI assistant with 34+ core modules.{capabilities_text}{modules_text} I can help with technical questions, code generation, security analysis, market predictions, and much more. I'm designed to be like Siri or Alexa, but with the ability to think about questions and answer them dynamically."
        elif 'what are you' in question_lower:
            response = f"I'm FAME, an AI assistant with dynamic capabilities.{capabilities_text}{modules_text} I can answer questions, generate code, analyze data, and help with a wide variety of tasks. I'm designed to think about your questions and provide intelligent, context-aware responses."
        elif 'how do you' in question_lower or 'how can you' in question_lower:
            response = f"I work by dynamically analyzing your questions and using my 34+ core modules to provide comprehensive answers.{capabilities_text}{modules_text} I can execute multiple tasks in parallel, search the web using multiple APIs simultaneously, and synthesize information from various sources to give you the best possible answer."
        else:
            # Generic response about FAME
            response = f"I'm FAME (Fully Autonomous Meta-Evolving AI).{capabilities_text}{modules_text} I can help you with many different tasks. What would you like to know?"
        
        return {
            "response": response,
            "source": "dynamic_reasoning_engine",
            "reasoning": reasoning,
            "confidence": 0.75,
            "type": reasoning.get('question_type', 'self_referential')
        }


# Singleton instance
_reasoning_engine: Optional[DynamicReasoningEngine] = None


def get_reasoning_engine() -> DynamicReasoningEngine:
    """Get or create reasoning engine instance"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = DynamicReasoningEngine()
    return _reasoning_engine

