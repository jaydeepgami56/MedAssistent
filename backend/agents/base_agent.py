"""
BaseAgent - Abstract base class for all MedAssist AI specialist agents.

This module provides the foundational interface that all specialist agents
(Triage, Radiology, Diagnostic, Pharmacy, Monitoring, Documentation, Research)
inherit from, ensuring consistent behavior across the agent ecosystem.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for all MedAssist AI specialist agents.

    All specialist agents inherit from this class and must implement the
    abstract methods execute_skill() and chat(). This ensures a consistent
    interface for agent execution, skill invocation, and audit logging.

    Attributes:
        agent_id: Unique identifier for the agent (e.g., "triage", "radiology")
        name: Human-readable agent name (e.g., "Triage Agent")
        status: Current agent status (default: "Active")
        skills: List of skill names this agent can execute
        queue: Number of pending requests in agent queue (default: 0)
        models_used: List of AI models used by this agent
        color: Hex color code for UI accent color (e.g., "#ef4444")
        icon: Text/emoji icon for UI display
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        skills: list[str],
        models_used: list[str],
        color: str,
        icon: str,
        status: str = "Active",
        queue: int = 0
    ):
        """
        Initialize the base agent with required properties.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable agent name
            skills: List of skill names this agent can execute
            models_used: List of AI models used by this agent
            color: Hex color code for UI accent color
            icon: Text/emoji icon for UI display
            status: Current agent status (default: "Active")
            queue: Number of pending requests (default: 0)
        """
        self.agent_id = agent_id
        self.name = name
        self.status = status
        self.skills = skills
        self.queue = queue
        self.models_used = models_used
        self.color = color
        self.icon = icon

    @abstractmethod
    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute a specific skill with given parameters.

        This method must be implemented by all specialist agents to handle
        skill execution logic. Each agent implements domain-specific processing
        based on its SKILL.md definition.

        Args:
            skill_name: Name of the skill to execute (must be in self.skills)
            params: Dictionary of parameters required for skill execution

        Returns:
            dict: Execution result containing output data, confidence, etc.

        Raises:
            ValueError: If skill_name is not in self.skills
            NotImplementedError: If subclass does not implement this method
        """
        pass

    @abstractmethod
    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses to user messages.

        This method must be implemented by all specialist agents to handle
        interactive chat conversations. Returns an async iterator for streaming
        responses token-by-token.

        Args:
            message: User message to respond to
            context: Dictionary of conversation context (history, patient data, etc.)

        Yields:
            str: Response tokens streamed one at a time

        Raises:
            NotImplementedError: If subclass does not implement this method
        """
        pass

    def get_info(self) -> dict:
        """
        Get agent metadata as a dictionary.

        Returns all agent properties (agent_id, name, status, skills, queue,
        models_used, color, icon) as a dictionary for API responses and UI display.

        Returns:
            dict: Agent metadata with all properties
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "skills": self.skills,
            "queue": self.queue,
            "models_used": self.models_used,
            "color": self.color,
            "icon": self.icon
        }

    def log_audit(
        self,
        request: str,
        model: str,
        confidence: float,
        action: str
    ) -> None:
        """
        Log audit entry for compliance and debugging.

        Logs agent actions to console (placeholder for database logging).
        All agent executions should be audited for HIPAA compliance,
        debugging, and quality monitoring.

        Args:
            request: User request or skill invocation
            model: AI model used for processing
            confidence: Confidence score (0.0 to 1.0)
            action: Action taken (e.g., "approved", "flagged", "escalated")

        Note:
            This is a placeholder implementation that prints to console.
            Future versions will write to PostgreSQL audit_log table.
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = (
            f"[AUDIT] {timestamp} | "
            f"Agent: {self.agent_id} | "
            f"Request: {request[:50]}{'...' if len(request) > 50 else ''} | "
            f"Model: {model} | "
            f"Confidence: {confidence:.3f} | "
            f"Action: {action}"
        )
        print(log_entry)
