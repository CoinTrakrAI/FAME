#!/usr/bin/env python3
"""
F.A.M.E. - ElevenLabs Text-to-Speech Integration
Premium voice synthesis for FAME
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
import threading
import queue
import asyncio

logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import io
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available - ElevenLabs audio playback will be limited")


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech Engine for FAME"""
    
    def __init__(self, api_key: str = None, voice_id: str = None):
        # FAME Identity - ElevenLabs API Key
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "f2e121c82fa6cd50dd7094029c335c5e3ac10d6cef698ca7a6c1770662de20b7")
        
        # FAME Voice ID
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "W9UYe7tosbBFWdXWaZZo")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
        # Initialize pygame for audio playback if available
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
    
    def speak(self, text: str, wait: bool = False):
        """Speak text using ElevenLabs TTS"""
        if not self.api_key or self.api_key.startswith('your_'):
            logger.warning("ElevenLabs API key not configured")
            return
        
        def _speak():
            try:
                audio_data = self._generate_speech(text)
                if audio_data:
                    self._play_audio(audio_data)
            except Exception as e:
                logger.error(f"ElevenLabs TTS error: {e}")
        
        # Run in thread to avoid blocking
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        
        if wait:
            thread.join()
    
    def speak_async(self, text: str):
        """Speak text asynchronously (add to queue)"""
        self.speech_queue.put(text)
        if not self.is_speaking:
            self._start_speech_worker()
    
    def _generate_speech(self, text: str) -> Optional[bytes]:
        """Generate speech audio from text"""
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Best quality model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    def _play_audio(self, audio_data: bytes):
        """Play audio data"""
        if PYGAME_AVAILABLE:
            try:
                audio_file = io.BytesIO(audio_data)
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            except Exception as e:
                logger.error(f"Audio playback error: {e}")
        else:
            # Fallback: save to file
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    f.write(audio_data)
                    temp_path = f.name
                
                # Try to play with system default player
                import platform
                if platform.system() == "Windows":
                    os.startfile(temp_path)
                elif platform.system() == "Darwin":
                    os.system(f"afplay {temp_path}")
                else:
                    os.system(f"mpg123 {temp_path}")
            except Exception as e:
                logger.warning(f"Could not play audio: {e}")
    
    def _start_speech_worker(self):
        """Start background speech worker"""
        def speech_worker():
            self.is_speaking = True
            while not self.speech_queue.empty():
                try:
                    text = self.speech_queue.get()
                    audio_data = self._generate_speech(text)
                    if audio_data:
                        self._play_audio(audio_data)
                except Exception as e:
                    logger.error(f"Speech worker error: {e}")
            self.is_speaking = False
        
        thread = threading.Thread(target=speech_worker, daemon=True)
        thread.start()
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get voice information"""
        return {
            "provider": "ElevenLabs",
            "voice_id": self.voice_id,
            "api_key_configured": bool(self.api_key and not self.api_key.startswith('your_')),
            "audio_playback_available": PYGAME_AVAILABLE
        }
    
    def test_voice(self) -> bool:
        """Test voice synthesis"""
        try:
            test_text = "Hello, I am FAME - Financial AI Mastermind Executive. Voice synthesis is working correctly."
            audio_data = self._generate_speech(test_text)
            if audio_data:
                self._play_audio(audio_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Voice test failed: {e}")
            return False

