#!/usr/bin/env python3
"""
F.A.M.E. - Speech-to-Text Engine
Real-time voice recognition for natural interaction
"""

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("[WARNING] speech_recognition not available. Install with: pip install SpeechRecognition")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("[WARNING] pyaudio not available. Install with: pip install pyaudio")

import threading
try:
    import queue
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False

import asyncio
from typing import Dict, Any, Optional, Callable
import json


class SpeechToTextEngine:
    """Advanced speech recognition with multiple backends"""
    
    def __init__(self):
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = None
            self.microphone = None
            print("[WARNING] Speech recognition not available")
        else:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                print("Calibrating microphone for ambient noise...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                print("Microphone calibrated!")
            except Exception as e:
                print(f"[WARNING] Microphone initialization failed: {e}")
                self.microphone = None
        
        if QUEUE_AVAILABLE:
            self.audio_queue = queue.Queue()
        else:
            self.audio_queue = None
        
        self.is_listening = False
        self.callbacks = []
    
    def add_callback(self, callback: Callable[[str], None]):
        """Add callback for processed text"""
        self.callbacks.append(callback)
    
    async def start_listening(self):
        """Start continuous listening"""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.microphone:
            print("[ERROR] Speech recognition not available")
            return
        
        self.is_listening = True
        
        def listen_worker():
            while self.is_listening:
                try:
                    print("Listening...")
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    
                    # Process audio
                    text = self.process_audio_sync(audio)
                    
                    if text:
                        for callback in self.callbacks:
                            try:
                                callback(text)
                            except Exception as e:
                                print(f"Callback error: {e}")
                                
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Listening error: {e}")
                    continue
        
        # Start listening in background thread
        thread = threading.Thread(target=listen_worker, daemon=True)
        thread.start()
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
    
    def process_audio_sync(self, audio) -> Optional[str]:
        """Process audio synchronously"""
        try:
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"Google STT: {text}")
                return text
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Google Speech Recognition error: {e}")
            
            # Fallback: Sphinx (offline) - may not be available
            try:
                text = self.recognizer.recognize_sphinx(audio)
                print(f"Sphinx STT: {text}")
                return text
            except sr.UnknownValueError:
                print("Sphinx could not understand audio")
            except Exception as e:
                print(f"Sphinx error: {e}")
            
            return None
            
        except Exception as e:
            print(f"Audio processing error: {e}")
            return None
    
    async def process_audio(self, audio) -> Optional[str]:
        """Process audio with multiple recognition backends (async wrapper)"""
        return self.process_audio_sync(audio)
    
    async def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file"""
        if not SPEECH_RECOGNITION_AVAILABLE:
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


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator interface for speech-to-text"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return {"error": "Speech recognition not available. Install SpeechRecognition and pyaudio."}
    
    audio_file = request.get("audio_file")
    if audio_file:
        async def transcribe():
            engine = SpeechToTextEngine()
            return await engine.transcribe_audio_file(audio_file)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(transcribe())
            return result
        finally:
            loop.close()
    else:
        return {"error": "No audio file provided"}

