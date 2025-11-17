#!/usr/bin/env python3
"""
F.A.M.E. - Speech-to-Text Engine
Real-time voice recognition for natural interaction
"""

import threading
import queue
import asyncio
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not available - voice features will be limited")

# Try to import pyaudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("pyaudio not available - voice features will be limited")


class SpeechToTextEngine:
    """Advanced speech recognition with multiple backends"""
    
    def __init__(self):
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = None
            self.microphone = None
            logger.warning("Speech recognition not available")
            return
        
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            logger.info("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone calibrated!")
        except Exception as e:
            logger.warning(f"Microphone initialization failed: {e}")
            self.microphone = None
        
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.callbacks = []
    
    def add_callback(self, callback: Callable[[str], None]):
        """Add callback for processed text"""
        self.callbacks.append(callback)
    
    async def start_listening(self):
        """Start continuous listening"""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.microphone:
            logger.error("Speech recognition not available")
            return
        
        self.is_listening = True
        
        def listen_worker():
            while self.is_listening:
                try:
                    logger.debug("Listening...")
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                    # Process audio
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        text = loop.run_until_complete(self.process_audio(audio))
                        loop.close()
                        
                        if text:
                            for callback in self.callbacks:
                                callback(text)
                    except Exception as e:
                        logger.error(f"Audio processing error: {e}")
                            
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Listening error: {e}")
                    continue
        
        # Start listening in background thread
        thread = threading.Thread(target=listen_worker, daemon=True)
        thread.start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
    
    async def process_audio(self, audio) -> Optional[str]:
        """Process audio with multiple recognition backends"""
        if not self.recognizer:
            return None
        
        try:
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Google STT: {text}")
                return text
            except sr.UnknownValueError:
                logger.debug("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                logger.warning(f"Google Speech Recognition error: {e}")
            
            # Fallback: Sphinx (offline)
            try:
                text = self.recognizer.recognize_sphinx(audio)
                logger.info(f"Sphinx STT: {text}")
                return text
            except sr.UnknownValueError:
                logger.debug("Sphinx could not understand audio")
            except Exception as e:
                logger.debug(f"Sphinx error: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return None
    
    async def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file"""
        if not self.recognizer:
            return {
                "success": False,
                "error": "Speech recognition not available",
                "file": audio_file_path
            }
        
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                
                return {
                    "success": True,
                    "text": text,
                    "file": audio_file_path,
                    "engine": "google"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": audio_file_path
            }
