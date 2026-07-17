"""
Bridge package — one-way interface to PRISM.

EXAMINA consumes PRISM output. It never instructs PRISM.
EXAMINA never imports PRISM internal modules directly.
All types in this package are EXAMINA-native translations
of PRISM outputs. PRISM internals never leak beyond this boundary.

See specs/BRIDGE_SPEC_v1.1.md for the complete interface contract.
"""

from examina.bridge.client import BridgeClient
from examina.bridge.factory import get_bridge_client
from examina.bridge.local_client import LocalBridgeClient
from examina.bridge.remote_client import RemoteBridgeClient
from examina.bridge.types import (
    BridgeConfidence,
    BridgeContradiction,
    BridgeError,
    BridgeFact,
    BridgeHypothesis,
    BridgeRequest,
    BridgeResult,
    BridgeTimelineEvent,
)

__all__ = [
    "BridgeClient",
    "BridgeConfidence",
    "BridgeContradiction",
    "BridgeError",
    "BridgeFact",
    "BridgeHypothesis",
    "BridgeRequest",
    "BridgeResult",
    "BridgeTimelineEvent",
    "LocalBridgeClient",
    "RemoteBridgeClient",
    "get_bridge_client",
]
