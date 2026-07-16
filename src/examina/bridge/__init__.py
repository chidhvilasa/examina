"""
Bridge package — one-way interface to PRISM.

EXAMINA consumes PRISM output. It never instructs PRISM.
EXAMINA never imports PRISM internal modules directly.
All types in this package are EXAMINA-native translations
of PRISM outputs. PRISM internals never leak beyond this boundary.

See specs/BRIDGE_SPEC_v1.0.md for the complete interface contract.
"""
