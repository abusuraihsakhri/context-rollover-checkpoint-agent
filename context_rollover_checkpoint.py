#!/usr/bin/env python3
"""
Context Rollover Checkpoint & Delta Restoration Engine
------------------------------------------------------
Long-horizon agent state checkpointer, trigger policy evaluator, differential state
comparator, and zlib state compressor for autonomous multi-agent pipelines.

Domain: Autonomous Context Management & State Engines
Standard: Deterministic Agent State Machine v1.0
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import copy
import json
import time
import zlib
from context_rollover.models import FrontierPayload, AgentTelemetryAlert, ExecutionStatus
from context_rollover.engine import FrontierDomainEngine
from context_rollover.triggers import (
    TriggerPolicy,
    TokenCountTrigger,
    TimeElapsedTrigger,
    ErrorCountTrigger,
    ContextOverflowTrigger,
    TurnCountTrigger,
    TriggerEvaluator,
    create_evaluator_from_config,
)
from context_rollover.compression import CheckpointCompressor, CompressionMetadata
from context_rollover.restore_diff import (
    FieldChangeType,
    FieldChange,
    RestoreDiff,
    RestoreDiffEngine,
)


class ContextRolloverEngine:
    """Unified checkpoint management, trigger evaluation, and state recovery engine."""

    def __init__(
        self,
        token_threshold: int = 4000,
        compress_threshold: int = 1024,
        compression_level: int = 6,
    ):
        self.evaluator = TriggerEvaluator([
            TokenCountTrigger(threshold=token_threshold),
            ErrorCountTrigger(threshold=5),
        ])
        self.compressor = CheckpointCompressor(
            compress_threshold=compress_threshold,
            compression_level=compression_level,
        )
        self.diff_engine = RestoreDiffEngine()
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self.checkpoint_history: List[str] = []

    def should_rollover(self, state: Dict[str, Any]) -> bool:
        """Evaluate whether the given state triggers context rollover."""
        return self.evaluator.evaluate(state) is not None

    def create_checkpoint(
        self,
        checkpoint_id: str,
        state_data: Dict[str, Any],
    ) -> Tuple[bytes, CompressionMetadata]:
        """Snapshot current state, compress, and store."""
        snapshot = copy.deepcopy(state_data)
        compressed_bytes, metadata = self.compressor.compress(snapshot)
        self.checkpoints[checkpoint_id] = {
            "id": checkpoint_id,
            "data": snapshot,
            "raw_bytes": compressed_bytes,
            "metadata": metadata.to_dict(),
            "created_at": time.time(),
        }
        self.checkpoint_history.append(checkpoint_id)
        return compressed_bytes, metadata

    def restore_checkpoint(
        self,
        checkpoint_id: str,
        current_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], RestoreDiff]:
        """Compute delta diff between current state and target checkpoint, then restore."""
        if checkpoint_id not in self.checkpoints:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found.")

        target_state = copy.deepcopy(self.checkpoints[checkpoint_id]["data"])
        diff = self.diff_engine.compute_diff(
            current_state=current_state,
            checkpoint_state=target_state,
            checkpoint_id=checkpoint_id,
        )
        return target_state, diff


__all__ = [
    "ContextRolloverEngine",
    "FrontierDomainEngine",
    "FrontierPayload",
    "AgentTelemetryAlert",
    "ExecutionStatus",
    "TriggerPolicy",
    "TokenCountTrigger",
    "TimeElapsedTrigger",
    "ErrorCountTrigger",
    "ContextOverflowTrigger",
    "TurnCountTrigger",
    "TriggerEvaluator",
    "create_evaluator_from_config",
    "CheckpointCompressor",
    "CompressionMetadata",
    "FieldChangeType",
    "FieldChange",
    "RestoreDiff",
    "RestoreDiffEngine",
]
