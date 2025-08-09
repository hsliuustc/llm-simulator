from __future__ import annotations

from dataclasses import dataclass

from .config import SimConfig, ArrivalConfig, PromptConfig, OutputConfig, ClusterMonolithic, ClusterDisagg


@dataclass
class Scenario:
    name: str

    def apply(self, cfg: SimConfig) -> SimConfig:
        raise NotImplementedError


@dataclass
class LightLoadDisagg(Scenario):
    name: str = "light_disagg"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=1.0)
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(prefill_gpus=2, decode_gpus=2, prefill_tokens_per_s=8000.0, decode_tokens_per_s=2000.0)
        return cfg


@dataclass
class HeavyLoadMono(Scenario):
    name: str = "heavy_mono"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "mono"
        cfg.arrival = ArrivalConfig(rate_per_s=4.0)
        cfg.prompt_tokens = PromptConfig(mean=6.5, sigma=0.9, min_value=8)
        cfg.output_tokens = OutputConfig(mean=6.5, sigma=1.1, min_value=16)
        cfg.cluster_mono = ClusterMonolithic(num_gpus=4, prefill_tokens_per_s=8000.0, decode_tokens_per_s=2000.0)
        return cfg