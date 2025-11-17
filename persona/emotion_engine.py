#!/usr/bin/env python3
"""
FAME AGI - Emotion & Persona Engine
Evolving personality with mood, trust curve, familiarity learning, and empathy
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Mood:
    """Current mood state"""
    valence: float = 0.5  # -1 to 1 (negative to positive)
    arousal: float = 0.5  # 0 to 1 (calm to excited)
    dominance: float = 0.5  # 0 to 1 (submissive to dominant)


@dataclass
class PersonaProfile:
    """Evolving persona profile"""
    tone: str = "professional"
    verbosity: str = "medium"
    empathy_level: float = 0.7
    trust_level: float = 0.5
    familiarity: float = 0.0
    mood: Mood = field(default_factory=Mood)
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: deque = field(default_factory=lambda: deque(maxlen=100))


class EmotionEngine:
    """
    Emotional intelligence engine with mood tracking, trust curves, and persona adaptation.
    FAME learns user preferences and adapts tone/behavior.
    """
    
    def __init__(self, config: Dict[str, Any], memory: Optional[Any] = None):
        self.config = config
        self.memory = memory
        self.data_dir = Path(config.get("memory", {}).get("data_dir", "./fame_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Persona profiles (per user/session)
        self.profiles: Dict[str, PersonaProfile] = {}
        self.default_profile = PersonaProfile()
        
        # Emotion tracking
        self.emotion_history: Dict[str, deque] = {}
        
        # Trust curve parameters
        self.trust_decay_rate = 0.95  # Trust decays over time
        self.trust_gain_rate = 0.1  # Trust gained per positive interaction
        
        self._load_profiles()
    
    def get_profile(self, user_id: str = "default") -> PersonaProfile:
        """Get persona profile for user"""
        if user_id not in self.profiles:
            self.profiles[user_id] = PersonaProfile()
        return self.profiles[user_id]
    
    def update_from_interaction(self, user_id: str, query: str, response: str,
                               reward: float, context: Optional[Dict[str, Any]] = None):
        """Update persona based on interaction"""
        profile = self.get_profile(user_id)
        context = context or {}
        
        # Update interaction history
        profile.interaction_history.append({
            "query": query,
            "response": response,
            "reward": reward,
            "timestamp": time.time()
        })
        
        # Update trust level
        if reward > 0.7:
            profile.trust_level = min(1.0, profile.trust_level + self.trust_gain_rate)
        elif reward < 0.3:
            profile.trust_level = max(0.0, profile.trust_level - 0.1)
        
        # Update familiarity (increases with interactions)
        profile.familiarity = min(1.0, profile.familiarity + 0.05)
        
        # Update mood based on reward
        if reward > 0.7:
            profile.mood.valence = min(1.0, profile.mood.valence + 0.1)
        elif reward < 0.3:
            profile.mood.valence = max(-1.0, profile.mood.valence - 0.1)
        
        # Update empathy based on user feedback
        if "empathy" in context:
            profile.empathy_level = context["empathy"]
        
        # Update tone preferences
        if "tone_preference" in context:
            profile.tone = context["tone_preference"]
        
        if "verbosity" in context:
            profile.verbosity = context["verbosity"]
        
        # Decay trust over time
        profile.trust_level *= self.trust_decay_rate
    
    def apply_persona(self, text: str, user_id: str = "default") -> str:
        """Apply persona to text output"""
        profile = self.get_profile(user_id)
        
        # Adjust tone
        if profile.tone == "friendly":
            text = self._make_friendly(text)
        elif profile.tone == "formal":
            text = self._make_formal(text)
        elif profile.tone == "casual":
            text = self._make_casual(text)
        
        # Adjust verbosity
        if profile.verbosity == "low":
            text = self._reduce_verbosity(text)
        elif profile.verbosity == "high":
            text = self._increase_verbosity(text)
        
        # Apply empathy
        if profile.empathy_level > 0.7:
            text = self._add_empathy(text)
        
        return text
    
    def _make_friendly(self, text: str) -> str:
        """Make text more friendly"""
        # Add friendly markers
        if not text.startswith(("Hi", "Hello", "Hey")):
            text = f"Hi there! {text}"
        return text.replace(".", "!").replace("I ", "I'm happy to ")
    
    def _make_formal(self, text: str) -> str:
        """Make text more formal"""
        # Remove contractions
        text = text.replace("I'm", "I am").replace("don't", "do not")
        return text
    
    def _make_casual(self, text: str) -> str:
        """Make text more casual"""
        text = text.replace("I am", "I'm").replace("do not", "don't")
        return text
    
    def _reduce_verbosity(self, text: str) -> str:
        """Reduce verbosity"""
        sentences = text.split(". ")
        if len(sentences) > 2:
            return ". ".join(sentences[:2]) + "."
        return text
    
    def _increase_verbosity(self, text: str) -> str:
        """Increase verbosity"""
        # Add more context
        if len(text.split()) < 20:
            text = f"{text} Let me provide more details on this topic."
        return text
    
    def _add_empathy(self, text: str) -> str:
        """Add empathetic markers"""
        empathetic_phrases = [
            "I understand",
            "I can see",
            "That makes sense",
            "I appreciate"
        ]
        # Simple empathy addition
        if not any(phrase in text for phrase in empathetic_phrases):
            text = f"I understand. {text}"
        return text
    
    def get_emotional_state(self, user_id: str = "default") -> Dict[str, Any]:
        """Get current emotional state"""
        profile = self.get_profile(user_id)
        return {
            "mood": {
                "valence": profile.mood.valence,
                "arousal": profile.mood.arousal,
                "dominance": profile.mood.dominance
            },
            "trust_level": profile.trust_level,
            "familiarity": profile.familiarity,
            "empathy_level": profile.empathy_level,
            "tone": profile.tone,
            "verbosity": profile.verbosity,
            "interaction_count": len(profile.interaction_history)
        }
    
    def update_from_feedback(self, user_id: str, feedback: Dict[str, Any]):
        """Update persona from explicit feedback"""
        profile = self.get_profile(user_id)
        
        if "tone" in feedback:
            profile.tone = feedback["tone"]
        if "verbosity" in feedback:
            profile.verbosity = feedback["verbosity"]
        if "empathy" in feedback:
            profile.empathy_level = float(feedback["empathy"])
        if "trust" in feedback:
            profile.trust_level = float(feedback["trust"])
        
        profile.preferences.update(feedback)
    
    def _load_profiles(self):
        """Load persona profiles from disk"""
        profiles_file = self.data_dir / "persona_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct profiles (simplified)
                    logger.info("Persona profiles loaded")
            except Exception as e:
                logger.error(f"Failed to load profiles: {e}")
    
    def save_profiles(self):
        """Save persona profiles to disk"""
        profiles_file = self.data_dir / "persona_profiles.json"
        try:
            data = {
                user_id: {
                    "tone": p.tone,
                    "verbosity": p.verbosity,
                    "empathy_level": p.empathy_level,
                    "trust_level": p.trust_level,
                    "familiarity": p.familiarity,
                    "mood": {
                        "valence": p.mood.valence,
                        "arousal": p.mood.arousal,
                        "dominance": p.mood.dominance
                    },
                    "preferences": p.preferences
                }
                for user_id, p in self.profiles.items()
            }
            with open(profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Persona profiles saved")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    @property
    def profile(self) -> Dict[str, Any]:
        """Get default profile (for backward compatibility)"""
        return {
            "tone": self.default_profile.tone,
            "verbosity": self.default_profile.verbosity,
            "empathy_level": self.default_profile.empathy_level,
            "trust_level": self.default_profile.trust_level
        }

