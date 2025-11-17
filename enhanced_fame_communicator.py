#!/usr/bin/env python3
"""
F.A.M.E. - Enhanced Communicator
Full communication capabilities with voice and chat
"""

import sys
import os
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Try to import tkinter
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("ERROR: Tkinter not available. Please install tkinter.")
    sys.exit(1)

import threading
import asyncio
from datetime import datetime
import logging

# Import communication modules
try:
    from core.enhanced_chat_interface import EnhancedChatInterface
    from core.speech_to_text import SpeechToTextEngine
    from core.text_to_speech import TextToSpeechEngine
except ImportError as e:
    print(f"ERROR: Failed to import communication modules: {e}")
    sys.exit(1)

# Try to import market oracle
try:
    from core.enhanced_market_oracle import EnhancedMarketOracle
    MARKET_ORACLE_AVAILABLE = True
except ImportError:
    MARKET_ORACLE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced market oracle not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAMECommunicator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("F.A.M.E. - AI Communication Hub")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')
        
        # Initialize communication systems
        self.chat_interface = EnhancedChatInterface()
        self.stt_engine = SpeechToTextEngine()
        self.tts_engine = TextToSpeechEngine()
        
        if MARKET_ORACLE_AVAILABLE:
            self.market_oracle = EnhancedMarketOracle()
        else:
            self.market_oracle = None
        
        # Voice state
        self.is_listening = False
        
        self.setup_interface()
        self.setup_voice_callbacks()
    
    def setup_interface(self):
        """Setup communication interface"""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#0a0a0a')
        header_frame.pack(fill='x', pady=20)
        
        title = tk.Label(header_frame, text="🎤 F.A.M.E. - AI COMMUNICATION HUB",
                        font=("Arial", 24, "bold"), fg="#00ff00", bg="#0a0a0a")
        title.pack()
        
        subtitle = tk.Label(header_frame, text="Voice Chat • Business Intelligence • Real-time Analysis",
                           font=("Arial", 12), fg="#cccccc", bg="#0a0a0a")
        subtitle.pack()
        
        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tabs = {
            'voice_chat': ttk.Frame(self.notebook),
            'text_chat': ttk.Frame(self.notebook),
            'business_analysis': ttk.Frame(self.notebook),
            'system_status': ttk.Frame(self.notebook)
        }
        
        for name, frame in self.tabs.items():
            self.notebook.add(frame, text=name.replace('_', ' ').title())
        
        self.setup_voice_chat_tab()
        self.setup_text_chat_tab()
        self.setup_business_analysis_tab()
        self.setup_system_status_tab()
        
        # Console
        self.setup_console()
    
    def setup_voice_chat_tab(self):
        """Setup voice chat interface"""
        frame = self.tabs['voice_chat']
        
        # Voice controls
        control_frame = tk.Frame(frame, bg='#1a1a1a')
        control_frame.pack(fill='x', pady=10, padx=10)
        
        self.voice_status = tk.Label(control_frame, text="🔴 VOICE INACTIVE", 
                                   font=("Arial", 12, "bold"), fg="red", bg="#1a1a1a")
        self.voice_status.pack(side='left', padx=10)
        
        self.listen_btn = tk.Button(control_frame, text="🎤 Start Listening", 
                                  command=self.toggle_listening,
                                  bg="#cc0000", fg="white", font=("Arial", 10, "bold"))
        self.listen_btn.pack(side='left', padx=5)
        
        self.speak_btn = tk.Button(control_frame, text="🔊 Test Voice", 
                                 command=self.test_voice,
                                 bg="#0066cc", fg="white", font=("Arial", 10))
        self.speak_btn.pack(side='left', padx=5)
        
        # Persona selection
        persona_frame = tk.Frame(frame, bg='#1a1a1a')
        persona_frame.pack(fill='x', pady=5, padx=10)
        
        tk.Label(persona_frame, text="AI Persona:", fg="white", bg="#1a1a1a").pack(side='left')
        
        self.persona_var = tk.StringVar(value="business_expert")
        personas = [("Business Expert", "business_expert"), 
                   ("Technical Advisor", "technical_advisor"),
                   ("Strategic Thinker", "strategic_thinker")]
        
        for text, value in personas:
            tk.Radiobutton(persona_frame, text=text, variable=self.persona_var,
                          value=value, fg="white", bg="#1a1a1a", selectcolor="#2a2a2a").pack(side='left', padx=10)
        
        # Voice conversation display
        self.voice_display = scrolledtext.ScrolledText(frame, height=20, bg="#000000", fg="#00ff00",
                                                     font=("Arial", 11))
        self.voice_display.pack(fill='both', expand=True, padx=10, pady=10)
        self.voice_display.insert(tk.END, "🎤 FAME Voice System Ready\n")
        self.voice_display.insert(tk.END, "Click 'Start Listening' to begin voice conversation\n\n")
    
    def setup_text_chat_tab(self):
        """Setup text chat interface"""
        frame = self.tabs['text_chat']
        
        # Chat area
        self.chat_display = scrolledtext.ScrolledText(frame, height=20, bg="#000000", fg="#00ff00",
                                                    font=("Arial", 11))
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input area
        input_frame = tk.Frame(frame, bg='#1a1a1a')
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.chat_input = tk.Text(input_frame, height=3, bg="#2a2a2a", fg="white",
                                font=("Arial", 11))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        send_btn = tk.Button(input_frame, text="Send", command=self.send_chat_message,
                           bg="#00aa00", fg="white", font=("Arial", 10, "bold"))
        send_btn.pack(side='right')
        
        # Add sample questions
        sample_frame = tk.Frame(frame, bg='#1a1a1a')
        sample_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(sample_frame, text="Try asking:", fg="white", bg="#1a1a1a").pack(side='left')
        
        samples = [
            "Analyze Apple stock",
            "Build a trading bot",
            "Business strategy advice",
            "Technology trends analysis"
        ]
        
        for sample in samples:
            btn = tk.Button(sample_frame, text=sample, 
                          command=lambda s=sample: self.insert_sample_question(s),
                          bg="#444444", fg="white", font=("Arial", 8))
            btn.pack(side='left', padx=2)
    
    def setup_business_analysis_tab(self):
        """Setup business intelligence tab"""
        frame = self.tabs['business_analysis']
        
        # Analysis controls
        control_frame = tk.Frame(frame, bg='#1a1a1a')
        control_frame.pack(fill='x', pady=10, padx=10)
        
        # Stock analysis
        stock_frame = tk.Frame(control_frame, bg='#1a1a1a')
        stock_frame.pack(side='left', padx=10)
        
        tk.Label(stock_frame, text="Stock Analysis:", fg="white", bg="#1a1a1a").pack()
        self.stock_entry = tk.Entry(stock_frame, width=10)
        self.stock_entry.pack(side='left', padx=5)
        self.stock_entry.insert(0, "AAPL")
        
        analyze_stock_btn = tk.Button(stock_frame, text="Analyze", 
                                    command=self.analyze_stock,
                                    bg="#006600", fg="white")
        analyze_stock_btn.pack(side='left', padx=5)
        
        # Business questions
        biz_frame = tk.Frame(control_frame, bg='#1a1a1a')
        biz_frame.pack(side='left', padx=20)
        
        tk.Label(biz_frame, text="Business Intelligence:", fg="white", bg="#1a1a1a").pack()
        
        biz_questions = [
            "Market trends analysis",
            "Competitive landscape",
            "Investment opportunities",
            "Risk assessment"
        ]
        
        for question in biz_questions:
            btn = tk.Button(biz_frame, text=question,
                          command=lambda q=question: self.ask_business_question(q),
                          bg="#660066", fg="white", font=("Arial", 8))
            btn.pack(side='left', padx=2)
        
        # Analysis output
        self.analysis_output = scrolledtext.ScrolledText(frame, height=20, bg="#000000", fg="#00ff00",
                                                       font=("Arial", 11))
        self.analysis_output.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_system_status_tab(self):
        """Setup system status tab"""
        frame = self.tabs['system_status']
        
        status_text = f"""
F.A.M.E. COMMUNICATION SYSTEM STATUS
====================================

🤖 AI CAPABILITIES:

• Voice Recognition: {'ACTIVE' if self.stt_engine.recognizer else 'NOT AVAILABLE'}
• Text-to-Speech: {'ACTIVE' if self.tts_engine.engine else 'NOT AVAILABLE'}  
• Business Intelligence: ACTIVE
• Market Analysis: {'ACTIVE' if MARKET_ORACLE_AVAILABLE else 'NOT AVAILABLE'}
• Code Generation: ACTIVE

🎯 TESTING MODULES:

1. INTELLECTUAL CAPACITY:

   - Strategic Thinking
   - Business Acumen
   - Technical Expertise
   - Financial Analysis

2. COMMUNICATION MODES:

   - Voice Conversations
   - Text Chat
   - Business Q&A
   - Real-time Analysis

3. SPECIALIZED KNOWLEDGE:

   - Market Trends & Analysis
   - Investment Strategies
   - Technology Architecture
   - Business Development

🚀 READY FOR INTELLIGENCE TESTING:

Ask FAME about:

• Complex business strategies
• Market analysis and predictions
• Technology architecture decisions
• Investment opportunities and risks
• Competitive positioning
• Innovation opportunities
"""
        
        status_display = scrolledtext.ScrolledText(frame, bg="#000000", fg="#00ff00",
                                                 font=("Consolas", 10))
        status_display.pack(fill='both', expand=True, padx=10, pady=10)
        status_display.insert(tk.END, status_text)
        status_display.config(state=tk.DISABLED)
    
    def setup_console(self):
        """Setup system console"""
        console_frame = tk.Frame(self.root, bg="black")
        console_frame.pack(fill='x', side='bottom')
        
        self.console = scrolledtext.ScrolledText(console_frame, bg="black", fg="#00ff00",
                                               font=("Consolas", 9), height=6)
        self.console.pack(fill='x', padx=10, pady=5)
        self.log_message("🎤 FAME Communication System Initialized", "success")
    
    def setup_voice_callbacks(self):
        """Setup voice recognition callbacks"""
        self.stt_engine.add_callback(self.handle_voice_input)
    
    def handle_voice_input(self, text: str):
        """Handle recognized voice input"""
        self.root.after(0, lambda: self.process_voice_command(text))
    
    def process_voice_command(self, text: str):
        """Process voice command"""
        self.log_message(f"🎤 Voice input: {text}", "info")
        
        # Display in voice chat
        self.voice_display.insert(tk.END, f"\n👤 YOU: {text}\n", "user")
        self.voice_display.see(tk.END)
        
        # Process with AI
        threading.Thread(target=self.process_ai_response, args=(text, "voice"), daemon=True).start()
    
    def process_ai_response(self, message: str, interface: str = "text"):
        """Process message with AI and get response"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            persona = self.persona_var.get()
            
            async def get_response():
                return await self.chat_interface.chat_with_fame(message, persona)
            
            response_data = loop.run_until_complete(get_response())
            loop.close()
            
            # Update UI in main thread
            self.root.after(0, lambda: self.display_ai_response(response_data, interface))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"AI Error: {e}", "error"))
    
    def display_ai_response(self, response_data: dict, interface: str):
        """Display AI response"""
        if "error" in response_data:
            response_text = f"Error: {response_data['error']}"
            self.log_message(f"AI response error: {response_data['error']}", "error")
        else:
            response_text = response_data["response"]
            self.log_message(f"🤖 AI responded ({response_data['persona']})", "success")
        
        # Display in appropriate interface
        if interface == "voice":
            self.voice_display.insert(tk.END, f"🤖 FAME: {response_text}\n", "assistant")
            self.voice_display.see(tk.END)
            # Speak response
            self.tts_engine.speak_async(response_text)
        else:
            self.chat_display.insert(tk.END, f"\n🤖 FAME: {response_text}\n", "assistant")
            self.chat_display.see(tk.END)
    
    def toggle_listening(self):
        """Toggle voice listening"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Start voice listening"""
        def start_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stt_engine.start_listening())
        
        threading.Thread(target=start_async, daemon=True).start()
        self.is_listening = True
        self.listen_btn.config(text="🔴 Stop Listening", bg="#00aa00")
        self.voice_status.config(text="🟢 LISTENING ACTIVELY", fg="#00ff00")
        self.log_message("🎤 Voice listening activated", "success")
    
    def stop_listening(self):
        """Stop voice listening"""
        self.stt_engine.stop_listening()
        self.is_listening = False
        self.listen_btn.config(text="🎤 Start Listening", bg="#cc0000")
        self.voice_status.config(text="🔴 VOICE INACTIVE", fg="red")
        self.log_message("🎤 Voice listening stopped", "info")
    
    def test_voice(self):
        """Test TTS voice"""
        test_text = "Hello! I am FAME AI, ready for intelligent conversation and business analysis."
        self.tts_engine.speak_async(test_text)
        self.log_message("🔊 Voice test activated", "info")
    
    def send_chat_message(self):
        """Send chat message"""
        message = self.chat_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        self.chat_input.delete("1.0", tk.END)
        self.chat_display.insert(tk.END, f"\n👤 YOU: {message}\n", "user")
        self.chat_display.see(tk.END)
        
        self.log_message(f"💬 Chat sent: {message[:50]}...", "info")
        threading.Thread(target=self.process_ai_response, args=(message, "text"), daemon=True).start()
    
    def insert_sample_question(self, question: str):
        """Insert sample question"""
        self.chat_input.delete("1.0", tk.END)
        self.chat_input.insert("1.0", question)
    
    def analyze_stock(self):
        """Analyze stock"""
        symbol = self.stock_entry.get().strip().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a stock symbol")
            return
        
        self.log_message(f"📈 Analyzing stock: {symbol}", "info")
        
        # Use finance-first responder for stock analysis
        threading.Thread(target=self.process_ai_response, args=(f"Analyze {symbol} stock", "text"), daemon=True).start()
    
    def ask_business_question(self, question: str):
        """Ask business intelligence question"""
        self.log_message(f"🤔 Business question: {question}", "info")
        
        # Use the chat interface for business questions
        threading.Thread(target=self.process_ai_response, args=(question, "text"), daemon=True).start()
    
    def log_message(self, message: str, message_type: str = "info"):
        """Log message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "#00ff00",
            "warning": "#ffff00",
            "error": "#ff0000",
            "success": "#00ffff"
        }
        
        color = colors.get(message_type, "#00ff00")
        
        self.console.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.console.insert(tk.END, f"{message}\n", message_type)
        
        self.console.tag_configure("timestamp", foreground="#888888")
        self.console.tag_configure(message_type, foreground=color)
        
        self.console.see(tk.END)
        self.root.update()


def main():
    """Launch FAME Communication System"""
    if not TKINTER_AVAILABLE:
        print("ERROR: Tkinter not available")
        sys.exit(1)
    
    app = FAMECommunicator()
    app.root.mainloop()


if __name__ == "__main__":
    main()
