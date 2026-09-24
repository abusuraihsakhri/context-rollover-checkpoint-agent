"""
Checkpoint Restore Diff for Context Rollover Checkpoint Agent.
Computes diffs between current state and checkpoint before restore to prevent data loss.
"""
import copy
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum

_MISSING = object()


class FieldChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class FieldChange:
    """Represents a single field-level change."""
    field_path: str
    change_type: FieldChangeType
    current_value: Optional[Any] = None
    checkpoint_value: Optional[Any] = None


@dataclass
class RestoreDiff:
    """Complete diff between current state and checkpoint state."""
    checkpoint_id: str
    changes: List[FieldChange]
    fields_added: int = 0
    fields_removed: int = 0
    fields_modified: int = 0
    fields_unchanged: int = 0
    computed_at: float = field(default_factory=time.time)

    def has_changes(self) -> bool:
        return (self.fields_added + self.fields_removed + self.fields_modified) > 0

    def summary(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "total_changes": self.fields_added + self.fields_removed + self.fields_modified,
            "added": self.fields_added,
            "removed": self.fields_removed,
            "modified": self.fields_modified,
            "unchanged": self.fields_unchanged,
            "computed_at": self.computed_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "changes": [
                {
                    "field": c.field_path,
                    "type": c.change_type.value,
                    "current": c.current_value,
                    "checkpoint": c.checkpoint_value,
                }
                for c in self.changes
                if c.change_type != FieldChangeType.UNCHANGED
            ],
        }


class RestoreDiffEngine:
    """Computes and manages restore diffs for checkpoint comparison."""

    def __init__(self):
        self._diff_log: List[Dict[str, Any]] = []

    def compute_diff(self, current_state: Dict[str, Any],
                     checkpoint_state: Dict[str, Any],
                     checkpoint_id: str = "unknown") -> RestoreDiff:
        """Compute field-level diff between current state and checkpoint."""
        changes = []
        self._diff_recursive(current_state, checkpoint_state, changes, prefix="")
        diff = RestoreDiff(
            checkpoint_id=checkpoint_id,
            changes=changes,
        )
        for c in changes:
            if c.change_type == FieldChangeType.ADDED:
                diff.fields_added += 1
            elif c.change_type == FieldChangeType.REMOVED:
                diff.fields_removed += 1
            elif c.change_type == FieldChangeType.MODIFIED:
                diff.fields_modified += 1
            else:
                diff.fields_unchanged += 1

        self._diff_log.append(diff.summary())
        return diff

    def selective_restore(self, current_state: Dict[str, Any],
                          checkpoint_state: Dict[str, Any],
                          fields_to_restore: List[str]) -> Dict[str, Any]:
        """Restore only specific fields from checkpoint."""
        result = copy.deepcopy(current_state)
        for field_path in fields_to_restore:
            value = self._get_nested(checkpoint_state, field_path, default=_MISSING)
            if value is not _MISSING:
                self._set_nested(result, field_path, copy.deepcopy(value))
        return result

    def format_diff_display(self, diff: RestoreDiff) -> str:
        """Format a diff for human-readable display."""
        lines = [
            f"Restore Diff for Checkpoint: {diff.checkpoint_id}",
            "=" * 60,
            f"  Will ADD:     {diff.fields_added} fields",
            f"  Will REMOVE:  {diff.fields_removed} fields",
            f"  Will MODIFY:  {diff.fields_modified} fields",
            f"  Unchanged:    {diff.fields_unchanged} fields",
            "-" * 60,
        ]
        for change in diff.changes:
            if change.change_type == FieldChangeType.UNCHANGED:
                continue
            symbol = {"added": "+", "removed": "-", "modified": "~"}[change.change_type.value]
            lines.append(f"  [{symbol}] {change.field_path}")
            if change.current_value is not None:
                lines.append(f"      current:     {json.dumps(change.current_value, default=str)[:80]}")
            if change.checkpoint_value is not None:
                lines.append(f"      checkpoint:  {json.dumps(change.checkpoint_value, default=str)[:80]}")
        return "\n".join(lines)

    def get_diff_log(self) -> List[Dict[str, Any]]:
        return list(self._diff_log)

    def _diff_recursive(self, current: Any, checkpoint: Any,
                        changes: List[FieldChange], prefix: str) -> None:
        if isinstance(current, dict) and isinstance(checkpoint, dict):
            all_keys = set(current.keys()) | set(checkpoint.keys())
            for key in sorted(all_keys):
                path = f"{prefix}.{key}" if prefix else key
                if key in current and key in checkpoint:
                    self._diff_recursive(current[key], checkpoint[key], changes, path)
                elif key in current:
                    changes.append(FieldChange(path, FieldChangeType.REMOVED, current_value=current[key]))
                else:
                    changes.append(FieldChange(path, FieldChangeType.ADDED, checkpoint_value=checkpoint[key]))
        elif isinstance(current, list) and isinstance(checkpoint, list):
            max_len = max(len(current), len(checkpoint))
            for i in range(max_len):
                path = f"{prefix}[{i}]"
                if i < len(current) and i < len(checkpoint):
                    self._diff_recursive(current[i], checkpoint[i], changes, path)
                elif i < len(current):
                    changes.append(FieldChange(path, FieldChangeType.REMOVED, current_value=current[i]))
                else:
                    changes.append(FieldChange(path, FieldChangeType.ADDED, checkpoint_value=checkpoint[i]))
        else:
            if current == checkpoint:
                changes.append(FieldChange(prefix, FieldChangeType.UNCHANGED, current, checkpoint))
            else:
                changes.append(FieldChange(prefix, FieldChangeType.MODIFIED, current, checkpoint))

    def _get_nested(self, obj: Dict[str, Any], path: str, default: Any = None) -> Any:
        parts = path.replace("[", ".").replace("]", "").split(".")
        current: Any = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if idx < len(current):
                    current = current[idx]
                else:
                    return default
            else:
                return default
        return current

    def _set_nested(self, obj: Dict[str, Any], path: str, value: Any) -> None:
        parts = path.replace("[", ".").replace("]", "").split(".")
        current: Any = obj
        for index, part in enumerate(parts[:-1]):
            next_is_index = parts[index + 1].isdigit()
            if isinstance(current, dict):
                if part not in current or current[part] is None:
                    current[part] = [] if next_is_index else {}
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                position = int(part)
                while len(current) <= position:
                    current.append(None)
                if current[position] is None:
                    current[position] = [] if next_is_index else {}
                current = current[position]
            else:
                raise TypeError(f"Cannot traverse field path '{path}' through '{part}'")

        last = parts[-1]
        if isinstance(current, dict):
            current[last] = value
        elif isinstance(current, list) and last.isdigit():
            position = int(last)
            while len(current) <= position:
                current.append(None)
            current[position] = value
        else:
            raise TypeError(f"Cannot set field path '{path}'")
