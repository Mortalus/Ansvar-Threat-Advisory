"""
Backward-compatible shim for legacy imports.

Older tests and code may import ThreatGenerator from this module.
We re-export the modern ThreatGeneratorV3 to maintain compatibility.
"""

from .threat_generator_v3 import ThreatGeneratorV3 as ThreatGenerator  # noqa: F401


