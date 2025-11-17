# orchestrator/voice_adapter.py

import asyncio


def init(manager):
    """
    If fame_voice_engine exists, bind to voice events.
    
    fame_voice_engine should implement:
      - transcribe(audio_bytes) -> text
      - speak(text) -> audio bytes or stream
    """
    mgr = manager
    
    if 'fame_voice_engine' in mgr.plugins:
        fame = mgr.plugins['fame_voice_engine']
        
        # If fame voice emits a transcript event we can subscribe
        if hasattr(fame, 'on_transcript'):
            def handle_transcript(transcript):
                # Schedule query handling
                asyncio.ensure_future(
                    mgr.handle_query({
                        'text': transcript,
                        'source': 'voice'
                    })
                )
            
            fame.on_transcript(handle_transcript)
        
        # Also subscribe to voice events via event bus
        async def on_voice_input(event_data):
            transcript = event_data.get('transcript', '')
            if transcript:
                await mgr.handle_query({
                    'text': transcript,
                    'source': 'voice',
                    'audio': event_data.get('audio')
                })
        
        mgr.bus.subscribe('voice.input', on_voice_input)
    
    # Set up voice output handler
    async def on_query_response(event_data):
        response_text = event_data.get('response', '')
        if response_text and 'fame_voice_engine' in mgr.plugins:
            fame = mgr.plugins['fame_voice_engine']
            if hasattr(fame, 'speak'):
                try:
                    if asyncio.iscoroutinefunction(fame.speak):
                        await fame.speak(response_text)
                    else:
                        await asyncio.to_thread(fame.speak, response_text)
                except Exception as e:
                    mgr.audit_log.append({
                        "event": "voice.speak_error",
                        "error": str(e)
                    })
    
    mgr.bus.subscribe('query.completed', on_query_response)

