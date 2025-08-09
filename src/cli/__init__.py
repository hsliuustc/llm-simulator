"""
Command-line interface tools for running simulations and comparisons.
"""

from .run import cli, simulate
from .compare import main as compare_main

__all__ = [
    "cli",
    "simulate", 
    "compare_main"
]
