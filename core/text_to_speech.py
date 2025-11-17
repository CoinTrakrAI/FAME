#!/usr/bin/env python3
"""
F.A.M.E. - Text-to-Speech Engine
Natural voice responses for FAME
"""

import threading
import queue
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available - TTS features will be limited")


class TextToSpeechEngine:
    """Advanced TTS with multiple voice options"""
    
    def __init__(self):
        if not PYTTSX3_AVAILABLE:
            self.engine = None
            logger.warning("TTS engine not available")
            return
        
        try:
            self.engine = pyttsx3.init()
            self.speech_queue = queue.Queue()
            self.is_speaking = False
            
            # Configure engine
            self._configure_engine()
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _configure_engine(self):
        """Configure TTS engine"""
        if not self.engine:
            return
        
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Set voice (try to find a natural sounding voice)
            if len(voices) > 0:
                # Prefer female voices for natural sound
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech properties
            self.engine.setProperty('rate', 180)  # Speed percent
            self.engine.setProperty('volume', 0.8)  # Volume 0-1
        except Exception as e:
            logger.warning(f"TTS configuration error: {e}")
    
    async def speak(self, text: str, wait: bool = False):
        """Speak text"""
        if not self.engine:
            logger.warning("TTS engine not available")
            return
        
        def _speak():
            try:
                self.engine.say(text)
                if wait:
                    self.engine.runAndWait()
                else:
                    self.engine.startLoop(False)
                    self.engine.iterate()
                    self.engine.endLoop()
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
        
        # Run in thread to avoid blocking
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        
        if wait:
            thread.join()
    
    def speak_async(self, text: str):
        """Speak text asynchronously (add to queue)"""
        if not self.engine:
            logger.warning("TTS engine not available")
            return
        
        self.speech_queue.put(text)
        if not self.is_speaking:
            self._start_speech_worker()
    
    def _start_speech_worker(self):
        """Start background speech worker"""
        if not self.engine:
            return
        
        def speech_worker():
            self.is_speaking = True
            while not self.speech_queue.empty():
                try:
                    text = self.speech_queue.get()
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"Speech worker error: {e}")
            self.is_speaking = False
        
        thread = threading.Thread(target=speech_worker, daemon=True)
        thread.start()
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get current voice configuration"""
        if not self.engine:
            return {
                "available": False,
                "error": "TTS engine not available"
            }
        
        try:
            voices = self.engine.getProperty('voices')
            return {
                "available": True,
                "rate": self.engine.getProperty('rate'),
                "volume": self.engine.getProperty('volume'),
                "voice": self.engine.getProperty('voice'),
                "voices_available": len(voices) if voices else 0
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    def set_voice_property(self, rate: int = None, volume: float = None):
        """Set voice properties"""
        if not self.engine:
            return
        
        try:
            if rate is not None:
                self.engine.setProperty('rate', rate)
            if volume is not None:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
        except Exception as e:
            logger.error(f"Failed to set voice property: {e}")
