#!/usr/bin/env python3
"""
FAME Advanced Trading Handlers - Base Class
Base class for all advanced trading handlers
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseTradingHandler(ABC):
    """
    Base class for advanced trading question handlers
    
    Handlers can:
    1. Check if real-time data is available
    2. Generate real-time responses when data is available
    3. Fall back to static responses when data is not available
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """
        Check if this handler can handle the question
        
        Args:
            text: Question text
            
        Returns:
            True if handler can handle, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_static(self, text: str) -> Dict[str, Any]:
        """
        Generate static response (no real-time data)
        
        Args:
            text: Question text
            
        Returns:
            Response dict with:
            - response: str (answer text)
            - source: str (data source)
            - type: str (question type)
            - confidence: float (0-1)
        """
        pass
    
    def has_realtime_data(self, text: str) -> bool:
        """
        Check if real-time data is available for this question
        
        Override in subclasses to check actual data availability
        
        Args:
            text: Question text
            
        Returns:
            True if real-time data available, False otherwise
        """
        return False
    
    def handle_realtime(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Generate real-time response (with live data)
        
        Override in subclasses to use actual real-time data
        
        Args:
            text: Question text
            
        Returns:
            Response dict with real-time data, or None if not available
        """
        return None
    
    def handle(self, text: str) -> Dict[str, Any]:
        """
        Main handler method - tries real-time first, falls back to static
        
        Args:
            text: Question text
            
        Returns:
            Response dict
        """
        # Check if we can handle this question
        if not self.can_handle(text):
            return {
                "response": "This handler cannot process this question.",
                "source": self.name,
                "type": "error",
                "confidence": 0.0
            }
        
        # Try real-time first if available
        if self.has_realtime_data(text):
            try:
                realtime_response = self.handle_realtime(text)
                if realtime_response:
                    self.logger.debug(f"Generated real-time response for: {text[:50]}...")
                    return realtime_response
            except Exception as e:
                self.logger.warning(f"Error generating real-time response: {e}, falling back to static")
        
        # Fall back to static response
        static_response = self.handle_static(text)
        self.logger.debug(f"Generated static response for: {text[:50]}...")
        return static_response
    
    def build_response(self, response_text: str, source: str, response_type: str,
                      confidence: float, realtime: bool = False,
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build standardized response dict
        
        Args:
            response_text: Answer text
            source: Data source name
            response_type: Question/response type
            confidence: Confidence score (0-1)
            realtime: Whether this is real-time data
            data: Additional data dict
            
        Returns:
            Standardized response dict
        """
        response = {
            "response": response_text,
            "source": f"{source}{' (real-time)' if realtime else ''}",
            "type": response_type,
            "confidence": confidence,
            "realtime": realtime
        }
        
        if data:
            response["data"] = data
        
        return response

