from __future__ import annotations

import json
import math
from typing import Optional

import click

from ..core.config import SimConfig, load_config
from ..core.simulator import run_simulation


def _log_to_real(mu: float, sigma: float) -> tuple[float, float]:
    mean = math.exp(mu + 0.5 * sigma * sigma)
    var = (math.exp(sigma * sigma) - 1.0) * math.exp(2 * mu + sigma * sigma)
    std = math.sqrt(var)
    return mean, std


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--mode", type=click.Choice(["mono", "disagg"]), default=None, help="Simulation mode override")
@click.option("--sim-seconds", type=float, default=None, help="Simulation horizon in seconds")
@click.option("--warmup-seconds", type=float, default=None, help="Warmup time in seconds (excluded from metrics)")
@click.option("--seed", type=int, default=None, help="Random seed")
@click.option("--config", type=click.Path(exists=True, dir_okay=False), default=None, help="YAML config file path")
@click.option("--dump-ttft", type=click.Path(dir_okay=False), default=None, help="Optional path to dump raw TTFT samples as JSON array")

def simulate(mode: Optional[str], sim_seconds: Optional[float], warmup_seconds: Optional[float], seed: Optional[int], config: Optional[str], dump_ttft: Optional[str]) -> None:
    cfg: SimConfig = load_config(config)

    if mode is not None:
        cfg.mode = mode
    if sim_seconds is not None:
        cfg.sim_seconds = sim_seconds
    if warmup_seconds is not None:
        cfg.warmup_seconds = warmup_seconds
    if seed is not None:
        cfg.random_seed = seed

    if cfg.mode == "mono":
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

    prompt_tuple = (
        cfg.prompt_tokens.mean,
        cfg.prompt_tokens.sigma,
        cfg.prompt_tokens.min_value,
    )
    output_tuple = (
        cfg.output_tokens.mean,
        cfg.output_tokens.sigma,
        cfg.output_tokens.min_value,
    )

    metrics, stats = run_simulation(
        mode=cfg.mode,
        sim_seconds=cfg.sim_seconds,
        warmup_seconds=cfg.warmup_seconds,
        random_seed=cfg.random_seed,
        arrival_rate_per_s=cfg.arrival.rate_per_s,
        prompt_lognormal=prompt_tuple,
        output_lognormal=output_tuple,
        mono_params=mono_params,
        disagg_params=disagg_params,
    )

    # Enrich output with resolved distribution info for verification
    p_mean_real, p_std_real = _log_to_real(cfg.prompt_tokens.mean, cfg.prompt_tokens.sigma)
    o_mean_real, o_std_real = _log_to_real(cfg.output_tokens.mean, cfg.output_tokens.sigma)

    stats.update({
        "arrival_rate_per_s": cfg.arrival.rate_per_s,
        "prompt_tokens_log": {
            "mu": cfg.prompt_tokens.mean,
            "sigma": cfg.prompt_tokens.sigma,
            "min_value": cfg.prompt_tokens.min_value,
        },
        "prompt_tokens_real": {
            "mean": p_mean_real,
            "std": p_std_real,
        },
        "output_tokens_log": {
            "mu": cfg.output_tokens.mean,
            "sigma": cfg.output_tokens.sigma,
            "min_value": cfg.output_tokens.min_value,
        },
        "output_tokens_real": {
            "mean": o_mean_real,
            "std": o_std_real,
        },
    })

    print(json.dumps(stats, indent=2))

    if dump_ttft is not None:
        # Dump all TTFT samples regardless of warmup; plotting script can filter
        with open(dump_ttft, "w", encoding="utf-8") as f:
            json.dump(metrics.ttft_values, f)


if __name__ == "__main__":
    cli()