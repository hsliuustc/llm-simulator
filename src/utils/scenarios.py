from __future__ import annotations

from dataclasses import dataclass

from ..core.config import SimConfig, ArrivalConfig, PromptConfig, OutputConfig, ClusterMonolithic, ClusterDisagg


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


# ============================================================================
# Queue Process Impact Study Scenarios
# ============================================================================

@dataclass
class QueueImpactStudy(Scenario):
    """Base class for queue impact study scenarios."""
    name: str = "queue_impact_study"

    def apply(self, cfg: SimConfig) -> SimConfig:
        raise NotImplementedError


@dataclass
class LowLoadFCFS(QueueImpactStudy):
    """Low load scenario to establish baseline TTFT without queueing."""
    name: str = "low_load_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=0.5)  # Very low load
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class MediumLoadFCFS(QueueImpactStudy):
    """Medium load scenario to observe moderate queueing effects."""
    name: str = "medium_load_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=2.0)  # Medium load
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class HighLoadFCFS(QueueImpactStudy):
    """High load scenario to observe significant queueing effects."""
    name: str = "high_load_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=4.0)  # High load
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class SlowPrefillFCFS(QueueImpactStudy):
    """Scenario with slow prefill processing to study prefill queue impact."""
    name: str = "slow_prefill_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=2.0)
        cfg.prompt_tokens = PromptConfig(mean=6.5, sigma=0.9, min_value=8)  # Longer prompts
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=1,  # Fewer prefill GPUs
            decode_gpus=2, 
            prefill_tokens_per_s=4000.0,  # Slower prefill
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class SlowDecodeFCFS(QueueImpactStudy):
    """Scenario with slow decode processing to study decode queue impact."""
    name: str = "slow_decode_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=2.0)
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=6.0, sigma=1.1, min_value=16)  # Longer outputs
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=1,  # Fewer decode GPUs
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=1000.0  # Slower decode
        )
        return cfg


@dataclass
class BalancedFCFS(QueueImpactStudy):
    """Balanced scenario with equal prefill and decode processing times."""
    name: str = "balanced_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=2.0)
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=4000.0,  # Balanced processing rates
            decode_tokens_per_s=4000.0
        )
        return cfg


@dataclass
class MonolithicFCFS(QueueImpactStudy):
    """Monolithic scenario for comparison with disaggregated FCFS."""
    name: str = "monolithic_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "mono"
        cfg.arrival = ArrivalConfig(rate_per_s=2.0)
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_mono = ClusterMonolithic(
            num_gpus=4,
            prefill_tokens_per_s=8000.0,
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class QueueSaturationStudy(QueueImpactStudy):
    """Study queue saturation effects with very high load."""
    name: str = "queue_saturation_study"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=6.0)  # Very high load
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=0.8, min_value=8)
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.0, min_value=16)
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=2000.0
        )
        return cfg


@dataclass
class VariableLoadFCFS(QueueImpactStudy):
    """Scenario with variable load to study queue dynamics."""
    name: str = "variable_load_fcfs"

    def apply(self, cfg: SimConfig) -> SimConfig:
        cfg.mode = "disagg"
        cfg.arrival = ArrivalConfig(rate_per_s=3.0)  # Variable load
        cfg.prompt_tokens = PromptConfig(mean=6.0, sigma=1.2, min_value=8)  # High variance
        cfg.output_tokens = OutputConfig(mean=5.0, sigma=1.2, min_value=16)  # High variance
        cfg.cluster_disagg = ClusterDisagg(
            prefill_gpus=2, 
            decode_gpus=2, 
            prefill_tokens_per_s=8000.0, 
            decode_tokens_per_s=2000.0
        )
        return cfg