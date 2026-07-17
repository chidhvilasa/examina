"""LocalBridgeClient — development-mode bridge to a local PRISM subprocess.

Calls PRISM via `python -m prism.bridge.cli`, a subprocess that reads
file bytes on stdin and writes the bridge JSON payload to stdout (see
PRISM's `prism/bridge/cli.py` and specs/BRIDGE_SPEC_v1.1.md). This is
EXAMINA's only interaction with PRISM: no PRISM Python module is ever
imported directly (Constitution Principle 10 — the bridge is one-way).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from examina.bridge.client import BridgeClient
from examina.bridge.types import BridgeError, BridgeRequest, BridgeResult
from examina.bridge.validator import parse_bridge_payload, validate_bridge_payload

logger = logging.getLogger(__name__)


class LocalBridgeClient(BridgeClient):
    """Runs PRISM's bridge CLI as a subprocess and parses its stdout."""

    def __init__(
        self,
        prism_path: Path | None = None,
        timeout_seconds: int = 60,
        python_executable: str | None = None,
    ) -> None:
        self.prism_path = prism_path or Path(os.environ.get("PRISM_PATH", "../PRISM"))
        self.timeout_seconds = timeout_seconds
        self.python_executable = python_executable or os.environ.get("PRISM_PYTHON", "python")

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.prism_path)
        return env

    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        """Send a file to PRISM for analysis and return structured results.

        Raises BridgeError on any failure. Never raises any other
        exception type — every underlying transport exception is caught
        here and re-raised as BridgeError with the matching code.
        """
        env = self._build_env()
        env["PRISM_FILE_HASH"] = request.file_hash
        env["PRISM_FILE_TYPE"] = request.file_type

        cmd = [self.python_executable, "-m", "prism.bridge.cli"]

        try:
            result = subprocess.run(
                cmd,
                input=request.file_bytes,
                capture_output=True,
                timeout=self.timeout_seconds,
                env=env,
                cwd=str(self.prism_path),
            )
        except subprocess.TimeoutExpired as exc:
            raise BridgeError(
                code="ANALYSIS_TIMEOUT",
                message="Analysis exceeded time limit",
                request_id=request.request_id,
            ) from exc
        except FileNotFoundError as exc:
            raise BridgeError(
                code="BRIDGE_UNAVAILABLE",
                message="PRISM is not available at the configured path",
                request_id=request.request_id,
            ) from exc
        except Exception as exc:
            logger.error(
                "Unexpected error invoking PRISM subprocess: %s: %s", type(exc).__name__, exc
            )
            raise BridgeError(
                code="BRIDGE_UNAVAILABLE", message=str(exc), request_id=request.request_id
            ) from exc

        if result.returncode != 0:
            raise self._error_from_stderr(result.stderr, request)

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise BridgeError(
                code="INVALID_RESPONSE",
                message="PRISM output was not valid JSON",
                request_id=request.request_id,
            ) from exc

        validate_bridge_payload(payload)
        bridge_result = parse_bridge_payload(payload)
        bridge_result = bridge_result.model_copy(update={"request_id": request.request_id})

        self.validate_result(bridge_result)
        return bridge_result

    def _error_from_stderr(self, stderr: bytes, request: BridgeRequest) -> BridgeError:
        try:
            error_payload = json.loads(stderr)
            error_code = error_payload.get("error_code", "PRISM_ERROR")
            error_message = error_payload.get("error_message", "PRISM process failed")
        except json.JSONDecodeError:
            error_code = "PRISM_ERROR"
            error_message = "PRISM process failed"

        if error_code != "PRISM_ERROR":
            error_code = "PRISM_ERROR"

        return BridgeError(code=error_code, message=error_message, request_id=request.request_id)

    async def health_check(self) -> bool:
        """Return True if PRISM is importable at the configured path.
        Never raises."""
        try:
            result = subprocess.run(
                [self.python_executable, "-c", "import prism"],
                capture_output=True,
                timeout=5,
                cwd=str(self.prism_path),
                env=self._build_env(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("health_check failed: %s: %s", type(exc).__name__, exc)
            return False
        return result.returncode == 0

    def get_bridge_version(self) -> str:
        return "bridge:1.0"
