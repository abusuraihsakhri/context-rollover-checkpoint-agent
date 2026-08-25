#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for Context Rollover Checkpoint & Delta Restoration Engine
Tests triggers (Token, Time, Error, Context Overflow, Turn Count, TriggerEvaluator),
Zlib state compressor, hierarchical field-level diff calculation, and full snapshot restoration workflows.
"""

import unittest
import time
import json
from context_rollover_checkpoint import (
    ContextRolloverEngine,
    FrontierDomainEngine,
    FrontierPayload,
    TokenCountTrigger,
    TimeElapsedTrigger,
    ErrorCountTrigger,
    ContextOverflowTrigger,
    TurnCountTrigger,
    TriggerEvaluator,
    create_evaluator_from_config,
    CheckpointCompressor,
    CompressionMetadata,
    FieldChangeType,
    RestoreDiffEngine,
)


class TestTriggerPolicies(unittest.TestCase):
    """Test suite for autonomous rollover trigger evaluations."""

    def test_token_count_trigger_below_threshold(self):
        trigger = TokenCountTrigger(threshold=5000)
        state = {"token_count": 4999}
        self.assertFalse(trigger.evaluate(state))

    def test_token_count_trigger_at_or_above_threshold(self):
        trigger = TokenCountTrigger(threshold=5000)
        state = {"token_count": 5000}
        self.assertTrue(trigger.evaluate(state))
        state2 = {"token_count": 7500}
        self.assertTrue(trigger.evaluate(state2))

    def test_token_count_trigger_missing_key(self):
        trigger = TokenCountTrigger(threshold=5000)
        self.assertFalse(trigger.evaluate({}))

    def test_time_elapsed_trigger(self):
        trigger = TimeElapsedTrigger(threshold_seconds=10.0)
        state_recent = {"last_rollover_time": time.time()}
        self.assertFalse(trigger.evaluate(state_recent))

        state_expired = {"last_rollover_time": time.time() - 15.0}
        self.assertTrue(trigger.evaluate(state_expired))

    def test_error_count_trigger(self):
        trigger = ErrorCountTrigger(threshold=3)
        self.assertFalse(trigger.evaluate({"error_count": 2}))
        self.assertTrue(trigger.evaluate({"error_count": 3}))
        self.assertTrue(trigger.evaluate({"error_count": 5}))

    def test_context_overflow_trigger(self):
        trigger = ContextOverflowTrigger(threshold_percent=80.0)
        self.assertFalse(trigger.evaluate({"context_usage_percent": 75.0}))
        self.assertTrue(trigger.evaluate({"context_usage_percent": 85.0}))

    def test_turn_count_trigger(self):
        trigger = TurnCountTrigger(threshold=15)
        self.assertFalse(trigger.evaluate({"turn_count": 10}))
        self.assertTrue(trigger.evaluate({"turn_count": 15}))

    def test_trigger_evaluator_first_match(self):
        t1 = TokenCountTrigger(threshold=1000)
        t2 = ErrorCountTrigger(threshold=5)
        evaluator = TriggerEvaluator([t1, t2])

        # Neither fired
        self.assertIsNone(evaluator.evaluate({"token_count": 500, "error_count": 2}))
        # First fired
        res = evaluator.evaluate({"token_count": 1500, "error_count": 2})
        self.assertIsNotNone(res)
        self.assertEqual(res.name(), "token_count")

    def test_trigger_evaluator_evaluate_all(self):
        t1 = TokenCountTrigger(threshold=1000)
        t2 = ErrorCountTrigger(threshold=5)
        evaluator = TriggerEvaluator([t1, t2])

        fired = evaluator.evaluate_all({"token_count": 1500, "error_count": 10})
        self.assertEqual(len(fired), 2)

    def test_create_evaluator_from_config(self):
        configs = [
            {"type": "token_count", "threshold": 2000},
            {"type": "error_count", "threshold": 4},
        ]
        evaluator = create_evaluator_from_config(configs)
        self.assertEqual(len(evaluator.triggers), 2)


class TestCheckpointCompressor(unittest.TestCase):
    """Test suite for zlib-based state snapshot compression."""

    def test_uncompressed_small_payload(self):
        compressor = CheckpointCompressor(compress_threshold=1024)
        small_state = {"agent_id": "A1", "status": "ACTIVE"}
        raw_bytes, meta = compressor.compress(small_state)
        self.assertEqual(meta.algorithm, "none")
        self.assertEqual(meta.compression_ratio, 1.0)

        decomp = compressor.decompress(raw_bytes, is_compressed=False)
        self.assertEqual(decomp["agent_id"], "A1")

    def test_compressed_large_payload(self):
        compressor = CheckpointCompressor(compress_threshold=100, compression_level=6)
        large_state = {
            "conversation_history": [
                {"role": "user", "content": "Explain quantum side-channel attacks in detail." * 20},
                {"role": "assistant", "content": "Side-channel analysis exploits physical leakage." * 20},
            ]
        }
        raw_bytes, meta = compressor.compress(large_state)
        self.assertEqual(meta.algorithm, "zlib")
        self.assertLess(meta.compression_ratio, 1.0)
        self.assertLess(meta.compressed_size, meta.original_size)

        decomp = compressor.decompress(raw_bytes, is_compressed=True)
        self.assertEqual(len(decomp["conversation_history"]), 2)

    def test_compress_log_recording(self):
        compressor = CheckpointCompressor(compress_threshold=50)
        payload = {"data": "x" * 200}
        _, meta = compressor.compress(payload)
        log = compressor.get_compression_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["algorithm"], "zlib")


class TestRestoreDiffEngine(unittest.TestCase):
    """Test suite for hierarchical delta diffing between states."""

    def setUp(self):
        self.diff_engine = RestoreDiffEngine()

    def test_identical_states_no_diff(self):
        state = {"a": 1, "b": "hello", "nested": {"x": 10}}
        diff = self.diff_engine.compute_diff(current_state=state, checkpoint_state=state, checkpoint_id="CP-01")
        self.assertFalse(diff.has_changes())
        self.assertEqual(diff.fields_modified, 0)
        self.assertEqual(diff.fields_added, 0)
        self.assertEqual(diff.fields_removed, 0)

    def test_modified_fields(self):
        curr = {"step": 10, "status": "running"}
        ckpt = {"step": 5, "status": "paused"}
        diff = self.diff_engine.compute_diff(current_state=curr, checkpoint_state=ckpt, checkpoint_id="CP-02")
        self.assertTrue(diff.has_changes())
        self.assertEqual(diff.fields_modified, 2)

    def test_added_and_removed_fields(self):
        curr = {"task_id": "T1", "new_field": "transient"}
        ckpt = {"task_id": "T1", "old_field": "persisted"}
        diff = self.diff_engine.compute_diff(current_state=curr, checkpoint_state=ckpt, checkpoint_id="CP-03")
        self.assertTrue(diff.has_changes())
        self.assertGreater(diff.fields_added + diff.fields_removed, 0)

    def test_nested_dictionary_diff(self):
        curr = {"config": {"retries": 5, "timeout": 30}}
        ckpt = {"config": {"retries": 3, "timeout": 30}}
        diff = self.diff_engine.compute_diff(current_state=curr, checkpoint_state=ckpt, checkpoint_id="CP-04")
        self.assertTrue(diff.has_changes())
        self.assertEqual(diff.fields_modified, 1)
        self.assertEqual(diff.changes[0].field_path, "config.retries")

    def test_selective_restore(self):
        curr = {"status": "ACTIVE", "counter": 100, "temp_data": "temp"}
        ckpt = {"status": "PAUSED", "counter": 50, "temp_data": "old_temp"}
        restored = self.diff_engine.selective_restore(curr, ckpt, ["status"])
        self.assertEqual(restored["status"], "PAUSED")
        self.assertEqual(restored["counter"], 100)


class TestContextRolloverEngineWorkflows(unittest.TestCase):
    """Test suite for integrated ContextRolloverEngine workflows."""

    def test_engine_initialization_and_trigger(self):
        engine = ContextRolloverEngine(token_threshold=3000)
        self.assertFalse(engine.should_rollover({"token_count": 1000, "error_count": 0}))
        self.assertTrue(engine.should_rollover({"token_count": 3500, "error_count": 0}))

    def test_create_and_restore_checkpoint(self):
        engine = ContextRolloverEngine(token_threshold=3000, compress_threshold=100)
        state_v1 = {"agent_id": "AG-01", "task_queue": ["task1", "task2"], "tokens": 1200}
        raw_bytes, meta = engine.create_checkpoint("CKPT-001", state_v1)
        self.assertIn("CKPT-001", engine.checkpoints)

        current_state_v2 = {"agent_id": "AG-01", "task_queue": ["task3"], "tokens": 4500}
        restored, diff = engine.restore_checkpoint("CKPT-001", current_state_v2)
        self.assertEqual(restored["tokens"], 1200)
        self.assertTrue(diff.has_changes())

    def test_restore_missing_checkpoint_raises_keyerror(self):
        engine = ContextRolloverEngine()
        with self.assertRaises(KeyError):
            engine.restore_checkpoint("NON_EXISTENT", {})


class TestFrontierDomainEngineRules(unittest.TestCase):
    """Test suite for domain threshold boundary validations."""

    def test_evaluate_primary_parameter_nominal(self):
        res = FrontierDomainEngine.evaluate_primary_parameter(15.0)
        self.assertIsNone(res)

    def test_evaluate_primary_parameter_breach(self):
        res = FrontierDomainEngine.evaluate_primary_parameter(30.0)
        self.assertIsNotNone(res)
        self.assertEqual(res["summary"], "Primary Domain Boundary Deviation")

    def test_evaluate_secondary_kinetics_critical(self):
        res = FrontierDomainEngine.evaluate_secondary_kinetics(5.0, is_critical=True)
        self.assertIsNotNone(res)
        self.assertIn("Critical Domain Condition", res["summary"])

    def test_audit_specification_conformance_violation(self):
        res = FrontierDomainEngine.audit_specification_conformance("DISCORDANT_ANOMALY", {})
        self.assertIsNotNone(res)
        self.assertIn("Specification / Protocol Anomaly", res["summary"])


if __name__ == "__main__":
    unittest.main()
