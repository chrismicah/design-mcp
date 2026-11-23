"""Compatibility import for source-checkout clients."""

import sys

from design_mcp import database

sys.modules[__name__] = database
