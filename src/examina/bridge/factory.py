"""
Bridge client factory — the ONLY place that chooses between
LocalBridgeClient and RemoteBridgeClient. All other EXAMINA code calls
get_bridge_client() and never knows which implementation it receives.
"""

from __future__ import annotations

import os
from pathlib import Path

from examina.bridge.client import BridgeClient
from examina.bridge.local_client import LocalBridgeClient
from examina.bridge.remote_client import RemoteBridgeClient


def get_bridge_client() -> BridgeClient:
    env = os.environ.get("EXAMINA_ENV", "development")

    if env == "production":
        base_url = os.environ.get("PRISM_BRIDGE_URL")
        token = os.environ.get("PRISM_BRIDGE_TOKEN")
        if not base_url:
            raise RuntimeError(
                "PRISM_BRIDGE_URL environment variable must be set when EXAMINA_ENV=production"
            )
        if not token:
            raise RuntimeError(
                "PRISM_BRIDGE_TOKEN environment variable must be set when EXAMINA_ENV=production"
            )
        return RemoteBridgeClient(base_url=base_url, token=token)

    prism_path = os.environ.get("PRISM_PATH", "../PRISM")
    return LocalBridgeClient(prism_path=Path(prism_path))
