"""
Base Agent class defining the interface for all agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    """Abstract base class for all agents."""
    
    name: str = "agent"
    
    @abstractmethod
    def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query and return a response.
        
        Args:
            query: User message
            context: Dict with user_token, session_id, etc.
            
        Returns:
            Dict with keys: reply, safe, score (optional), trace (optional)
        """
        pass
