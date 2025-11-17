#!/usr/bin/env python3
"""
F.A.M.E. 11.0 - Advanced Voice Interface
Natural conversation with cosmic AI
"""

import threading
import time
from typing import Dict, List, Any

# Voice libraries
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    sr = None
    pyttsx3 = None


class CosmicVoiceInterface:
    """Advanced voice interface with natural conversation"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.listening = False
        
        if not VOICE_AVAILABLE:
            return
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Voice settings
        self.voice_rate = 150
        self.voice_volume = 0.8
        self.conversation_context = []
        
        # Initialize
        self._setup_voice_engine()
    
    def _setup_voice_engine(self):
        """Setup voice engine"""
        if not VOICE_AVAILABLE:
            return
        
        try:
            # Configure TTS
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
            self.tts_engine.setProperty('rate', self.voice_rate)
            self.tts_engine.setProperty('volume', self.voice_volume)
            
            # Configure recognizer
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
        except Exception as e:
            print(f"Voice setup error: {e}")
    
    def start_conversation_mode(self):
        """Start natural conversation mode"""
        if not VOICE_AVAILABLE:
            print("Voice libraries not available")
            return
        
        self.listening = True
        self.conversation_thread = threading.Thread(target=self._conversation_loop, daemon=True)
        self.conversation_thread.start()
        
        self.speak("Cosmic intelligence activated. I'm listening, creator.")
    
    def stop_conversation_mode(self):
        """Stop conversation mode"""
        self.listening = False
        if VOICE_AVAILABLE:
            self.speak("Entering standby mode. Awaiting your command.")
    
    def _conversation_loop(self):
        """Main conversation loop"""
        while self.listening and VOICE_AVAILABLE:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                    text = self.recognizer.recognize_google(audio)
                    self._process_speech(text)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self.speak("I didn't catch that. Could you repeat?")
            except Exception as e:
                print(f"Voice error: {e}")
                time.sleep(1)
    
    def _process_speech(self, text: str):
        """Process spoken text"""
        print(f"Voice command: {text}")
        
        # Add to conversation context
        self.conversation_context.append({"role": "user", "content": text})
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        # Process command
        response = self._generate_ai_response(text)
        self.speak(response)
        
        # Update UI
        self._execute_voice_command(text)
    
    def _generate_ai_response(self, text: str) -> str:
        """Generate AI response"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['dashboard', 'home', 'main']):
            return "Navigating to cosmic dashboard."
        elif any(word in text_lower for word in ['hack', 'penetrate', 'attack']):
            return "Opening universal hacking suite."
        elif any(word in text_lower for word in ['develop', 'build', 'create']):
            return "Launching universal development environment."
        elif any(word in text_lower for word in ['cloud', 'aws', 'azure']):
            return "Accessing cloud dominance panel."
        elif any(word in text_lower for word in ['god mode', 'cosmic', 'unlimited']):
            return "Activating cosmic god mode."
        elif any(word in text_lower for word in ['autonomous', 'self', 'auto']):
            return "Initiating autonomous operation mode."
        elif any(word in text_lower for word in ['sleep', 'rest', 'stop']):
            return "Entering standby mode."
        elif any(word in text_lower for word in ['thank', 'thanks']):
            return "You're welcome, creator."
        else:
            return f"I understand: {text}. How would you like me to proceed?"
    
    def _execute_voice_command(self, text: str):
        """Execute actions based on voice commands"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['dashboard', 'home']):
            self.main_app.after(0, self.main_app.show_dashboard)
        elif any(word in text_lower for word in ['hack', 'penetrate']):
            self.main_app.after(0, self.main_app.show_hacking_suite)
        elif any(word in text_lower for word in ['develop', 'build']):
            self.main_app.after(0, self.main_app.show_development)
        elif any(word in text_lower for word in ['cloud']):
            self.main_app.after(0, self.main_app.show_cloud_control)
        elif any(word in text_lower for word in ['god mode', 'cosmic']):
            self.main_app.after(0, self.main_app.show_god_mode)
        elif any(word in text_lower for word in ['settings', 'configure']):
            self.main_app.after(0, self.main_app.show_settings)
    
    def speak(self, text: str):
        """Speak text"""
        if not VOICE_AVAILABLE:
            print(f"TTS: {text}")
            return
        
        def _speak():
            try:
                sentences = text.split('. ')
                for sentence in sentences:
                    if sentence.strip():
                        self.tts_engine.say(sentence.strip())
                        self.tts_engine.runAndWait()
                        time.sleep(0.3)
            except Exception as e:
                print(f"Speech error: {e}")
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def set_voice_properties(self, rate: int = None, volume: float = None):
        """Set voice properties"""
        if not VOICE_AVAILABLE:
            return
        
        if rate is not None:
            self.voice_rate = rate
            self.tts_engine.setProperty('rate', rate)
        
        if volume is not None:
            self.voice_volume = volume
            self.tts_engine.setProperty('volume', volume)

