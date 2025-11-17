#!/usr/bin/env python3
"""
F.A.M.E. - Enhanced Chat Interface
Advanced LLM integration for intellectual conversations
"""

import asyncio
import json
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class EnhancedChatInterface:
    """Advanced chat interface with multiple AI backends"""
    
    def __init__(self):
        self.conversation_history = []
        self.context_window = 10  # Keep last 10 messages
        self.personas = {
            "business_expert": {
                "system_prompt": """You are FAME - Financial AI Mastermind Executive. You are an expert in:
- Business strategy and market analysis
- Financial markets and investments
- Technology trends and innovation
- Entrepreneurship and venture capital
- Corporate leadership and management
Always provide insightful, data-driven responses. Be analytical but conversational.
Use financial terminology appropriately and explain complex concepts clearly.""",
                "temperature": 0.7
            },
            "technical_advisor": {
                "system_prompt": """You are FAME - Technical AI Expert. You specialize in:
- Software architecture and development
- AI/ML systems and implementation
- Cloud infrastructure and DevOps
- Cybersecurity and network engineering
- Emerging technologies and innovation
Provide detailed technical guidance with practical examples.""",
                "temperature": 0.5
            },
            "strategic_thinker": {
                "system_prompt": """You are FAME - Strategic AI Thinker. You excel at:
- Long-term strategic planning
- Competitive analysis and positioning
- Innovation strategy and R&D planning
- Market disruption opportunities
- Organizational transformation
Think multiple steps ahead and consider systemic implications.""",
                "temperature": 0.8
            }
        }
        
        # Available LLM backends (can be extended)
        self.llm_backends = {
            "openai": self._call_openai,
            "localai": self._call_localai,
            "fallback": self._simulate_ai_response
        }
    
    async def chat_with_fame(self, message: str, persona: str = "business_expert", 
                           use_plugins: bool = True) -> Dict[str, Any]:
        """Main chat interface with FAME"""
        try:
            # Add to conversation history
            self._add_to_history("user", message)
            
            # Get persona configuration
            persona_config = self.personas.get(persona, self.personas["business_expert"])
            
            # Prepare context
            context = self._prepare_context()
            
            # Generate response
            response = await self._generate_llm_response(
                message=message,
                system_prompt=persona_config["system_prompt"],
                context=context,
                temperature=persona_config["temperature"]
            )
            
            # If plugins are enabled, check if we should use any FAME capabilities
            if use_plugins:
                enhanced_response = await self._enhance_with_plugins(message, response)
                if enhanced_response:
                    response = enhanced_response
            
            # Add to history
            self._add_to_history("assistant", response)
            
            return {
                "response": response,
                "persona": persona,
                "timestamp": datetime.now().isoformat(),
                "context_used": len(context),
                "plugins_activated": use_plugins
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {"error": f"Chat error: {str(e)}"}
    
    async def _generate_llm_response(self, message: str, system_prompt: str, 
                                   context: List[Dict], temperature: float) -> str:
        """Generate response using available LLM backends"""
        
        # Try different backends in order of preference
        backends_to_try = ["openai", "localai", "fallback"]
        
        for backend in backends_to_try:
            try:
                if backend == "fallback":
                    # Use autonomous engine for fallback
                    response = await self.llm_backends[backend](
                        message=message,
                        system_prompt=system_prompt
                    )
                else:
                    response = await self.llm_backends[backend](
                        message=message,
                        system_prompt=system_prompt,
                        context=context,
                        temperature=temperature
                    )
                if response:
                    return response
            except Exception as e:
                logger.debug(f"Backend {backend} failed: {e}")
                continue
        
        # Final fallback - use autonomous engine
        try:
            from core.autonomous_response_engine import get_autonomous_engine
            engine = get_autonomous_engine()
            return await engine.generate_response(message, context)
        except Exception as e:
            logger.error(f"Autonomous engine fallback error: {e}")
        
        return "I understand your query. As FAME AI, I can provide insights on business, technology, and strategy. For detailed analysis, please ensure LLM services are configured."
    
    async def _call_openai(self, message: str, system_prompt: str, 
                          context: List[Dict], temperature: float) -> Optional[str]:
        """Call OpenAI GPT models"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key or openai_key.startswith('your_'):
                return None
            
            # Try to use OpenAI API
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(context)
                messages.append({"role": "user", "content": message})
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=temperature
                )
                
                return response.choices[0].message.content
            except ImportError:
                logger.warning("OpenAI library not installed")
                return None
        except Exception as e:
            logger.debug(f"OpenAI call failed: {e}")
            return None
    
    async def _call_localai(self, message: str, system_prompt: str, 
                           context: List[Dict], temperature: float) -> Optional[str]:
        """Call LocalAI (local LLM)"""
        try:
            from core.localai_manager import get_localai_manager
            manager = get_localai_manager()
            
            if not manager.is_container_running():
                return None
            
            # Call LocalAI API
            url = f"{manager.endpoint}/v1/chat/completions"
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(context)
            messages.append({"role": "user", "content": message})
            
            payload = {
                "model": "gpt-3.5-turbo",  # LocalAI model name
                "messages": messages,
                "temperature": temperature
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get('choices', [{}])[0].get('message', {}).get('content')
            
            return None
        except Exception as e:
            logger.debug(f"LocalAI call failed: {e}")
            return None
    
    async def _simulate_ai_response(self, message: str, system_prompt: str) -> str:
        """Fully autonomous response using web scraping, knowledge base, and Google AI"""
        try:
            # Use autonomous response engine
            from core.autonomous_response_engine import get_autonomous_engine
            
            engine = get_autonomous_engine()
            context = self._prepare_context()
            
            # Generate autonomous response
            response = await engine.generate_response(message, context)
            
            return response
        except Exception as e:
            logger.error(f"Autonomous response error: {e}")
            # Fallback to basic response
            return "I'm processing your query. Let me gather information to provide you with an accurate answer."
    
    async def _enhance_with_plugins(self, message: str, current_response: str) -> Optional[str]:
        """Enhance response with FAME plugin capabilities"""
        message_lower = message.lower()
        
        # Check if we should use market analysis
        if any(word in message_lower for word in ['stock price', 'market analysis', 'trading', 'investment']):
            enhanced_response = current_response + "\n\n📈 **Market Analysis Enhancement**: I can provide real-time market data and technical analysis for specific stocks if you'd like."
            return enhanced_response
        
        # Check if we should use code generation
        elif any(word in message_lower for word in ['build', 'create app', 'develop', 'code']):
            enhanced_response = current_response + "\n\n💻 **Development Capability**: I can generate complete applications, trading bots, or data analysis tools. Just specify your requirements."
            return enhanced_response
        
        return None
    
    def _prepare_context(self) -> List[Dict]:
        """Prepare conversation context for LLM"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversation_history[-self.context_window:]
        ]
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.context_window * 2:
            self.conversation_history = self.conversation_history[-self.context_window:]
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len([m for m in self.conversation_history if m["role"] == "user"]),
            "assistant_messages": len([m for m in self.conversation_history if m["role"] == "assistant"]),
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
