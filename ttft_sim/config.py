from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import math
import yaml


@dataclass
class ArrivalConfig:
    rate_per_s: float = 2.0  # Poisson rate


@dataclass
class LogNormalConfig:
    # Log-space parameters for numpy.lognormal
    mean: float = 6.0
    sigma: float = 1.0
    min_value: int = 1


@dataclass
class PromptConfig(LogNormalConfig):
    pass


@dataclass
class OutputConfig(LogNormalConfig):
    pass


@dataclass
class ClusterMonolithic:
    num_gpus: int = 4
    prefill_tokens_per_s: float = 8000.0
    decode_tokens_per_s: float = 2000.0


@dataclass
class ClusterDisagg:
    prefill_gpus: int = 2
    decode_gpus: int = 2
    prefill_tokens_per_s: float = 8000.0
    decode_tokens_per_s: float = 2000.0


@dataclass
class SimConfig:
    mode: str = "disagg"  # "mono" or "disagg"
    sim_seconds: float = 600.0
    warmup_seconds: float = 60.0
    random_seed: int = 42

    arrival: ArrivalConfig = field(default_factory=ArrivalConfig)
    prompt_tokens: PromptConfig = field(default_factory=PromptConfig)
    output_tokens: OutputConfig = field(default_factory=OutputConfig)

    cluster_mono: ClusterMonolithic = field(default_factory=ClusterMonolithic)
    cluster_disagg: ClusterDisagg = field(default_factory=ClusterDisagg)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "sim_seconds": self.sim_seconds,
            "warmup_seconds": self.warmup_seconds,
            "random_seed": self.random_seed,
            "arrival": vars(self.arrival),
            "prompt_tokens": vars(self.prompt_tokens),
            "output_tokens": vars(self.output_tokens),
            "cluster_mono": vars(self.cluster_mono),
            "cluster_disagg": vars(self.cluster_disagg),
        }


# --------- helpers for token distributions ---------

def _real_mean_std_to_log_params(real_mean: float, real_std: float) -> tuple[float, float]:
    if real_mean <= 0 or real_std <= 0:
        raise ValueError("real_mean and real_std must be > 0 for lognormal")
    variance = real_std * real_std
    sigma2 = math.log(1.0 + variance / (real_mean * real_mean))
    sigma = math.sqrt(sigma2)
    mu = math.log(real_mean) - 0.5 * sigma2
    return mu, sigma


def _p50_p90_to_log_params(p50: float, p90: float) -> tuple[float, float]:
    if p50 <= 0 or p90 <= 0 or p90 <= p50:
        raise ValueError("Require 0 < p50 < p90 for lognormal")
    z90 = 1.2815515655446004  # standard normal quantile for 0.9
    mu = math.log(p50)
    sigma = (math.log(p90) - math.log(p50)) / z90
    return mu, sigma


def _parse_token_dist(data: Dict[str, Any], default_min: int) -> LogNormalConfig:
    # Backward compatible: if no 'mode', treat 'mean'/'sigma' as log-space
    mode = data.get("mode", "log")
    min_value = int(data.get("min_value", default_min))

    if mode == "log":
        mu = float(data.get("mean", 6.0))
        sigma = float(data.get("sigma", 1.0))
        return LogNormalConfig(mean=mu, sigma=sigma, min_value=min_value)

    if mode == "real_mean_std":
        real_mean = float(data["mean"])  # required
        real_std = float(data["std"])    # required
        mu, sigma = _real_mean_std_to_log_params(real_mean, real_std)
        return LogNormalConfig(mean=mu, sigma=sigma, min_value=min_value)

    if mode == "p50_p90":
        p50 = float(data["p50"])  # required
        p90 = float(data["p90"])  # required
        mu, sigma = _p50_p90_to_log_params(p50, p90)
        return LogNormalConfig(mean=mu, sigma=sigma, min_value=min_value)

    raise ValueError(f"Unknown token distribution mode: {mode}")


def load_config(path: Optional[str]) -> SimConfig:
    if path is None:
        return SimConfig()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cfg = SimConfig()

    if "mode" in data:
        cfg.mode = data["mode"]
    if "sim_seconds" in data:
        cfg.sim_seconds = float(data["sim_seconds"])
    if "warmup_seconds" in data:
        cfg.warmup_seconds = float(data["warmup_seconds"])
    if "random_seed" in data:
        cfg.random_seed = int(data["random_seed"])

    if "arrival" in data:
        cfg.arrival = ArrivalConfig(**data["arrival"])  # type: ignore[arg-type]

    if "prompt_tokens" in data:
        cfg.prompt_tokens = PromptConfig(**vars(_parse_token_dist(data["prompt_tokens"], cfg.prompt_tokens.min_value)))

    if "output_tokens" in data:
        cfg.output_tokens = OutputConfig(**vars(_parse_token_dist(data["output_tokens"], cfg.output_tokens.min_value)))

    if "cluster_mono" in data:
        cfg.cluster_mono = ClusterMonolithic(**data["cluster_mono"])  # type: ignore[arg-type]
    if "cluster_disagg" in data:
        cfg.cluster_disagg = ClusterDisagg(**data["cluster_disagg"])  # type: ignore[arg-type]

    return cfg