"""
Checkpoint Compression for Context Rollover Checkpoint Agent.
Compresses checkpoint snapshots using zlib to minimize storage overhead.
"""
import zlib
import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, Union

PathLike = Union[str, os.PathLike]


@dataclass
class CompressionMetadata:
    """Metadata about a compressed checkpoint."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm: str = "zlib"
    compressed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "compression_ratio": self.compression_ratio,
            "algorithm": self.algorithm,
            "compressed_at": self.compressed_at,
        }


class CheckpointCompressor:
    """Handles compression and decompression of checkpoint data."""

    DEFAULT_COMPRESS_THRESHOLD = 10 * 1024  # 10KB

    def __init__(
        self,
        compress_threshold: int = DEFAULT_COMPRESS_THRESHOLD,
        compression_level: int = 6,
        base_dir: Optional[PathLike] = None,
    ):
        if compress_threshold < 0:
            raise ValueError("compress_threshold must be >= 0")
        if not 0 <= compression_level <= 9:
            raise ValueError("compression_level must be between 0 and 9")
        self.compress_threshold = compress_threshold
        self.compression_level = compression_level
        self.base_dir = Path(base_dir or Path.cwd()).expanduser().resolve()
        self._compression_log: list = []

    def should_compress(self, data: bytes) -> bool:
        """Check if data exceeds compression threshold."""
        return len(data) >= self.compress_threshold

    def compress(self, checkpoint_data: Dict[str, Any]) -> Tuple[bytes, CompressionMetadata]:
        """Compress checkpoint data. Returns (compressed_bytes, metadata)."""
        json_bytes = json.dumps(checkpoint_data, default=str).encode("utf-8")
        original_size = len(json_bytes)

        if not self.should_compress(json_bytes):
            metadata = CompressionMetadata(
                original_size=original_size,
                compressed_size=original_size,
                compression_ratio=1.0,
                algorithm="none",
            )
            return json_bytes, metadata

        compressed = zlib.compress(json_bytes, level=self.compression_level)
        compressed_size = len(compressed)
        ratio = compressed_size / original_size if original_size > 0 else 1.0

        metadata = CompressionMetadata(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=ratio,
        )
        self._compression_log.append(metadata.to_dict())
        return compressed, metadata

    def decompress(self, compressed_data: bytes, is_compressed: bool = True) -> Dict[str, Any]:
        """Decompress checkpoint data back to dict."""
        if not is_compressed:
            return json.loads(compressed_data.decode("utf-8"))
        decompressed = zlib.decompress(compressed_data)
        return json.loads(decompressed.decode("utf-8"))

    def save_checkpoint(self, checkpoint_data: Dict[str, Any], filepath: PathLike) -> CompressionMetadata:
        """Save a checkpoint below the configured base directory."""
        resolved = self._resolve_path(filepath)
        compressed, metadata = self.compress(checkpoint_data)
        ext = ".gz" if metadata.algorithm == "zlib" else ".json"
        actual_path = resolved if str(resolved).endswith(ext) else Path(f"{resolved}{ext}")
        self._assert_within_base(actual_path)

        actual_path.parent.mkdir(parents=True, exist_ok=True)
        actual_path.write_bytes(compressed)

        meta_path = Path(f"{actual_path}.meta")
        self._assert_within_base(meta_path)
        meta_path.write_text(json.dumps(metadata.to_dict(), indent=2), encoding="utf-8")
        return metadata

    def load_checkpoint(self, filepath: PathLike) -> Dict[str, Any]:
        """Load a checkpoint below the configured base directory."""
        resolved = self._resolve_path(filepath)
        if not resolved.is_file():
            raise FileNotFoundError(f"Checkpoint file not found: '{filepath}'")
        return self.decompress(resolved.read_bytes(), resolved.suffix == ".gz")

    def _resolve_path(self, filepath: PathLike) -> Path:
        raw = Path(filepath).expanduser()
        if any(part == ".." for part in raw.parts):
            raise ValueError(f"Invalid filepath: path traversal detected in '{filepath}'")
        candidate = raw if raw.is_absolute() else self.base_dir / raw
        resolved = candidate.resolve(strict=False)
        self._assert_within_base(resolved, original=filepath)
        return resolved

    def _assert_within_base(self, path: Path, original: Optional[PathLike] = None) -> None:
        try:
            path.resolve(strict=False).relative_to(self.base_dir)
        except ValueError as exc:
            shown = original if original is not None else path
            raise ValueError(
                f"Invalid filepath: path traversal or root escape detected for '{shown}' (allowed root: '{self.base_dir}')"
            ) from exc

    def get_compression_log(self) -> list:
        return list(self._compression_log)

    def get_stats(self) -> Dict[str, Any]:
        if not self._compression_log:
            return {"total_compressions": 0}
        total_original = sum(e["original_size"] for e in self._compression_log)
        total_compressed = sum(e["compressed_size"] for e in self._compression_log)
        return {
            "total_compressions": len(self._compression_log),
            "total_original_bytes": total_original,
            "total_compressed_bytes": total_compressed,
            "overall_ratio": total_compressed / total_original if total_original > 0 else 1.0,
            "space_saved_bytes": total_original - total_compressed,
        }
