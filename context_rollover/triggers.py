"""
Rollover Trigger Policies for Context Rollover Checkpoint Agent.
Defines configurable trigger policies that determine when rollover should occur.
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class TriggerPolicy(ABC):
    """Base interface for rollover trigger policies."""

    @abstractmethod
    def evaluate(self, state: Dict[str, Any]) -> bool:
        """Return True if the trigger condition is met."""
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def describe(self) -> Dict[str, Any]:
        pass


@dataclass
class TokenCountTrigger(TriggerPolicy):
    """Trigger when token count exceeds threshold."""
    threshold: int = 4000

    def evaluate(self, state: Dict[str, Any]) -> bool:
        return state.get("token_count", 0) >= self.threshold

    def name(self) -> str:
        return "token_count"

    def describe(self) -> Dict[str, Any]:
        return {"type": "token_count", "threshold": self.threshold}


@dataclass
class TimeElapsedTrigger(TriggerPolicy):
    """Trigger when time since last rollover exceeds threshold."""
    threshold_seconds: float = 300.0

    def evaluate(self, state: Dict[str, Any]) -> bool:
        last_rollover = state.get("last_rollover_time", 0)
        return (time.time() - last_rollover) >= self.threshold_seconds

    def name(self) -> str:
        return "time_elapsed"

    def describe(self) -> Dict[str, Any]:
        return {"type": "time_elapsed", "threshold_seconds": self.threshold_seconds}


@dataclass
class ErrorCountTrigger(TriggerPolicy):
    """Trigger when error count exceeds threshold."""
    threshold: int = 3

    def evaluate(self, state: Dict[str, Any]) -> bool:
        return state.get("error_count", 0) >= self.threshold

    def name(self) -> str:
        return "error_count"

    def describe(self) -> Dict[str, Any]:
        return {"type": "error_count", "threshold": self.threshold}


@dataclass
class ContextOverflowTrigger(TriggerPolicy):
    """Trigger when context window usage exceeds percentage."""
    threshold_percent: float = 85.0

    def evaluate(self, state: Dict[str, Any]) -> bool:
        usage = state.get("context_usage_percent", 0)
        return usage >= self.threshold_percent

    def name(self) -> str:
        return "context_overflow"

    def describe(self) -> Dict[str, Any]:
        return {"type": "context_overflow", "threshold_percent": self.threshold_percent}


@dataclass
class TurnCountTrigger(TriggerPolicy):
    """Trigger after a fixed number of conversation turns."""
    threshold: int = 20

    def evaluate(self, state: Dict[str, Any]) -> bool:
        return state.get("turn_count", 0) >= self.threshold

    def name(self) -> str:
        return "turn_count"

    def describe(self) -> Dict[str, Any]:
        return {"type": "turn_count", "threshold": self.threshold}


# Registry
TRIGGER_REGISTRY: Dict[str, type] = {
    "token_count": TokenCountTrigger,
    "time_elapsed": TimeElapsedTrigger,
    "error_count": ErrorCountTrigger,
    "context_overflow": ContextOverflowTrigger,
    "turn_count": TurnCountTrigger,
}


class TriggerEvaluator:
    """Evaluates multiple trigger policies and reports which fired."""

    def __init__(self, triggers: Optional[List[TriggerPolicy]] = None):
        self.triggers: List[TriggerPolicy] = triggers or []
        self._fire_log: List[Dict[str, Any]] = []

    def add_trigger(self, trigger: TriggerPolicy) -> None:
        self.triggers.append(trigger)

    def evaluate(self, state: Dict[str, Any]) -> Optional[TriggerPolicy]:
        """Evaluate all triggers; return the first one that fires, or None."""
        for trigger in self.triggers:
            if trigger.evaluate(state):
                self._fire_log.append({
                    "trigger": trigger.name(),
                    "config": trigger.describe(),
                    "state_snapshot": {k: v for k, v in state.items() if k != "full_context"},
                    "fired_at": time.time(),
                })
                return trigger
        return None

    def evaluate_all(self, state: Dict[str, Any]) -> List[TriggerPolicy]:
        """Evaluate all triggers; return all that fire."""
        fired = [t for t in self.triggers if t.evaluate(state)]
        for t in fired:
            self._fire_log.append({
                "trigger": t.name(),
                "config": t.describe(),
                "fired_at": time.time(),
            })
        return fired

    def get_fire_log(self) -> List[Dict[str, Any]]:
        return list(self._fire_log)

    def get_trigger_summary(self) -> List[Dict[str, Any]]:
        return [t.describe() for t in self.triggers]


def create_evaluator_from_config(trigger_configs: List[Dict[str, Any]]) -> TriggerEvaluator:
    """Create a TriggerEvaluator from a list of config dicts."""
    evaluator = TriggerEvaluator()
    for cfg in trigger_configs:
        trigger_type = cfg.get("type")
        if trigger_type not in TRIGGER_REGISTRY:
            raise ValueError(f"Unknown trigger type: {trigger_type}")
        params = {k: v for k, v in cfg.items() if k != "type"}
        evaluator.add_trigger(TRIGGER_REGISTRY[trigger_type](**params))
    return evaluator
