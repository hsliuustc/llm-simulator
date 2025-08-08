from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import yaml


@dataclass
class ArrivalConfig:
    rate_per_s: float = 2.0  # Poisson rate


@dataclass
class LogNormalConfig:
    mean: float = 6.0  # log-space mean for numpy.lognormal
    sigma: float = 1.0  # log-space sigma
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

    arrival: ArrivalConfig = ArrivalConfig()
    prompt_tokens: PromptConfig = PromptConfig()
    output_tokens: OutputConfig = OutputConfig()

    cluster_mono: ClusterMonolithic = ClusterMonolithic()
    cluster_disagg: ClusterDisagg = ClusterDisagg()

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
        cfg.prompt_tokens = PromptConfig(**data["prompt_tokens"])  # type: ignore[arg-type]
    if "output_tokens" in data:
        cfg.output_tokens = OutputConfig(**data["output_tokens"])  # type: ignore[arg-type]
    if "cluster_mono" in data:
        cfg.cluster_mono = ClusterMonolithic(**data["cluster_mono"])  # type: ignore[arg-type]
    if "cluster_disagg" in data:
        cfg.cluster_disagg = ClusterDisagg(**data["cluster_disagg"])  # type: ignore[arg-type]

    return cfg