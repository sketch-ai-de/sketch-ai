"""Base types for ReAct agent."""

from abc import abstractmethod
from typing import Dict

from llama_index.bridge.pydantic import BaseModel


class BaseReasoningStep(BaseModel):
    """Reasoning step."""

    @abstractmethod
    def get_content(self) -> str:
        """Get content."""

    @property
    @abstractmethod
    def is_done(self) -> bool:
        """Is the reasoning step the last one."""


class ActionReasoningStep(BaseReasoningStep):
    """Action Reasoning step."""

    thought: str
    action: str
    action_input: Dict

    def get_content(self) -> str:
        """Get content."""
        return (
            f"Thought: {self.thought}\nAction: {self.action}\n"
            f"Action Input: {self.action_input}"
        )

    @property
    def is_done(self) -> bool:
        """Is the reasoning step the last one."""
        return False


class ActionReasoningStepArr(BaseReasoningStep):
    """Action Reasoning step."""

    thoughts: list
    actions: list
    action_inputs: list

    def get_content(self) -> str:
        """Get content."""
        return (
            f"Thoughts: {self.thoughts}\nActions: {self.actions}\n"
            f"Action Inputs: {self.action_inputs}"
        )

    @property
    def is_done(self) -> bool:
        """Is the reasoning step the last one."""
        return False


class ObservationReasoningStep(BaseReasoningStep):
    """Observation reasoning step."""

    observation: str

    def get_content(self) -> str:
        """Get content."""
        return f"Observation: {self.observation}"

    @property
    def is_done(self) -> bool:
        """Is the reasoning step the last one."""
        return False


class ResponseReasoningStep(BaseReasoningStep):
    """Response reasoning step."""

    thought: str
    response: str
    is_streaming: bool = False

    def get_content(self) -> str:
        """Get content."""
        if self.is_streaming:
            return (
                f"Thought: {self.thought}\nResponse (Starts With): {self.response} ..."
            )
        else:
            return f"Thought: {self.thought}\nResponse: {self.response}"

    @property
    def is_done(self) -> bool:
        """Is the reasoning step the last one."""
        return True
