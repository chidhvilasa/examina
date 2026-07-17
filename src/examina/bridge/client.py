"""
BridgeClient abstract interface.

See specs/BRIDGE_SPEC_v1.1.md. Concrete implementations
(LocalBridgeClient, RemoteBridgeClient) never call PRISM-internal
modules directly outside this package's boundary.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from examina.bridge.types import BridgeError, BridgeRequest, BridgeResult


class BridgeClient(ABC):
    @abstractmethod
    async def analyze(self, request: BridgeRequest) -> BridgeResult:
        """
        Send a file to PRISM for analysis and return structured results.

        Raises BridgeError on any failure.
        Never raises any other exception type.
        All exceptions from underlying transport must be caught
        and re-raised as BridgeError with the appropriate code.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Return True if the bridge is reachable and PRISM is responsive.
        Return False (never raise) if the bridge is unavailable.
        """

    @abstractmethod
    def get_bridge_version(self) -> str:
        """Return the bridge version string this client implements."""

    def validate_result(self, result: BridgeResult) -> None:
        """
        Validate that a BridgeResult is internally consistent.

        Raises BridgeError with code INVALID_RESPONSE if:
          - bridge_version does not start with "bridge:"
          - hypotheses rank values are not unique
          - hypotheses rank values are not contiguous from 1
          - partial_analysis is True but partial_reason is None
        """
        if not result.bridge_version.startswith("bridge:"):
            raise BridgeError(
                code="INVALID_RESPONSE",
                message="bridge_version must start with 'bridge:'",
                request_id=result.request_id,
            )

        ranks = [h.rank for h in result.hypotheses]
        if len(set(ranks)) != len(ranks):
            raise BridgeError(
                code="INVALID_RESPONSE",
                message="hypotheses rank values are not unique",
                request_id=result.request_id,
            )
        if ranks and set(ranks) != set(range(1, len(ranks) + 1)):
            raise BridgeError(
                code="INVALID_RESPONSE",
                message="hypotheses rank values are not contiguous from 1",
                request_id=result.request_id,
            )

        if result.partial_analysis and not result.partial_reason:
            raise BridgeError(
                code="INVALID_RESPONSE",
                message="partial_analysis is True but partial_reason is not set",
                request_id=result.request_id,
            )
