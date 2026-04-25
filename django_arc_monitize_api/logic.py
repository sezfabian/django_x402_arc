import asyncio

import boa
from circlekit import create_gateway_middleware
from .conf import arc_settings

# Global gateway instance
_gateway = None
_gateway_loop_id = None

def get_gateway():
    global _gateway, _gateway_loop_id
    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        # Sync context (no running loop)
        loop_id = None

    # Recreate middleware when loop changes. Some Django dev/runserver async
    # paths create/close request loops, and the underlying async HTTP client is
    # loop-bound.
    if _gateway is None or _gateway_loop_id != loop_id:
        # 1. Validate settings
        arc_settings.check()

        # 2. Configure titanoboa for Arc (same pattern as circle-titanoboa-sdk docs)
        boa.set_network_env(arc_settings.ARC_RPC_URL)

        # 3. Initialize the x402 gateway
        # The SDK uses these to verify signatures against the actual chain state
        _gateway = create_gateway_middleware(
            seller_address=arc_settings.SELLER_ADDRESS,
            chain=arc_settings.NETWORK
        )
        _gateway_loop_id = loop_id
    return _gateway
