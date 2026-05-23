"""
services/orchestrator/engines/base.py - Abstract Orchestrator Execution Engine
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from shared.types import ExecutionContext

class ExecutionEngine(ABC):
    """Abstract Base Class representing an orchestration execution model"""
    
    @abstractmethod
    async def execute(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Executes the query using the specific engine architecture
        
        Args:
            message: User natural language input
            history: Thread conversation history
            context: Session bounds context containing auth keys
            
        Returns:
            A dictionary containing 'response', 'trace' and other engine specific payloads
        """
        pass
