from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import simpy


@dataclass
class Request:
    request_id: int
    arrival_time: float
    prompt_tokens: int
    output_tokens: int


@dataclass
class Metrics:
    ttft_values: List[float]
    ttft_times: List[float]
    completed_requests: int
    dropped_requests: int
    start_time: float
    end_time: float
    # GPU time accounting (seconds of GPU occupancy)
    mono_gpu_time_total: float
    prefill_gpu_time_total: float
    decode_gpu_time_total: float

    def add_ttft(self, value: float, event_time: float) -> None:
        self.ttft_values.append(value)
        self.ttft_times.append(event_time)

    def add_gpu_time_mono(self, t: float) -> None:
        self.mono_gpu_time_total += t

    def add_gpu_time_prefill(self, t: float) -> None:
        self.prefill_gpu_time_total += t

    def add_gpu_time_decode(self, t: float) -> None:
        self.decode_gpu_time_total += t

    def mark_completed(self) -> None:
        self.completed_requests += 1

    def finalize(self, end_time: float) -> None:
        self.end_time = end_time

    def summary(self, warmup: float = 0.0) -> dict:
        filtered_values = []
        for i, event_time in enumerate(self.ttft_times):
            if event_time >= warmup:
                filtered_values.append(self.ttft_values[i])
        if not filtered_values:
            return {
                "num_samples": 0,
                "mean_ttft_s": float("nan"),
                "p50_ttft_s": float("nan"),
                "p90_ttft_s": float("nan"),
                "p99_ttft_s": float("nan"),
            }
        arr = np.array(filtered_values, dtype=float)
        return {
            "num_samples": len(filtered_values),
            "mean_ttft_s": float(arr.mean()),
            "p50_ttft_s": float(np.percentile(arr, 50)),
            "p90_ttft_s": float(np.percentile(arr, 90)),
            "p99_ttft_s": float(np.percentile(arr, 99)),
        }


# Distribution helpers

def poisson_interarrival_time(rate_per_s: float, rng: random.Random) -> float:
    return rng.expovariate(rate_per_s)


def lognormal_tokens(mean: float, sigma: float, min_value: int, rng: random.Random) -> int:
    val = np.random.lognormal(mean=mean, sigma=sigma)
    return max(int(val), min_value)


class MonolithicSimulator:
    def __init__(
        self,
        env: simpy.Environment,
        num_gpus: int,
        prefill_tokens_per_s: float,
        decode_tokens_per_s: float,
    ) -> None:
        self.env = env
        self.num_gpus = num_gpus
        self.prefill_rate = prefill_tokens_per_s
        self.decode_rate = decode_tokens_per_s
        self.gpu = simpy.Resource(env, capacity=num_gpus)

    def process(self, req: Request, metrics: Metrics) -> simpy.events.Event:
        with self.gpu.request() as ticket:
            yield ticket
            service_start = self.env.now
            prefill_time = req.prompt_tokens / self.prefill_rate
            first_token_time = 1.0 / self.decode_rate
            # Wait until TTFT within the service while holding the GPU
            yield self.env.timeout(prefill_time + first_token_time)
            ttft = self.env.now - req.arrival_time
            metrics.add_ttft(self.env.now, ttft)
            # Finish remaining decode while still holding the GPU
            remaining_decode_tokens = max(req.output_tokens - 1, 0)
            remaining_decode_time = remaining_decode_tokens / self.decode_rate
            yield self.env.timeout(remaining_decode_time)
            # GPU released automatically on context manager exit


class DisaggregatedSimulator:
    def __init__(
        self,
        env: simpy.Environment,
        prefill_gpus: int,
        decode_gpus: int,
        prefill_tokens_per_s: float,
        decode_tokens_per_s: float,
    ) -> None:
        self.env = env
        self.prefill_rate = prefill_tokens_per_s
        self.decode_rate = decode_tokens_per_s
        self.prefill_pool = simpy.Resource(env, capacity=prefill_gpus)
        self.decode_pool = simpy.Resource(env, capacity=decode_gpus)
        self.prefill_gpus = prefill_gpus
        self.decode_gpus = decode_gpus

    def process(self, req: Request, metrics: Metrics) -> simpy.events.Event:
        # Stage 1: Prefill on prefill pool
        with self.prefill_pool.request() as prefill_ticket:
            yield prefill_ticket
            prefill_time = req.prompt_tokens / self.prefill_rate
            yield self.env.timeout(prefill_time)
            metrics.add_gpu_time_prefill(prefill_time)
        # Stage 2: First decode token on decode pool
        with self.decode_pool.request() as decode_ticket:
            yield decode_ticket
            first_token_time = 1.0 / self.decode_rate
            yield self.env.timeout(first_token_time)
            ttft = self.env.now - req.arrival_time
            metrics.add_ttft(ttft, self.env.now)
            # Continue generating remaining tokens while holding decode pool
            remaining_decode_tokens = max(req.output_tokens - 1, 0)
            remaining_decode_time = remaining_decode_tokens / self.decode_rate
            total_decode_time = first_token_time + remaining_decode_time
            metrics.add_gpu_time_decode(total_decode_time)
            yield self.env.timeout(remaining_decode_time)
            metrics.mark_completed()


def run_simulation(
    mode: str,
    sim_seconds: float,
    warmup_seconds: float,
    random_seed: int,
    arrival_rate_per_s: float,
    prompt_lognormal: Tuple[float, float, int],
    output_lognormal: Tuple[float, float, int],
    mono_params: Optional[Tuple[int, float, float]] = None,
    disagg_params: Optional[Tuple[int, int, float, float]] = None,
) -> Tuple[Metrics, dict]:
    assert mode in ("mono", "disagg")
    rng = random.Random(random_seed)
    np.random.seed(random_seed)

    env = simpy.Environment()

    if mode == "mono":
        assert mono_params is not None
        num_gpus, prefill_r, decode_r = mono_params
        sim = MonolithicSimulator(env, num_gpus, prefill_r, decode_r)
    else:
        assert disagg_params is not None
        prefill_gpus, decode_gpus, prefill_r, decode_r = disagg_params
        sim = DisaggregatedSimulator(env, prefill_gpus, decode_gpus, prefill_r, decode_r)

    metrics = Metrics(
        ttft_values=[],
        ttft_times=[],
        completed_requests=0,
        dropped_requests=0,
        start_time=0.0,
        end_time=0.0,
        mono_gpu_time_total=0.0,
        prefill_gpu_time_total=0.0,
        decode_gpu_time_total=0.0,
    )

    def arrival_process(env: simpy.Environment) -> simpy.events.Event:
        request_id = 0
        while True:
            ia = poisson_interarrival_time(arrival_rate_per_s, rng)
            yield env.timeout(ia)
            arrival_time = env.now
            prompt_tokens = lognormal_tokens(*prompt_lognormal, rng=rng)
            output_tokens = lognormal_tokens(*output_lognormal, rng=rng)
            req = Request(
                request_id=request_id,
                arrival_time=arrival_time,
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
            )
            request_id += 1
            env.process(sim.process(req, metrics))

    env.process(arrival_process(env))
    metrics.start_time = env.now
    env.run(until=sim_seconds)
    metrics.finalize(end_time=env.now)

    # Build summary
    stats = metrics.summary(warmup=warmup_seconds)
    elapsed = metrics.end_time - metrics.start_time
    stats.update({
        "elapsed_s": elapsed,
        "mode": mode,
        "throughput_rps": metrics.completed_requests / elapsed if elapsed > 0 else float("nan"),
    })

    if mode == "mono":
        util = metrics.mono_gpu_time_total / (num_gpus * elapsed) if elapsed > 0 else float("nan")
        stats.update({
            "utilization_gpu": util,
            "num_gpus": num_gpus,
        })
    else:
        util_prefill = metrics.prefill_gpu_time_total / (prefill_gpus * elapsed) if elapsed > 0 else float("nan")
        util_decode = metrics.decode_gpu_time_total / (decode_gpus * elapsed) if elapsed > 0 else float("nan")
        stats.update({
            "utilization_prefill": util_prefill,
            "utilization_decode": util_decode,
            "prefill_gpus": prefill_gpus,
            "decode_gpus": decode_gpus,
        })

    return metrics, stats