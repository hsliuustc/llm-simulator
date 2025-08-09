"""
TTFT Simulator - A comprehensive simulator for studying Time-To-First-Token performance
in LLM serving systems with support for both monolithic and disaggregated architectures.
"""

__version__ = "0.1.0"
__author__ = "LLM Simulator Team"

from .core.simulator import run_simulation, Request, Metrics
from .core.config import SimConfig, load_config

__all__ = [
    "run_simulation",
    "Request", 
    "Metrics",
    "SimConfig",
    "load_config"
]