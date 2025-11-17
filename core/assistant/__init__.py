#!/usr/bin/env python3
"""
F.A.M.E. Assistant Module
Siri/Alexa-style voice assistant capabilities
"""

from .assistant_api import handle_text_input, handle_voice_input

__all__ = ['handle_text_input', 'handle_voice_input']

