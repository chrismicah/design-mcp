"""Compatibility import for source-checkout clients."""

import sys

from design_mcp import schema

sys.modules[__name__] = schema
