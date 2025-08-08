#!/usr/bin/env python3
"""Sweep arrival rates and plot TTFT percentiles vs arrival rate for mono/disagg."""

from __future__ import annotations

import argparse
from typing import List, Tuple

import matplotlib.pyplot as plt

from .config import SimConfig
from .simulator import run_simulation


def run_point(mode: str, rate: float, cfg: SimConfig) -> dict:
    # Use same cfg but override mode and arrival rate
    cfg_local = SimConfig(**cfg.to_dict())  # shallow copy via dict
    cfg_local.mode = mode
    # Build params
    if mode == "mono":
        mono_params = (
            cfg.cluster_mono.num_gpus,
            cfg.cluster_mono.prefill_tokens_per_s,
            cfg.cluster_mono.decode_tokens_per_s,
        )
        disagg_params = None
    else:
        mono_params = None
        disagg_params = (
            cfg.cluster_disagg.prefill_gpus,
            cfg.cluster_disagg.decode_gpus,
            cfg.cluster_disagg.prefill_tokens_per_s,
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
    ap.add_argument("--sim-seconds", type=float, default=600.0)
    ap.add_argument("--warmup-seconds", type=float, default=60.0)
    args = ap.parse_args()

    cfg = SimConfig(sim_seconds=args.sim_seconds, warmup_seconds=args.warmup_seconds)

    rates = [float(x) for x in args.rates.split(",")]

    results = {"mono": [], "disagg": []}
    for mode in ("mono", "disagg"):
        for r in rates:
            stats = run_point(mode, r, cfg)
            results[mode].append((r, stats))

    # Plot percentiles
    plt.figure(figsize=(7, 5))
    for mode, color in [("mono", "C0"), ("disagg", "C3")]:
        xs = [r for r, _ in results[mode]]
        p50 = [s["p50_ttft_s"] for _, s in results[mode]]
        p90 = [s["p90_ttft_s"] for _, s in results[mode]]
        p99 = [s["p99_ttft_s"] for _, s in results[mode]]
        plt.plot(xs, p50, marker="o", color=color, linestyle="-", label=f"{mode} P50")
        plt.plot(xs, p90, marker="s", color=color, linestyle="--", label=f"{mode} P90")
        plt.plot(xs, p99, marker="^", color=color, linestyle=":", label=f"{mode} P99")

    plt.xlabel("Arrival rate (req/s)")
    plt.ylabel("TTFT (s)")
    plt.title("TTFT percentiles vs arrival rate")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig_ttft_vs_rate.png", dpi=150)
    print("Saved fig_ttft_vs_rate.png")


if __name__ == "__main__":
    main()