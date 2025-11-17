#!/usr/bin/env python3
"""
FAME Chat UI - Simple text-based interface for speaking with FAME
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.brain import Brain

class FAME_Chat:
    def __init__(self):
        self.brain = Brain()
        self.conversation_history = []
        
    async def chat_loop(self):
        """Main chat loop"""
        print("=" * 80)
        print("FAME CHAT INTERFACE")
        print("=" * 80)
        print("Type 'quit', 'exit', or 'bye' to end the conversation")
        print("Type 'clear' to clear conversation history")
        print("Type 'evolution' to trigger self-evolution")
        print("=" * 80)
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("YOU: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("\nFAME: Goodbye! I'll be here when you need me.")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("[Conversation history cleared]\n")
                    continue
                
                if user_input.lower() in ['evolution', 'self-evolve', 'self evolve', 'fix bugs', 'improve yourself']:
                    print("\nFAME: Initiating self-evolution with knowledge from books...\n")
                    try:
                        from core.self_evolution import handle_evolution_request
                        result = handle_evolution_request(user_input)
                        print("FAME:", result.get('response', 'Evolution complete'))
                        print()
                        continue
                    except Exception as e:
                        print(f"FAME: Evolution error: {e}\n")
                        import traceback
                        traceback.print_exc()
                        continue
                
                # Send to FAME - use unified system
                print("\nFAME: ", end="", flush=True)
                
                try:
                    # Use unified FAME system
                    from fame_unified import get_fame
                    
                    fame = get_fame()
                    response = await fame.process_text_async(user_input, source='chat_ui')
                    
                    # Display response
                    fame_response = response.get('response', 'I didn\'t understand that.')
                    print(fame_response)
                    
                    # Show comprehensive metadata (always display)
                    metadata_parts = []
                    
                    # Confidence (always show as percentage)
                    if 'confidence' in response:
                        conf = response['confidence']
                        conf_pct = f"{conf*100:.1f}%"
                        metadata_parts.append(f"Confidence: {conf_pct}")
                    
                    # Sources/resources used
                    sources_display = []
                    if 'sources' in response:
                        sources_display.extend(response['sources'])
                    elif 'source' in response:
                        sources_display.append(response['source'])
                    
                    # Check routing for modules
                    routing = response.get('routing', {})
                    if 'selected_modules' in routing:
                        for mod in routing['selected_modules']:
                            if mod not in sources_display:
                                sources_display.append(mod)
                    
                    # Knowledge base attribution
                    if 'knowledge_base_match' in response:
                        kb_match = response['knowledge_base_match']
                        kb_source = f"KB: {kb_match.get('book', 'N/A')}"
                        sources_display.append(kb_source)
                    
                    if sources_display:
                        sources_str = ", ".join(sources_display[:5])
                        metadata_parts.append(f"Sources: {sources_str}")
                    
                    # Intent
                    if 'intent' in response:
                        metadata_parts.append(f"Intent: {response['intent']}")
                    
                    if metadata_parts:
                        print("\n[" + " | ".join(metadata_parts) + "]")
                    
                    print()
                except ImportError:
                    # Fallback to brain routing if unified not available
                    response = await self.brain.handle_query({
                        'text': user_input,
                        'source': 'chat_ui',
                        'use_assistant': False
                    })
                    
                    # Display response
                    fame_response = response.get('response', 'I didn\'t understand that.')
                    print(fame_response)
                    
                    # Show confidence if available
                    if 'confidence' in response:
                        print(f"\n[Confidence: {response['confidence']*100:.1f}%]")
                    
                    print()
                except Exception as e:
                    print(f"\n[Error: {e}]\n")
                    import traceback
                    traceback.print_exc()
                
                # Save to history
                self.conversation_history.append({
                    'user': user_input,
                    'fame': fame_response
                })
                
            except KeyboardInterrupt:
                print("\n\nFAME: Goodbye!")
                break
            except Exception as e:
                print(f"\n[Error: {e}]\n")


async def main():
    chat = FAME_Chat()
    await chat.chat_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")

