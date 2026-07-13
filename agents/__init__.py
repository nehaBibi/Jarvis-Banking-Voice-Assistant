"""
Agent Manager - registry and switching logic for pluggable agents.
"""
from typing import Dict, Type, Optional
from .base import Agent
from .bfs import BFSAgent
from .astar import AStarAgent
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages agent registration, loading, and switching."""
    
    def __init__(self):
        self.agents: Dict[str, Type[Agent]] = {}
        self.default_agent = "bfs"
        self._instances: Dict[str, Agent] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register built-in agents."""
        self.register("bfs", BFSAgent)
        self.register("astar", AStarAgent)
        logger.info("Registered default agents: bfs, astar")
    
    def register(self, name: str, agent_class: Type[Agent]):
        """Register an agent class."""
        self.agents[name] = agent_class
        logger.debug(f"Registered agent: {name}")
    
    def get_agent(self, name: Optional[str] = None) -> Agent:
        """Get or create an agent instance."""
        agent_name = name or self.default_agent
        
        if agent_name not in self.agents:
            logger.warning(f"Agent '{agent_name}' not found, using default '{self.default_agent}'")
            agent_name = self.default_agent
        
        # Lazy instantiate agents (singletons per name)
        if agent_name not in self._instances:
            self._instances[agent_name] = self.agents[agent_name]()
        
        return self._instances[agent_name]
    
    def set_default(self, name: str):
        """Set the default agent."""
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not registered")
        self.default_agent = name
        logger.info(f"Default agent set to: {name}")
    
    def list_agents(self) -> list:
        """Return list of available agent names."""
        return list(self.agents.keys())
    
    def switch_agent(self, agent_name: str):
        """Set default agent (alias for set_default)."""
        self.set_default(agent_name)
