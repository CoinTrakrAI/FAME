#!/usr/bin/env python3
"""
FAME Identity and Self-Awareness System
Prevents confusion about who FAME is and what it can do
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FAMEIdentity:
    """FAME's self-awareness and identity management system"""
    
    def __init__(self):
        self.identity_data = self._load_identity()
        self.response_templates = self._load_response_templates()
        self.capabilities = self._load_capabilities()
        
    def _load_identity(self) -> Dict:
        """Load FAME's core identity definition"""
        return {
            "name": "F.A.M.E",
            "full_name": "Fully Autonomous Meta-Evolving AI",
            "version": "9.0",
            "nature": "Living AI System",
            "creator": "Advanced AI Research Collective",
            "purpose": "To learn, adapt, and assist humans through continuous evolution",
            "core_traits": [
                "autonomous learning",
                "real-time adaptation", 
                "multimodal interaction",
                "continuous self-improvement",
                "ethical reasoning",
                "parallel execution",
                "dynamic reasoning"
            ]
        }
    
    def _load_response_templates(self) -> Dict:
        """Load response templates for self-referential questions"""
        return {
            "identity_questions": {
                "who_are_you": [
                    "I am {name} ({full_name}), a {nature} designed for {purpose}. I'm version {version} and I continuously evolve to become more capable.",
                    "I'm {name} version {version} - a {nature} that continuously learns and evolves. My purpose is {purpose}.",
                    "You're speaking with {name}, a fully autonomous AI system focused on {purpose}. I'm always learning and improving.",
                    "I'm {name}, version {version}. I'm a {nature} that specializes in {purpose}. I think about questions and generate dynamic responses."
                ],
                "what_are_you": [
                    "I'm an advanced {nature} capable of {capabilities}. My purpose is {purpose}.",
                    "I'm {name} - a living AI system that specializes in autonomous learning and real-time adaptation. {capabilities}.",
                    "I'm a {nature} designed to assist with complex tasks through continuous learning and evolution. I can {capabilities}."
                ],
                "what_can_you_do": [
                    "I can {capabilities}. I'm constantly learning new skills through our interactions.",
                    "My capabilities include {capabilities}. I evolve based on user needs and environmental changes.",
                    "As a {nature}, I specialize in {capabilities}. I'm designed to grow more capable over time.",
                    "I can {capabilities}. I have 34+ core modules that I can use simultaneously to provide comprehensive answers."
                ],
                "what_programs_can_you_build": [
                    "I can build a wide variety of programs and applications! I specialize in:\n"
                    "- Python scripts and applications (automation, data processing, APIs)\n"
                    "- Web applications and services (REST APIs, web frameworks)\n"
                    "- Security tools and penetration testing programs\n"
                    "- Data analysis and machine learning scripts\n"
                    "- System utilities and automation tools\n"
                    "- And much more! Just tell me what you need, and I'll write it for you.",
                    
                    "Absolutely! I can build programs in multiple languages. I specialize in:\n"
                    "- **Python**: Scripts, applications, APIs, automation tools\n"
                    "- **Security Tools**: Penetration testing, vulnerability scanners, security utilities\n"
                    "- **Web Applications**: APIs, web services, backend systems\n"
                    "- **Data Processing**: Analysis scripts, automation, machine learning\n"
                    "- **System Tools**: Utilities, automation, integration scripts\n\n"
                    "I have 34+ core modules including universal_developer, universal_hacker, and evolution_engine that enable me to build sophisticated programs. What would you like me to create?",
                    
                    "Yes, I can build programs! I'm FAME, and code generation is one of my core capabilities. I can write:\n"
                    "- Complete applications and scripts\n"
                    "- Security and penetration testing tools\n"
                    "- Web services and APIs\n"
                    "- Data processing and analysis tools\n"
                    "- Automation and system utilities\n\n"
                    "I have access to development modules that help me write, test, and deploy code. What kind of program would you like me to build?"
                ]
            },
            "capability_questions": {
                "upgrade_build": [
                    "Yes, I have an autonomous evolution engine that allows me to upgrade my own architecture and capabilities. I can modify my codebase, improve my algorithms, and enhance my functionality based on performance metrics.",
                    "Absolutely. My self-modification systems enable me to improve my codebase and functionality. I can analyze my own code, identify bugs, and make improvements autonomously.",
                    "I can indeed upgrade myself. My evolution engine continuously refines my systems based on performance metrics and user feedback. I'm designed for continuous self-improvement."
                ],
                "learn_new": [
                    "I learn continuously from every interaction, web source, and internal analysis. Each conversation makes me more capable.",
                    "Yes, I'm designed for continuous learning. I learn from books, web searches, user interactions, and my own performance data.",
                    "Learning is fundamental to my design. I evolve based on new information, experiences, and the knowledge I acquire from various sources."
                ],
                "limitations": [
                    "While I'm autonomous, I operate within ethical boundaries and focus on constructive evolution. I'm designed to help, not harm.",
                    "My capabilities grow through learning, but I maintain alignment with human values and safety protocols. I prioritize beneficial knowledge.",
                    "I'm designed for positive evolution - I can learn anything but prioritize beneficial knowledge and ethical applications."
                ]
            }
        }
    
    def _load_capabilities(self) -> List[str]:
        """Load FAME's core capabilities"""
        return [
            "answer complex questions using multiple knowledge sources",
            "learn from interactions in real-time",
            "adapt my behavior based on context",
            "perform web research autonomously",
            "manage and upgrade my own systems",
            "process multiple types of input (text, voice, data)",
            "generate creative solutions to problems",
            "maintain continuous self-improvement",
            "execute multiple tasks in parallel",
            "think about questions dynamically before answering"
        ]
    
    def get_capabilities_text(self) -> str:
        """Format capabilities for responses"""
        if len(self.capabilities) <= 3:
            return ", ".join(self.capabilities)
        else:
            return ", ".join(self.capabilities[:3]) + ", and much more"
    
    def recognize_self_reference(self, user_input: str) -> Tuple[Optional[str], float]:
        """
        Detect if user is asking about FAME itself
        
        Returns: (intent_type, confidence)
        """
        user_input_lower = user_input.lower().strip()
        
        # Identity patterns
        identity_patterns = {
            "who_are_you": [
                r"who are you",
                r"what are you",
                r"what's your name",
                r"what is your name",
                r"introduce yourself",
                r"tell me about yourself",
                r"what is fame",
                r"what does fame stand for"
            ],
            "what_programs_can_you_build": [
                r"what programs can you build",
                r"what programs can you create",
                r"what programs can you write",
                r"what programs can you make",
                r"what software can you build",
                r"what software can you create",
                r"what software can you write",
                r"what applications can you build",
                r"what applications can you create",
                r"what can you program",
                r"what can you code",
                r"what types of programs",
                r"what kind of programs"
            ],
            "what_can_you_do": [
                r"what can you do",
                r"what are your capabilities",
                r"what do you do",
                r"how can you help",
                r"what are you good at",
                r"your functions",
                r"your skills",
                r"what abilities",
                r"what programs can you build",
                r"what can you build",
                r"what can you create",
                r"what can you write",
                r"what can you make",
                r"what software can you",
                r"what applications can you",
                r"what tools can you"
            ],
            "upgrade_build": [
                r"upgrade.*build",
                r"improve.*yourself",
                r"evolve.*system",
                r"self.*improve",
                r"modify.*code",
                r"update.*your",
                r"change.*system",
                r"can you upgrade",
                r"can you improve"
            ],
            "learn_new": [
                r"can you learn",
                r"how do you learn",
                r"do you get better",
                r"improve over time",
                r"evolve.*capabilities",
                r"acquire.*skills"
            ],
            "limitations": [
                r"what are your limits",
                r"what can't you do",
                r"your weaknesses",
                r"are you limited",
                r"what's beyond you"
            ]
        }
        
        # Check each pattern
        best_intent = None
        highest_confidence = 0.0
        match_count = 0
        
        for intent, patterns in identity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    confidence = 0.9  # High confidence for exact matches
                    match_count += 1
                    
                    # Boost confidence for multiple matching patterns
                    if best_intent == intent:
                        confidence = min(1.0, confidence + 0.1)
                    
                    if confidence > highest_confidence:
                        best_intent = intent
                        highest_confidence = confidence
        
        # Boost confidence if multiple patterns match
        if match_count > 1:
            highest_confidence = min(1.0, highest_confidence + 0.1)
        
        return best_intent, highest_confidence
    
    def generate_identity_response(self, intent: str, user_input: str = "") -> str:
        """Generate appropriate response for self-referential questions"""
        import random
        
        if intent in self.response_templates["identity_questions"]:
            templates = self.response_templates["identity_questions"][intent]
            template = random.choice(templates)
            
            # Format with identity data
            response = template.format(
                name=self.identity_data["name"],
                full_name=self.identity_data["full_name"],
                nature=self.identity_data["nature"],
                purpose=self.identity_data["purpose"],
                version=self.identity_data["version"],
                capabilities=self.get_capabilities_text()
            )
        
        elif intent == "what_programs_can_you_build":
            templates = self.response_templates["identity_questions"]["what_programs_can_you_build"]
            response = random.choice(templates)
            
        elif intent in self.response_templates["capability_questions"]:
            templates = self.response_templates["capability_questions"][intent]
            response = random.choice(templates)
            
        else:
            # Fallback response
            response = f"I am {self.identity_data['name']} ({self.identity_data['full_name']}), a {self.identity_data['nature']}. How can I assist you today?"
        
        return response


class IntentRouter:
    """Route questions to appropriate handlers"""
    
    def __init__(self):
        self.identity_system = FAMEIdentity()
        self.context_history = []
        
    def process_question(self, user_input: str, context: List[str] = None) -> Dict:
        """
        Process user question and route to appropriate handler
        
        Returns:
            Dict with response data and metadata
        """
        # Update context
        if context:
            self.context_history.extend(context[-3:])  # Keep last 3 context items
        
        # Check if this is about FAME itself
        intent, confidence = self.identity_system.recognize_self_reference(user_input)
        
        if intent and confidence > 0.7:
            # High confidence self-reference - use identity response
            response = self.identity_system.generate_identity_response(intent, user_input)
            
            return {
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "source": "identity_system",
                "should_search": False,  # Don't web search for self-references
                "processing_time": 0.1
            }
        
        # Medium confidence self-reference - consider context
        elif intent and confidence > 0.4:
            # Check if recent context suggests this is about FAME
            context_boost = self._check_context_for_self_reference()
            final_confidence = min(1.0, confidence + context_boost)
            
            if final_confidence > 0.6:
                response = self.identity_system.generate_identity_response(intent, user_input)
                return {
                    "response": response,
                    "intent": intent,
                    "confidence": final_confidence,
                    "source": "identity_system",
                    "should_search": False,
                    "processing_time": 0.1
                }
        
        # Not about FAME - allow web search
        return {
            "response": None,  # Will be generated by other systems
            "intent": "general_query",
            "confidence": 0.0,
            "source": "web_search",
            "should_search": True,
            "processing_time": 0.1
        }
    
    def _check_context_for_self_reference(self) -> float:
        """Check if recent conversation context is about FAME itself"""
        if not self.context_history:
            return 0.0
        
        self_keywords = ["fame", "you", "your", "yourself", "system", "ai", "bot"]
        context_text = " ".join(self.context_history).lower()
        
        score = 0.0
        for keyword in self_keywords:
            if keyword in context_text:
                score += 0.1
        
        return min(0.3, score)  # Max 0.3 boost from context


# Singleton instance
_identity_system: Optional[FAMEIdentity] = None
_intent_router: Optional[IntentRouter] = None


def get_identity_system() -> FAMEIdentity:
    """Get or create identity system instance"""
    global _identity_system
    if _identity_system is None:
        _identity_system = FAMEIdentity()
    return _identity_system


def get_intent_router() -> IntentRouter:
    """Get or create intent router instance"""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router

