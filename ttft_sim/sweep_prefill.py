#!/usr/bin/env python3
"""Sweep arrival rates and prefill token rates; plot TTFT vs arrival with multiple prefill curves."""

from __future__ import annotations

import argparse
from typing import List, Tuple

import matplotlib.pyplot as plt

from .config import SimConfig
from .simulator import run_simulation


def run_point(mode: str, rate: float, prefill_tokens_per_s: float, cfg: SimConfig) -> dict:
    # Build params using overrides for prefill
    if mode == "mono":
        mono_params = (
            cfg.cluster_mono.num_gpus,
            prefill_tokens_per_s,
            cfg.cluster_mono.decode_tokens_per_s,
        )
        disagg_params = None
    else:
        mono_params = None
        disagg_params = (
            cfg.cluster_disagg.prefill_gpus,
            cfg.cluster_disagg.decode_gpus,
            prefill_tokens_per_s,
            cfg.cluster_disagg.decode_tokens_per_s,
        )

    prompt_tuple = (cfg.prompt_tokens.mean, cfg.prompt_tokens.sigma, cfg.prompt_tokens.min_value)
    output_tuple = (cfg.output_tokens.mean, cfg.output_tokens.sigma, cfg.output_tokens.min_value)

    _, stats = run_simulation(
        mode=mode,
        sim_seconds=cfg.sim_seconds,
        warmup_seconds=cfg.warmup_seconds,
        random_seed=cfg.random_seed,
        arrival_rate_per_s=rate,
        prompt_lognormal=prompt_tuple,
        output_lognormal=output_tuple,
        mono_params=mono_params,
        disagg_params=disagg_params,
    )
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates", type=str, default="0.5,1,2,3,4,5", help="Comma-separated arrival rates per second")
    ap.add_argument("--prefill", type=str, default="4000,8000,16000", help="Comma-separated prefill token rates per GPU (tokens/s)")
    ap.add_argument("--mode", type=str, default="disagg", choices=["mono", "disagg"], help="Which architecture to plot")
    ap.add_argument("--sim-seconds", type=float, default=600.0)
    ap.add_argument("--warmup-seconds", type=float, default=60.0)
    args = ap.parse_args()

    cfg = SimConfig(sim_seconds=args.sim_seconds, warmup_seconds=args.warmup_seconds)

    rates = [float(x) for x in args.rates.split(",")]
    prefill_rates = [float(x) for x in args.prefill.split(",")]

    # Collect results: dict[prefill_rate] -> list[(rate, stats)]
    results = {}
    for p in prefill_rates:
        series = []
        for r in rates:
            stats = run_point(args.mode, r, p, cfg)
            series.append((r, stats))
        results[p] = series

    # Plot percentiles for chosen mode
    plt.figure(figsize=(7, 5))
    markers = ["o", "s", "^", "D", "P", "X"]
    for idx, (p, series) in enumerate(sorted(results.items())):
        xs = [r for r, _ in series]
        p50 = [s["p50_ttft_s"] for _, s in series]
        plt.plot(xs, p50, marker=markers[idx % len(markers)], label=f"prefill {int(p)} tok/s")

    plt.xlabel("Arrival rate (req/s)")
    plt.ylabel("TTFT P50 (s)")
    plt.title(f"TTFT P50 vs arrival — {args.mode} — varying prefill rate")
    plt.grid(True, alpha=0.3)
    plt.legend(title="Prefill rate")
    plt.tight_layout()
    out = f"fig_ttft_vs_rate_prefill_{args.mode}.png"
    plt.savefig(out, dpi=150)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()