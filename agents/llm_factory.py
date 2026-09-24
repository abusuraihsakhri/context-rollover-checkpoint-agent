"""Deterministic local mock interface used by the supervisor compatibility layer."""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Context Rollover Checkpoint Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: no external model call was made. Query received: '{prompt[:120]}'"


class LLMFactory:
    """Creates configured LLM client instances with zero-PHI protection."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Context Rollover Checkpoint Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(
            f"Provider '{provider}' is not implemented. "
            "Use 'mock' for the deterministic local compatibility interface."
        )
