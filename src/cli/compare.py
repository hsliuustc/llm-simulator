#!/usr/bin/env python3
"""Quick comparison of monolithic vs disaggregated TTFT performance."""

import json
import subprocess
import sys
from typing import Dict, Any


def run_sim(mode: str, sim_seconds: int = 300, warmup_seconds: int = 30) -> Dict[str, Any]:
    """Run a simulation and return the stats."""
    cmd = [
        sys.executable, "-m", "src.cli.run", "simulate",
        "--mode", mode,
        "--sim-seconds", str(sim_seconds),
        "--warmup-seconds", str(warmup_seconds),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def main():
    print("Running TTFT comparison (monolithic vs disaggregated)...")
    print("=" * 60)
    
    # Run both simulations
    mono_stats = run_sim("mono")
    disagg_stats = run_sim("disagg")
    
    print(f"Monolithic results:")
    print(f"  Samples: {mono_stats['num_samples']}")
    print(f"  Mean TTFT: {mono_stats['mean_ttft_s']:.3f}s")
    print(f"  P50 TTFT: {mono_stats['p50_ttft_s']:.3f}s")
    print(f"  P90 TTFT: {mono_stats['p90_ttft_s']:.3f}s")
    print(f"  P99 TTFT: {mono_stats['p99_ttft_s']:.3f}s")
    print()
    
    print(f"Disaggregated results:")
    print(f"  Samples: {disagg_stats['num_samples']}")
    print(f"  Mean TTFT: {disagg_stats['mean_ttft_s']:.3f}s")
    print(f"  P50 TTFT: {disagg_stats['p50_ttft_s']:.3f}s")
    print(f"  P90 TTFT: {disagg_stats['p90_ttft_s']:.3f}s")
    print(f"  P99 TTFT: {disagg_stats['p99_ttft_s']:.3f}s")
    print()
    
    # Calculate improvements
    mean_improvement = (disagg_stats['mean_ttft_s'] - mono_stats['mean_ttft_s']) / mono_stats['mean_ttft_s'] * 100
    p50_improvement = (disagg_stats['p50_ttft_s'] - mono_stats['p50_ttft_s']) / mono_stats['p50_ttft_s'] * 100
    p90_improvement = (disagg_stats['p90_ttft_s'] - mono_stats['p90_ttft_s']) / mono_stats['p90_ttft_s'] * 100
    
    print(f"Comparison (disagg vs mono):")
    print(f"  Mean TTFT: {mean_improvement:+.1f}%")
    print(f"  P50 TTFT: {p50_improvement:+.1f}%")
    print(f"  P90 TTFT: {p90_improvement:+.1f}%")
    print()
    print("Note: Positive values mean disaggregated is slower (expected due to")
    print("      queueing at both prefill and decode pools).")


if __name__ == "__main__":
    main() 