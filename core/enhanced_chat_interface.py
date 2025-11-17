#!/usr/bin/env python3
"""
F.A.M.E. - Enhanced Chat Interface
Advanced LLM integration for intellectual conversations
"""

import asyncio
import json
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from typing import Dict, List, Any, Optional
from datetime import datetime
import re


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
            "huggingface": self._call_huggingface,
            "local": self._call_local_llm
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
            return {"error": f"Chat error: {str(e)}"}
    
    async def _generate_llm_response(self, message: str, system_prompt: str, 
                                   context: List[Dict], temperature: float) -> str:
        """Generate response using available LLM backends"""
        
        # Try different backends in order of preference
        backends_to_try = ["openai", "huggingface", "local"]
        
        for backend in backends_to_try:
            try:
                response = await self.llm_backends[backend](
                    message=message,
                    system_prompt=system_prompt,
                    context=context,
                    temperature=temperature
                )
                if response:
                    return response
            except Exception as e:
                print(f"Backend {backend} failed: {e}")
                continue
        
        # Fallback response
        return "I understand your query. As FAME AI, I can provide insights on business, technology, and strategy. For detailed analysis, please ensure LLM services are configured."
    
    async def _call_openai(self, message: str, system_prompt: str, 
                          context: List[Dict], temperature: float) -> Optional[str]:
        """Call OpenAI GPT models"""
        try:
            # This would be implemented with actual OpenAI API
            # For now, return a simulated response
            return self._simulate_ai_response(message, system_prompt)
        except:
            return None
    
    async def _call_huggingface(self, message: str, system_prompt: str, 
                               context: List[Dict], temperature: float) -> Optional[str]:
        """Call Hugging Face inference API"""
        try:
            # Simulated Hugging Face call
            return self._simulate_ai_response(message, system_prompt)
        except:
            return None
    
    async def _call_local_llm(self, message: str, system_prompt: str, 
                             context: List[Dict], temperature: float) -> Optional[str]:
        """Call local LLM (Ollama, etc.)"""
        try:
            # Simulated local LLM call
            return self._simulate_ai_response(message, system_prompt)
        except:
            return None
    
    def _simulate_ai_response(self, message: str, system_prompt: str) -> str:
        """Simulate AI response for demonstration"""
        message_lower = message.lower()
        
        # Business/finance queries
        if any(word in message_lower for word in ['stock', 'invest', 'market', 'financial', 'business']):
            return """Based on my analysis, I'd recommend a diversified investment approach considering current market conditions. 

Key insights:
- Technology sectors show strong growth potential, particularly in AI and cloud computing
- Consider defensive positions in consumer staples given economic uncertainties
- Emerging markets offer growth opportunities but require careful risk assessment

For your specific situation, I'd suggest:
1. 60% in growth-oriented tech stocks
2. 25% in stable blue-chip companies  
3. 15% in cash for opportunistic investments

Would you like me to analyze any specific companies or sectors in more detail?"""
        
        # Technology queries
        elif any(word in message_lower for word in ['tech', 'code', 'software', 'ai', 'system']):
            return """From a technical perspective, here's my assessment:

Current technology trends favor:
- Microservices architecture for scalability
- AI/ML integration in business processes
- Cloud-native development with containerization
- Real-time data processing capabilities

For your development needs, I recommend:
- Using Python with FastAPI for backend services
- React/Vue.js for modern frontend interfaces
- Docker and Kubernetes for deployment
- AWS/Azure for cloud infrastructure

I can help architect specific solutions or review your technical strategy."""
        
        # Strategy queries
        elif any(word in message_lower for word in ['strategy', 'plan', 'competition', 'market position']):
            return """Strategic analysis suggests:

Competitive Positioning:
- Focus on differentiation through technology innovation
- Build strong customer relationships and loyalty programs
- Consider strategic partnerships for market expansion

Growth Opportunities:
- Digital transformation initiatives
- International market penetration
- Product/service diversification

Risk Management:
- Monitor regulatory changes in your industry
- Maintain financial flexibility for market downturns
- Invest in cybersecurity and data protection

Would you like me to develop a more detailed strategic plan for your specific business context?"""
        
        # Default response
        return """As FAME AI, I've analyzed your query from multiple perspectives:

Business Perspective: Consider market positioning and competitive advantages
Technical Perspective: Evaluate implementation feasibility and scalability  
Strategic Perspective: Assess long-term implications and growth potential

Could you provide more specific details about your situation so I can offer more targeted advice?"""
    
    async def _enhance_with_plugins(self, message: str, current_response: str) -> Optional[str]:
        """Enhance response with FAME plugin capabilities"""
        message_lower = message.lower()
        
        # Check if we should use market analysis
        if any(word in message_lower for word in ['stock price', 'market analysis', 'trading', 'investment']):
            # This would integrate with market_oracle
            enhanced_response = current_response + "\n\n**Market Analysis Enhancement**: I can provide real-time market data and technical analysis for specific stocks if you'd like."
            return enhanced_response
        
        # Check if we should use code generation
        elif any(word in message_lower for word in ['build', 'create app', 'develop', 'code']):
            enhanced_response = current_response + "\n\n**Development Capability**: I can generate complete applications, trading bots, or data analysis tools. Just specify your requirements."
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


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator interface for enhanced chat"""
    text = request.get("text", "").lower().strip()
    persona = request.get("persona", "business_expert")
    
    if not text:
        return {"error": "No message text provided"}
    
    # Delegate simple queries to qa_engine instead of giving generic responses
    simple_queries = [
        'hi', 'hello', 'hey', 'greetings', 'howdy',
        'date', 'time', 'today', 'now', 'what day', 'current date', 'current time',
        'who is', 'who was', 'president', 'current'
    ]
    
    # Check if this is a simple query that qa_engine should handle
    if any(query in text for query in simple_queries) or len(text) < 10:
        # Return error so qa_engine can handle it instead
        return {"error": "delegate_to_qa_engine", "message": "Simple query - should be handled by qa_engine"}
    
    # For complex queries, use the chat interface
    async def chat():
        interface = EnhancedChatInterface()
        return await interface.chat_with_fame(request.get("text", ""), persona)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(chat())
        return result
    finally:
        loop.close()

