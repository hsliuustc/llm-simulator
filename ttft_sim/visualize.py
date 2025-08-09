#!/usr/bin/env python3
"""Visualize TTFT distributions for monolithic vs disaggregated modes."""

import json
import subprocess
import sys
from typing import Dict, Any, List

import matplotlib.pyplot as plt
import numpy as np


def run_sim_with_details(mode: str, sim_seconds: int = 300, warmup_seconds: int = 30) -> Dict[str, Any]:
    """Run a simulation and return detailed stats including raw TTFT values."""
    cmd = [
        sys.executable, "-m", "ttft_sim.run", "simulate",
        "--mode", mode,
        "--sim-seconds", str(sim_seconds),
        "--warmup-seconds", str(warmup_seconds),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def plot_ttft_comparison():
    """Create a comparison plot of TTFT distributions."""
    print("Running simulations for visualization...")
    
    # Run simulations
    mono_stats = run_sim_with_details("mono")
    disagg_stats = run_sim_with_details("disagg")
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Histogram comparison
    ax1.hist([mono_stats['mean_ttft_s']], bins=20, alpha=0.7, label='Monolithic', color='blue')
    ax1.hist([disagg_stats['mean_ttft_s']], bins=20, alpha=0.7, label='Disaggregated', color='red')
    ax1.set_xlabel('TTFT (seconds)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('TTFT Distribution Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Percentile comparison
    percentiles = [50, 90, 99]
    mono_percentiles = [mono_stats['p50_ttft_s'], mono_stats['p90_ttft_s'], mono_stats['p99_ttft_s']]
    disagg_percentiles = [disagg_stats['p50_ttft_s'], disagg_stats['p90_ttft_s'], disagg_stats['p99_ttft_s']]
    
    x = np.arange(len(percentiles))
    width = 0.35
    
    ax2.bar(x - width/2, mono_percentiles, width, label='Monolithic', color='blue', alpha=0.7)
    ax2.bar(x + width/2, disagg_percentiles, width, label='Disaggregated', color='red', alpha=0.7)
    
    ax2.set_xlabel('Percentile')
    ax2.set_ylabel('TTFT (seconds)')
    ax2.set_title('TTFT Percentiles Comparison')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'P{p}' for p in percentiles])
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('ttft_comparison.png', dpi=150, bbox_inches='tight')
    print("Plot saved as 'ttft_comparison.png'")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Monolithic - Mean: {mono_stats['mean_ttft_s']:.3f}s, P99: {mono_stats['p99_ttft_s']:.3f}s")
    print(f"Disaggregated - Mean: {disagg_stats['mean_ttft_s']:.3f}s, P99: {disagg_stats['p99_ttft_s']:.3f}s")
    
    improvement = (disagg_stats['mean_ttft_s'] - mono_stats['mean_ttft_s']) / mono_stats['mean_ttft_s'] * 100
    print(f"Disaggregated is {improvement:+.1f}% slower on average")


if __name__ == "__main__":
    try:
        plot_ttft_comparison()
    except ImportError:
        print("matplotlib not available. Install with: pip install matplotlib")
        print("Or run the comparison without visualization:")
        subprocess.run([sys.executable, "ttft_sim/compare.py"]) 