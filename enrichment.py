"""Compatibility import for source-checkout clients."""

import sys

from design_mcp import enrichment

sys.modules[__name__] = enrichment
