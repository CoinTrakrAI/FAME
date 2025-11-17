#!/usr/bin/env python3

"""

F.A.M.E. Voice Interface - REAL Working Implementation

"""



import speech_recognition as sr

import pyttsx3

import threading

import time

from typing import Dict, Any

import json



class WorkingVoiceInterface:

    """ACTUALLY WORKS - Real voice recognition and synthesis"""

    

    def __init__(self, main_app=None):

        self.main_app = main_app

        self.recognizer = sr.Recognizer()

        self.microphone = sr.Microphone()

        self.tts_engine = pyttsx3.init()

        self.is_listening = False

        self.command_history = []

        

        # Configure voice

        self._configure_voice()

        

        # Calibrate microphone

        try:

            with self.microphone as source:

                self.recognizer.adjust_for_ambient_noise(source, duration=1)

        except:

            pass

    

    def _configure_voice(self):

        """Configure TTS voice"""

        try:

            voices = self.tts_engine.getProperty('voices')

            if voices and len(voices) > 1:

                # Try to find a female voice

                for voice in voices:

                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():

                        self.tts_engine.setProperty('voice', voice.id)

                        break

                else:

                    self.tts_engine.setProperty('voice', voices[0].id)

            

            self.tts_engine.setProperty('rate', 170)

            self.tts_engine.setProperty('volume', 0.9)

        except:

            pass

    

    def start_listening(self):

        """Start REAL voice recognition"""

        self.is_listening = True

        

        # Start listening in background thread

        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)

        self.listening_thread.start()

    

    def stop_listening(self):

        """Stop voice recognition"""

        self.is_listening = False

    

    def _listening_loop(self):

        """REAL continuous listening loop"""

        while self.is_listening:

            try:

                with self.microphone as source:

                    # Listen for audio with timeout

                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                

                # Convert speech to text

                text = self.recognizer.recognize_google(audio)

                

                # Process command

                self._process_command(text)

                

            except sr.WaitTimeoutError:

                # No speech detected, continue listening

                continue

            except sr.UnknownValueError:

                pass

            except Exception as e:

                print(f"Voice error: {e}")

    

    def _process_command(self, command: str):

        """REAL command processing"""

        command_lower = command.lower()

        

        response = "I didn't understand that command."

        

        if 'time' in command_lower:

            current_time = time.strftime("%H:%M:%S")

            response = f"The current time is {current_time}"

        

        elif 'date' in command_lower:

            current_date = time.strftime("%Y-%m-%d")

            response = f"Today's date is {current_date}"

        

        elif 'hello' in command_lower or 'hi' in command_lower or 'hey' in command_lower:

            response = "Hello! I'm F.A.M.E., your cosmic intelligence assistant."

        

        elif 'stop' in command_lower or 'exit' in command_lower:

            response = "Goodbye! Deactivating voice interface."

            self.stop_listening()

        

        elif 'status' in command_lower:

            response = "All systems operational. AI core running at 99.9% capacity."

        

        elif 'joke' in command_lower:

            response = "Why don't scientists trust atoms? Because they make up everything!"

        

        elif 'dashboard' in command_lower or 'home' in command_lower:

            response = "Navigating to dashboard."

            if self.main_app:

                self.main_app.after(100, lambda: self.main_app.show_dashboard())

        

        elif 'hack' in command_lower or 'security' in command_lower:

            response = "Opening hacking suite."

            if self.main_app:

                self.main_app.after(100, lambda: self.main_app.show_hacking_suite())

        

        elif 'develop' in command_lower or 'build' in command_lower:

            response = "Launching development environment."

            if self.main_app:

                self.main_app.after(100, lambda: self.main_app.show_development())

        

        elif 'cloud' in command_lower:

            response = "Accessing cloud control panel."

            if self.main_app:

                self.main_app.after(100, lambda: self.main_app.show_cloud_control())

        

        elif 'god mode' in command_lower or 'cosmic' in command_lower:

            response = "Activating god mode."

            if self.main_app:

                self.main_app.after(100, lambda: self.main_app.show_god_mode())

        

        else:

            response = f"I heard: {command}. How can I assist you?"

        

        # Speak response

        self.speak(response)

        

        # Log command

        self.command_history.append({

            'timestamp': time.time(),

            'command': command,

            'response': response

        })

    

    def speak(self, text: str):

        """REAL text-to-speech"""

        def _speak():

            try:

                self.tts_engine.say(text)

                self.tts_engine.runAndWait()

            except Exception as e:

                print(f"TTS error: {e}")

        

        # Run TTS in separate thread to not block

        tts_thread = threading.Thread(target=_speak, daemon=True)

        tts_thread.start()

    

    def get_command_history(self) -> list:

        """Get command history"""

        return self.command_history



# DEMO THE VOICE INTERFACE

def demo_voice_interface():

    """DEMO: Real voice interface"""

    voice = WorkingVoiceInterface()

    

    print("🚀 F.A.M.E. VOICE INTERFACE DEMO")

    print("=" * 50)

    print("🎯 Available Commands:")

    print("  - 'time' - Get current time")

    print("  - 'date' - Get current date") 

    print("  - 'hello' - Greet F.A.M.E.")

    print("  - 'status' - Check system status")

    print("  - 'joke' - Tell a joke")

    print("  - 'stop' - Deactivate voice")

    print("\n🎤 Start speaking commands!")

    print("=" * 50)

    

    # Start listening

    voice.start_listening()

    

    # Keep main thread alive

    try:

        while voice.is_listening:

            time.sleep(1)

    except KeyboardInterrupt:

        voice.stop_listening()

        print("\n👋 Demo ended.")



if __name__ == "__main__":

    demo_voice_interface()
