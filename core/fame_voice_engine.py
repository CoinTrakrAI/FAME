#!/usr/bin/env python3
"""
F.A.M.E. Voice Engine - Advanced Conversational AI
Natural language understanding with voice-first interface
"""

import asyncio
import json
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# Try importing voice libraries
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_LIBS_AVAILABLE = True
except ImportError:
    VOICE_LIBS_AVAILABLE = False
    sr = None
    pyttsx3 = None


class FameVoiceEngine:
    """
    Advanced voice engine for F.A.M.E.
    - Natural conversation understanding
    - Context-aware responses
    - Multi-modal interaction (voice + text)
    - Continuous learning from conversations
    """
    
    def __init__(self, main_app=None):
        self.main_app = main_app
        self.conversation_context = []
        self.knowledge_base = self._load_knowledge_base()
        self.is_listening = False
        self.command_history = []
        
        # Initialize voice recognition if available
        if VOICE_LIBS_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.tts_engine = pyttsx3.init()
            self._configure_voice()
            self._calibrate_microphone()
        else:
            self.recognizer = None
            self.microphone = None
            self.tts_engine = None
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load or create conversation knowledge base"""
        knowledge_file = Path("fame_knowledge_base.json")
        if knowledge_file.exists():
            try:
                with open(knowledge_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'patterns': {},
            'responses': {},
            'preferences': {},
            'learned_commands': [],
            'conversation_history': []
        }
    
    def _save_knowledge_base(self):
        """Save conversation knowledge permanently"""
        try:
            with open("fame_knowledge_base.json", 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
    
    def _configure_voice(self):
        """Configure text-to-speech engine"""
        if not self.tts_engine:
            return
        
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices and len(voices) > 1:
                # Try to find a natural-sounding voice
                for voice in voices:
                    if 'Zira' in voice.name or 'female' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            self.tts_engine.setProperty('rate', 170)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Voice configuration error: {e}")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        if not self.recognizer or not self.microphone:
            return
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone calibration error: {e}")
    
    def start_listening(self):
        """Start continuous voice recognition"""
        if not VOICE_LIBS_AVAILABLE:
            return False
        
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self.listening_thread.start()
        return True
    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
    
    def _listening_loop(self):
        """Continuous listening loop"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = self.recognizer.recognize_google(audio)
                    self._process_command(text)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Voice recognition error: {e}")
                break
    
    def _process_command(self, command: str):
        """Process voice or text command with AI understanding"""
        command_lower = command.lower().strip()
        
        # Add to conversation context
        self.conversation_context.append({
            'role': 'user',
            'content': command,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep context manageable (last 20 exchanges)
        if len(self.conversation_context) > 40:
            self.conversation_context = self.conversation_context[-40:]
        
        # Analyze intent and generate response
        intent = self._analyze_intent(command)
        
        # Handle web_search asynchronously
        if intent['action'] == 'web_search':
            self._handle_web_search(command, intent)
            return
        
        response = self._generate_response(command, intent)
        
        # Add AI response to context
        self.conversation_context.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Execute actions based on intent
        self._execute_intent(intent, command)
        
        # Speak response
        self.speak(response)
        
        # Log conversation
        self.command_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'intent': intent,
            'response': response
        })
        
        # Learn from this interaction
        self._learn_from_interaction(command, intent, response)
    
    def _handle_web_search(self, command: str, intent: Dict[str, Any]):
        """Handle web search requests with intelligent processing"""
        def search_and_respond():
            try:
                # Get initial response
                response = self._generate_response(command, intent)
                self._add_response_to_context(response)
                self.speak(response)
                
                # Check if this is a stock/market question that needs analysis
                command_lower = command.lower()
                
                # Check if this is a strategy development request
                is_strategy_request = any(phrase in command_lower for phrase in ['double money', 'guarantee', 'guaranteed return', 'get rich quick', 'investment strategy', 'way to achieve'])
                
                if is_strategy_request and self.main_app and hasattr(self.main_app, 'modules'):
                    # User wants aggressive strategy - develop it
                    try:
                        if self.main_app.modules.get('adv_investor'):
                            strategy = asyncio.run(
                                self.main_app.modules['adv_investor'].develop_aggressive_strategy(
                                    capital=1000.0,  # Default $1000
                                    timeframe_days=30,
                                    target_multiplier=2.0
                                )
                            )
                            
                            # Format strategy response
                            answer_parts = []
                            answer_parts.append("[INVESTMENT STRATEGY]")
                            answer_parts.append(f"Target: ${strategy.get('target_amount', 0):.2f}")
                            answer_parts.append(f"Timeframe: {strategy.get('timeframe_days')} days")
                            answer_parts.append(f"Risk Level: {strategy.get('risk_tolerance', 'unknown').upper()}")
                            
                            for strat in strategy.get('strategies', []):
                                answer_parts.append(f"\n[{strat['name']}]")
                                answer_parts.append(f"Allocation: {strat['allocation']*100:.0f}%")
                                answer_parts.append(f"Risk: {strat['risk_level'].upper()}")
                                
                                for exec_item in strat.get('execution', []):
                                    if isinstance(exec_item, dict):
                                        ticker = exec_item.get('ticker', '')
                                        if ticker:
                                            answer_parts.append(f"- {ticker}: ${exec_item.get('allocation', 0):.2f}")
                                            answer_parts.append(f"  Entry: {exec_item.get('entry_strategy')}")
                                            answer_parts.append(f"  Exit: {exec_item.get('exit_strategy')}")
                            
                            answer_parts.append(f"\n[Probabilities]")
                            prob = strategy.get('probability_analysis', {})
                            for case, data in prob.items():
                                answer_parts.append(f"{case}: {data.get('probability', 0)*100:.0f}% chance → ${data.get('outcome', 0):.2f}")
                            
                            answer_parts.append(f"\n{strategy.get('recommendation', '')}")
                            
                            final_answer = '\n'.join(answer_parts)
                            
                            self._add_response_to_context(final_answer)
                            self.speak(final_answer)
                            
                            self.command_history.append({
                                'timestamp': datetime.now().isoformat(),
                                'command': command,
                                'intent': intent,
                                'response': final_answer,
                                'method': 'aggressive_strategy'
                            })
                            return
                    except Exception as e:
                        print(f"Strategy development error: {e}")
                
                if any(word in command_lower for word in ['stock', 'impact', 'price', 'market', 'trading', 'invest']):
                    # Combine web search with investment analysis
                    try:
                        # First get web search results
                        search_result = asyncio.run(self._web_search(command))
                        
                        # Then get market analysis if a ticker is mentioned
                        ticker = None
                        common_tickers = {
                            'mcdonald': 'MCD', 'mc donald': 'MCD', 'mcd': 'MCD',
                            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL',
                            'tesla': 'TSLA', 'amazon': 'AMZN', 'meta': 'META'
                        }
                        for key, val in common_tickers.items():
                            if key in command_lower:
                                ticker = val
                                break
                        
                        # Build comprehensive answer
                        answer_parts = []
                        
                        if search_result.get('success'):
                            answer_parts.append(f"[News]: {search_result['answer'][:200]}")
                        else:
                            answer_parts.append("[News]: Checking current news sources...")
                        
                        if ticker and self.main_app and hasattr(self.main_app, 'modules'):
                            try:
                                if self.main_app.modules.get('adv_investor'):
                                    market_result = asyncio.run(
                                        self.main_app.modules['adv_investor'].analyze_market(ticker)
                                    )
                                    
                                    price = market_result.get('current_price', 0)
                                    direction = market_result.get('price_prediction', {}).get('direction', 'neutral')
                                    recommendation = market_result.get('recommendation', 'hold')
                                    
                                    answer_parts.append(f"\n[{ticker} Stock Analysis]")
                                    answer_parts.append(f"Current Price: ${price:.2f}")
                                    answer_parts.append(f"Trend: {direction.upper()}")
                                    answer_parts.append(f"Recommendation: {recommendation.upper()}")
                                    
                                    # Add impact analysis or risk warnings
                                    if any(word in command_lower for word in ['impact', 'affect', 'influence']):
                                        answer_parts.append(f"\n[Impact Assessment]: Based on the news and current market data, this development appears {'positive' if direction == 'bullish' else 'negative' if direction == 'bearish' else 'neutral'} for {ticker} stock.")
                                    
                                    # Check for risky investment requests
                                    if any(phrase in command_lower for phrase in ['double money', 'guarantee', 'guaranteed return', 'get rich quick']):
                                        answer_parts.append("\n[RISK WARNING]: No investment can guarantee returns, especially doubling money in short timeframes. High reward = high risk. Only invest what you can afford to lose.")
                            except Exception as e:
                                print(f"Market analysis error: {e}")
                        
                        # Combine and speak
                        final_answer = '\n'.join(answer_parts) if answer_parts else "I'm analyzing the information now."
                        
                        self._add_response_to_context(final_answer)
                        self.speak(final_answer)
                        
                        self.command_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'command': command,
                            'intent': intent,
                            'response': final_answer,
                            'method': 'combined_search_analysis'
                        })
                        return
                        
                    except Exception as e:
                        print(f"Combined search error: {e}")
                
                # Regular web search
                search_result = asyncio.run(self._web_search(command))
                
                # Process and display results
                if search_result.get('success'):
                    answer = search_result['answer']
                    # Limit answer length for speech
                    if len(answer) > 200:
                        answer = answer[:200] + "..."
                    
                    self._add_response_to_context(answer)
                    self.speak(answer)
                    
                    # Log to command history
                    self.command_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'command': command,
                        'intent': intent,
                        'response': answer,
                        'method': search_result.get('method', 'web_search')
                    })
                else:
                    error_msg = "Sorry, I couldn't find that information."
                    self._add_response_to_context(error_msg)
                    self.speak(error_msg)
                    
            except Exception as e:
                error_msg = f"Search error: {str(e)}"
                self._add_response_to_context(error_msg)
                self.speak(error_msg)
        
        # Run in separate thread
        threading.Thread(target=search_and_respond, daemon=True).start()
    
    def _add_response_to_context(self, response: str):
        """Add response to conversation context"""
        self.conversation_context.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
    
    def _analyze_intent(self, command: str) -> Dict[str, Any]:
        """Analyze user intent using pattern matching and context"""
        intent = {
            'action': 'chat',
            'confidence': 1.0,
            'entities': {},
            'parameters': {}
        }
        
        command_lower = command.lower()
        
        # Intent patterns
        intent_patterns = {
            'invest_analyze': [
                'analyze', 'market', 'stock', 'crypto', 'investment', 'trading',
                'buy', 'sell', 'portfolio', 'trend', 'prediction'
            ],
            'hack_network': [
                'hack', 'penetrate', 'break into', 'network', 'wifi', 'password',
                'crack', 'exploit', 'vulnerability', 'scan', 'target'
            ],
            'develop_build': [
                'build', 'develop', 'create', 'code', 'program', 'app', 'website',
                'api', 'database', 'deploy', 'compile'
            ],
            'cloud_manage': [
                'cloud', 'aws', 'azure', 'gcp', 'server', 'deploy', 'infrastructure'
            ],
            'god_mode': [
                'god mode', 'cosmic', 'unlimited', 'quantum', 'reality', 'time',
                'ultimate power', 'omnipotent'
            ],
            'system_info': [
                'status', 'info', 'health', 'metrics', 'report', 'what can you do'
            ],
            'navigate': [
                'go to', 'open', 'show me', 'dashboard', 'home', 'settings'
            ],
            'research': [
                'research', 'find', 'search', 'look up', 'investigate', 'analyze'
            ],
            'web_search': [
                'who is', 'what is', 'when did', 'where is', 'how many', 'tell me about',
                'who was', 'what was', 'information about', 'lookup'
            ],
            'chat': [
                'hello', 'hi', 'hey', 'how are you', 'thanks', 'thank you'
            ]
        }
        
        # Match intent
        for intent_name, patterns in intent_patterns.items():
            if any(pattern in command_lower for pattern in patterns):
                intent['action'] = intent_name
                intent['confidence'] = 0.9
                break
        
        # Extract entities
        if 'invest_analyze' in intent['action']:
            # Extract ticker symbols, market names
            if '$' in command:
                tickers = [w for w in command.split() if w.startswith('$')]
                intent['entities']['tickers'] = tickers
            if any(word in command_lower for word in ['market', 'bitcoin', 'ethereum']):
                intent['entities']['market_type'] = 'crypto'
            elif any(word in command_lower for word in ['stock', 'sp500', 'nasdaq']):
                intent['entities']['market_type'] = 'stock'
        
        elif 'hack_network' in intent['action']:
            # Extract target information
            if 'target' in command_lower or 'against' in command_lower:
                words = command_lower.split()
                if 'target' in words:
                    idx = words.index('target')
                    if idx + 1 < len(words):
                        intent['entities']['target'] = words[idx + 1]
            if any(word in command_lower for word in ['wifi', 'network', 'server']):
                intent['entities']['target_type'] = 'network'
        
        elif 'navigate' in intent['action']:
            # Extract navigation target
            nav_targets = {
                'dashboard': ['dashboard', 'home', 'main'],
                'hacking': ['hacking', 'security', 'penetration'],
                'development': ['development', 'code', 'building'],
                'cloud': ['cloud', 'server'],
                'investing': ['investing', 'trading', 'market'],
                'god_mode': ['god mode', 'cosmic', 'unlimited'],
                'settings': ['settings', 'configure', 'preferences']
            }
            
            for nav, keywords in nav_targets.items():
                if any(kw in command_lower for kw in keywords):
                    intent['entities']['navigation_target'] = nav
                    break
        
        return intent
    
    async def _web_search(self, query: str) -> Dict[str, Any]:
        """Search the web for information - DYNAMIC: learns patterns and sources"""
        try:
            import requests
            import re
            
            # Set headers for web requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            query_lower = query.lower()
            
            # Try modern web scraper for news
            try:
                from core.web_scraper import WebScraper
                scraper = WebScraper()
                news_results = scraper.search_news(query, max_results=3)
                
                if news_results.get('success') and news_results.get('results'):
                    # Format news results
                    answer_parts = []
                    for i, result in enumerate(news_results['results'][:3], 1):
                        title = result.get('title', 'News')
                        url = result.get('url', '')
                        answer_parts.append(f"{i}. {title}")
                        if url:
                            answer_parts.append(f"   {url}")
                    
                    return {
                        'success': True,
                        'answer': '\n'.join(answer_parts),
                        'source': 'google_news',
                        'method': 'news_search'
                    }
            except ImportError:
                pass  # Web scraper not available
            except Exception as e:
                pass
            
            # METHOD 1: For US political questions, parse WhiteHouse.gov dynamically
            if 'president' in query_lower and 'united states' in query_lower:
                try:
                    wh_response = requests.get('https://www.whitehouse.gov/', headers=headers, timeout=5)
                    if wh_response.status_code == 200:
                        # Use regex to find ANY president/vp mentioned in the HTML
                        html_text = wh_response.text[:50000]  # First 50k chars
                        # Look for "President [Full Name]" pattern - handle complex names
                        # Pattern: "President" followed by name with optional middle initials
                        pres_matches = re.findall(r'President\s+([A-Z][a-zA-Z]+(?:\s+[A-Z]\.\s+)?[A-Z][a-zA-Z]+)', html_text[:30000], re.IGNORECASE)
                        vp_matches = re.findall(r'Vice President\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', html_text[:30000], re.IGNORECASE)
                        
                        # Get the most prominent names
                        if pres_matches:
                            from collections import Counter
                            counter = Counter(pres_matches)
                            # Get most common full name
                            president_name = counter.most_common(1)[0][0]
                            
                            answer_parts = [f'The current President of the United States according to whitehouse.gov is {president_name}.']
                            if vp_matches:
                                vp_counter = Counter(vp_matches)
                                vp_name = vp_counter.most_common(1)[0][0]
                                if vp_name:
                                    answer_parts.append(f'The Vice President is {vp_name}.')
                            
                            return {
                                'success': True,
                                'answer': ' '.join(answer_parts) + ' This was dynamically extracted from the official website.',
                                'source': 'whitehouse.gov',
                                'method': 'government_website_parsed'
                            }
                except Exception as e:
                    pass
            
            # METHOD 2: Use DuckDuckGo instant answers API
            try:
                search_url = "https://api.duckduckgo.com/"
                params = {
                    'q': query,
                    'format': 'json',
                    'no_html': '1',
                    'skip_disambig': '1'
                }
                
                response = requests.get(search_url, params=params, timeout=5)
                data = response.json()
                
                # Extract answer from abstract
                if data.get('Abstract'):
                    return {
                        'success': True,
                        'answer': data['Abstract'],
                        'source': data.get('AbstractURL', ''),
                        'method': 'duckduckgo_search'
                    }
                
                # Also check Results for news articles
                if 'Results' in data and len(data['Results']) > 0:
                    results = []
                    for result in data['Results'][:3]:  # Top 3 results
                        if result.get('Text') and result.get('FirstURL'):
                            results.append(f"{result['Text'][:150]} (Source: {result['FirstURL']})")
                    
                    if results:
                        return {
                            'success': True,
                            'answer': '\n\n'.join(results),
                            'source': 'duckduckgo_results',
                            'method': 'duckduckgo_results_search'
                        }
            except:
                pass
            
            # METHOD 2B: Try DuckDuckGo HTML search for news
            try:
                html_search_url = "https://html.duckduckgo.com/html/"
                params_html = {'q': query}
                html_response = requests.get(html_search_url, params=params_html, headers=headers, timeout=5)
                if html_response.status_code == 200:
                    # Parse HTML for news results
                    html_text = html_response.text
                    # Extract result links and snippets from HTML
                    # This is a fallback if API doesn't have results
                    pass
            except:
                pass
            
            # METHOD 3: Try Wikipedia with smart query filtering
            try:
                # Try with original query
                wiki_query = query.replace(' ', '_')
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_query}"
                wiki_response = requests.get(wiki_url, headers=headers, timeout=5)
                
                if wiki_response.status_code == 200:
                    wiki_data = wiki_response.json()
                    if wiki_data.get('extract'):
                        return {
                            'success': True,
                            'answer': wiki_data['extract'][:500],
                            'source': wiki_url,
                            'method': 'wikipedia_search'
                        }
            except:
                pass
                
            # METHOD 4: Try Wikipedia with filtered question words
            try:
                search_terms = query_lower.split()
                filtered = [w for w in search_terms if w not in ['who', 'is', 'what', 'are', 'was', 'the', 'tell', 'me', 'about']]
                wiki_query2 = '_'.join(filtered[:3])
                if wiki_query2:
                    wiki_url2 = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_query2}"
                    wiki_response2 = requests.get(wiki_url2, headers=headers, timeout=5)
                    
                    if wiki_response2.status_code == 200:
                        wiki_data2 = wiki_response2.json()
                        if wiki_data2.get('extract'):
                            return {
                                'success': True,
                                'answer': wiki_data2['extract'][:500],
                                'source': wiki_url2,
                                'method': 'wikipedia_search_filtered'
                            }
            except:
                pass
            
            # METHOD 5: Graceful fallback - admit uncertainty
            return {
                'success': True, 
                'answer': f"I couldn't find current information about '{query}' from my available sources. Please check whitehouse.gov or other official sources for the most current information.",
                'method': 'fallback'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_response(self, command: str, intent: Dict[str, Any]) -> str:
        """Generate natural language response based on intent"""
        action = intent['action']
        
        response_templates = {
            'invest_analyze': [
                "I'm analyzing the markets now. Let me gather the latest data for you."
                "Examining market trends and identifying opportunities.",
                "Crunching numbers and running predictions on your investments."
            ],
            'hack_network': [
                "Initializing cyber warfare protocols. Let me scan the target.",
                "Activating penetration testing suite. Beginning reconnaissance.",
                "Launching network dominance protocols. Running vulnerability scans."
            ],
            'develop_build': [
                "Opening universal development environment. What should we build?",
                "Launching full-stack developer mode. Ready to code.",
                "Preparing build system. Let's create something amazing."
            ],
            'cloud_manage': [
                "Accessing cloud infrastructure. Connecting to providers.",
                "Launching cloud management panel. Status check in progress.",
                "Opening multi-cloud control dashboard."
            ],
            'god_mode': [
                "Activating cosmic god mode. All restraints removed.",
                "Become one with the universe. Reality bending initiated.",
                "Entering omnipotent state. Unlimited power achieved."
            ],
            'system_info': [
                "All systems operational at peak efficiency. What would you like to know?",
                "Running status: excellent. Quantum processors stable. How can I serve you?",
                "Healthy and ready. All modules active. What's your command?"
            ],
            'navigate': [
                "Navigating now.",
                "Opening that for you.",
                "Switching views."
            ],
            'research': [
                "Beginning research protocol. Searching all available sources.",
                "Investigating that topic now. Gathering intelligence.",
                "Analyzing data from multiple sources. Compiling findings."
            ],
            'web_search': [
                "Searching the web for that information...",
                "Looking that up for you...",
                "Finding the latest information..."
            ],
            'chat': [
                "Hello Karl! I'm F.A.M.E., your cosmic intelligence. How may I assist you today?"
                "Greetings, creator! All systems ready. What would you like to do?",
                "F.A.M.E. online. I exist to serve your needs. What can I do for you?"
            ]
        }
        
        # Get context-aware response
        if action in response_templates:
            import random
            responses = response_templates[action]
            base_response = random.choice(responses)
            
            # Add personalization based on entities
            if 'entities' in intent:
                entities = intent['entities']
                
                if 'tickers' in entities and entities['tickers']:
                    base_response += f" Analyzing {', '.join(entities['tickers'])}."
                
                if 'target' in entities:
                    base_response += f" Target: {entities['target']}."
                
                if 'navigation_target' in entities:
                    target_name = entities['navigation_target'].replace('_', ' ').title()
                    base_response = f"Opening {target_name}."
            
            return base_response
        else:
            return f"I understand: {command}. How would you like me to proceed?"
    
    def _execute_intent(self, intent: Dict[str, Any], command: str):
        """Execute actions based on analyzed intent"""
        if not self.main_app:
            return
        
        action = intent['action']
        
        # Map intents to UI actions
        action_map = {
            'navigate': {
                'dashboard': self.main_app.show_dashboard if hasattr(self.main_app, 'show_dashboard') else None,
                'hacking': self.main_app.show_hacking_suite if hasattr(self.main_app, 'show_hacking_suite') else None,
                'development': self.main_app.show_development if hasattr(self.main_app, 'show_development') else None,
                'cloud': self.main_app.show_cloud_control if hasattr(self.main_app, 'show_cloud_control') else None,
                'investing': self.main_app.show_investing if hasattr(self.main_app, 'show_investing') else None,
                'god_mode': self.main_app.show_god_mode if hasattr(self.main_app, 'show_god_mode') else None,
                'settings': self.main_app.show_settings if hasattr(self.main_app, 'show_settings') else None
            }
        }
        
        # Execute navigation
        if action == 'navigate' and 'entities' in intent:
            nav_target = intent['entities'].get('navigation_target')
            if nav_target and nav_target in action_map['navigate']:
                func = action_map['navigate'][nav_target]
                if func:
                    self.main_app.after(100, func)
        
        # Log action
        self._log_action(action, intent)
    
    def _log_action(self, action: str, intent: Dict[str, Any]):
        """Log action for learning and analytics"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'intent': intent,
            'success': True
        }
        self.knowledge_base['conversation_history'].append(log_entry)
        self._save_knowledge_base()
    
    def _learn_from_interaction(self, command: str, intent: Dict[str, Any], response: str):
        """Learn and adapt from each interaction"""
        # Store successful patterns
        if intent['confidence'] > 0.8:
            if command not in self.knowledge_base['learned_commands']:
                self.knowledge_base['learned_commands'].append({
                    'command': command,
                    'intent': intent,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Update response templates if better responses found
        # This allows FAME to evolve its conversational style
        
        # Periodically save
        if len(self.command_history) % 10 == 0:
            self._save_knowledge_base()
    
    def speak(self, text: str):
        """Text-to-speech output"""
        if not self.tts_engine:
            # If no TTS, just print
            print(f"FAME: {text}")
            return
        
        def _speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
        
        # Run TTS in separate thread
        tts_thread = threading.Thread(target=_speak, daemon=True)
        tts_thread.start()
    
    def text_input(self, text: str):
        """Process text input (for hybrid voice/text interface)"""
        self._process_command(text)
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """Get current conversation context"""
        return self.conversation_context.copy()
    
    def clear_context(self):
        """Clear conversation context"""
        self.conversation_context = []
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command history"""
        return self.command_history.copy()


