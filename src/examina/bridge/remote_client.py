"""RemoteBridgeClient — production-mode bridge to an independently deployed PRISM service."""

from __future__ import annotations

from examina.bridge.client import BridgeClient
from examina.bridge.types import BridgeError, BridgeRequest, BridgeResult


class RemoteBridgeClient(BridgeClient):
    """
    Used in production when PRISM runs on a separate server.

    Phase 1 note: `analyze` is a STUB that always raises BridgeError with
    code BRIDGE_UNAVAILABLE. The real implementation (introduced no
    earlier than the phase that needs a live remote PRISM deployment)
    will:
      - POST to {base_url}/analyze
      - Include an `Authorization: Bearer {token}` header
      - Serialize BridgeRequest to JSON
      - Deserialize the response into BridgeResult
      - Call self.validate_result(result)
      - Catch httpx exceptions and re-raise as BridgeError
    """

    def __init__(self, base_url: str, token: str, timeout_seconds: int = 60) -> None:
        self.base_url = base_url
        self.token = token
        self.timeout_seconds = timeout_seconds

    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        """STUB — always raises BridgeError(code="BRIDGE_UNAVAILABLE")."""
        raise BridgeError(
            code="BRIDGE_UNAVAILABLE",
            message=(
                "RemoteBridgeClient is not yet implemented. "
                "Use LocalBridgeClient in development."
            ),
            request_id=request.request_id,
        )

    async def health_check(self) -> bool:
        """
        STUB — always returns False.
        Real implementation performs a GET {base_url}/health request.
        """
        return False

    def get_bridge_version(self) -> str:
        return "bridge:1.0"
