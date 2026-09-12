"""
markowizard: Markowitz portfolio optimization and analysis library.

Provides tools for mean-variance optimization, capital allocation,
visualization, and market data fetching.
"""

from importlib.metadata import PackageNotFoundError, version

from markowizard.allocation import CapitalAllocator
from markowizard.core import MarkowitzOptimizer

try:
    __version__ = version("markowizard")
except PackageNotFoundError:
    __version__ = "0.2.0"

__all__ = [
    "CapitalAllocator",
    "MarkowitzOptimizer",
]
