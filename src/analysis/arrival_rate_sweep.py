#!/usr/bin/env python3
"""Arrival Rate Sweep Analysis - Study decode queue impact across arrival rates 0.5 to 10."""

from __future__ import annotations

import argparse
import json
import math
from typing import List, Dict, Any
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from ..core.config import SimConfig, ArrivalConfig, PromptConfig, OutputConfig, ClusterDisagg
from ..core.simulator import run_simulation


@dataclass
class ArrivalRateResult:
    """Results from arrival rate sweep analysis."""
    arrival_rate: float
    prefill_gpus: int
    decode_gpus: int
    decode_rate: float
    mean_ttft: float
    p50_ttft: float
    p90_ttft: float
    p99_ttft: float
    utilization_prefill: float
    utilization_decode: float
    queue_wait_time_prefill: float
    queue_wait_time_decode: float
    service_time_prefill: float
    service_time_decode: float
    throughput: float


class ArrivalRateAnalyzer:
    """Analyzer for arrival rate sweep analysis."""
    
    def __init__(self, sim_seconds: float = 300.0, warmup_seconds: float = 30.0):
        self.sim_seconds = sim_seconds
        self.warmup_seconds = warmup_seconds
        self.results: List[ArrivalRateResult] = []
    
    def run_arrival_rate_scenario(self, 
                                arrival_rate: float,
                                prefill_gpus: int = 2,
                                decode_gpus: int = 2,
                                decode_rate: float = 2000.0) -> ArrivalRateResult:
        """Run a specific arrival rate scenario."""
        
        # Create configuration
        cfg = SimConfig(
            mode="disagg",
            sim_seconds=self.sim_seconds,
            warmup_seconds=self.warmup_seconds,
            arrival=ArrivalConfig(rate_per_s=arrival_rate),
            prompt_tokens=PromptConfig(mean=6.0, sigma=0.8, min_value=8),
            output_tokens=OutputConfig(mean=5.0, sigma=1.0, min_value=16),
            cluster_disagg=ClusterDisagg(
                prefill_gpus=prefill_gpus,
                decode_gpus=decode_gpus,
                prefill_tokens_per_s=8000.0,
                decode_tokens_per_s=decode_rate
            )
        )
        
        # Build parameters for simulation
        disagg_params = (
            cfg.cluster_disagg.prefill_gpus,
            cfg.cluster_disagg.decode_gpus,
            cfg.cluster_disagg.prefill_tokens_per_s,
            cfg.cluster_disagg.decode_tokens_per_s,
        )
        
        prompt_tuple = (cfg.prompt_tokens.mean, cfg.prompt_tokens.sigma, cfg.prompt_tokens.min_value)
        output_tuple = (cfg.output_tokens.mean, cfg.output_tokens.sigma, cfg.output_tokens.min_value)
        
        _, stats = run_simulation(
            mode=cfg.mode,
            sim_seconds=cfg.sim_seconds,
            warmup_seconds=cfg.warmup_seconds,
            random_seed=cfg.random_seed,
            arrival_rate_per_s=cfg.arrival.rate_per_s,
            prompt_lognormal=prompt_tuple,
            output_lognormal=output_tuple,
            mono_params=None,
            disagg_params=disagg_params,
        )
        
        # Calculate queue wait times and service times
        prefill_service_time = math.exp(cfg.prompt_tokens.mean + 0.5 * cfg.prompt_tokens.sigma**2) / cfg.cluster_disagg.prefill_tokens_per_s
        decode_service_time = 1.0 / cfg.cluster_disagg.decode_tokens_per_s
        
        utilization_prefill = stats.get("utilization_prefill", 0.0)
        utilization_decode = stats.get("utilization_decode", 0.0)
        
        queue_wait_prefill = self._estimate_queue_wait_time(
            utilization_prefill, prefill_service_time, cfg.cluster_disagg.prefill_gpus
        )
        queue_wait_decode = self._estimate_queue_wait_time(
            utilization_decode, decode_service_time, cfg.cluster_disagg.decode_gpus
        )
        
        return ArrivalRateResult(
            arrival_rate=arrival_rate,
            prefill_gpus=prefill_gpus,
            decode_gpus=decode_gpus,
            decode_rate=decode_rate,
            mean_ttft=stats["mean_ttft_s"],
            p50_ttft=stats["p50_ttft_s"],
            p90_ttft=stats["p90_ttft_s"],
            p99_ttft=stats["p99_ttft_s"],
            utilization_prefill=utilization_prefill,
            utilization_decode=utilization_decode,
            queue_wait_time_prefill=queue_wait_prefill,
            queue_wait_time_decode=queue_wait_decode,
            service_time_prefill=prefill_service_time,
            service_time_decode=decode_service_time,
            throughput=stats.get("throughput_rps", 0.0),
        )
    
    def _estimate_queue_wait_time(self, utilization: float, service_time: float, num_servers: int) -> float:
        """Estimate queue wait time using M/M/c queue approximation."""
        if utilization >= 1.0:
            return float('inf')
        
        if num_servers == 1:
            if utilization >= 1.0:
                return float('inf')
            return (utilization / (1 - utilization)) * service_time
        else:
            if utilization >= num_servers:
                return float('inf')
            
            rho = utilization / num_servers
            if rho >= 1.0:
                return float('inf')
            
            wait_time = (rho / (1 - rho)) * service_time / num_servers
            return max(0.0, wait_time)
    
    def run_arrival_rate_sweep(self, 
                              rates: List[float] = None,
                              prefill_gpus: int = 2,
                              decode_gpus: int = 2,
                              decode_rate: float = 2000.0) -> List[ArrivalRateResult]:
        """Run arrival rate sweep analysis."""
        
        if rates is None:
            rates = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        results = []
        print(f"🔄 Running arrival rate sweep from {min(rates)} to {max(rates)} req/s...")
        
        for rate in rates:
            try:
                result = self.run_arrival_rate_scenario(
                    arrival_rate=rate,
                    prefill_gpus=prefill_gpus,
                    decode_gpus=decode_gpus,
                    decode_rate=decode_rate
                )
                results.append(result)
                print(f"✅ Rate {rate:.1f} req/s: {result.mean_ttft:.2f}s TTFT "
                      f"(Decode util: {result.utilization_decode:.2f})")
            except Exception as e:
                print(f"❌ Failed rate {rate}: {e}")
        
        self.results = results
        return results
    
    def run_multi_config_sweep(self) -> Dict[str, List[ArrivalRateResult]]:
        """Run arrival rate sweep for multiple configurations."""
        rates = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        configurations = {
            "2_prefill_2_decode": (2, 2, 2000.0),
            "2_prefill_1_decode": (2, 1, 2000.0),
            "2_prefill_4_decode": (2, 4, 2000.0),
            "2_prefill_2_decode_slow": (2, 2, 1000.0),
        }
        
        all_results = {}
        
        for config_name, (prefill_gpus, decode_gpus, decode_rate) in configurations.items():
            print(f"\n🚀 Running {config_name} configuration...")
            results = self.run_arrival_rate_sweep(rates, prefill_gpus, decode_gpus, decode_rate)
            all_results[config_name] = results
        
        return all_results
    
    def plot_arrival_rate_analysis(self, results: Dict[str, List[ArrivalRateResult]] = None, 
                                 save_path: str = "arrival_rate_sweep.png"):
        """Create visualization of arrival rate sweep analysis."""
        if results is None:
            results = {"2_prefill_2_decode": self.results}
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("Decode Queue Impact: Arrival Rate Sweep (0.5 to 10 req/s)", fontsize=16)
        
        colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']
        
        # 1. TTFT vs Arrival Rate
        ax1 = axes[0, 0]
        for i, (config_name, config_results) in enumerate(results.items()):
            rates = [r.arrival_rate for r in config_results]
            ttft_values = [r.mean_ttft for r in config_results]
            ax1.plot(rates, ttft_values, 'o-', label=config_name, color=colors[i % len(colors)], linewidth=2)
        
        ax1.set_xlabel("Arrival Rate (req/s)")
        ax1.set_ylabel("Mean TTFT (s)")
        ax1.set_title("TTFT vs Arrival Rate")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')  # Log scale to show exponential growth
        
        # 2. P99 TTFT vs Arrival Rate
        ax2 = axes[0, 1]
        for i, (config_name, config_results) in enumerate(results.items()):
            rates = [r.arrival_rate for r in config_results]
            p99_values = [r.p99_ttft for r in config_results]
            ax2.plot(rates, p99_values, 's-', label=config_name, color=colors[i % len(colors)], linewidth=2)
        
        ax2.set_xlabel("Arrival Rate (req/s)")
        ax2.set_ylabel("P99 TTFT (s)")
        ax2.set_title("P99 TTFT vs Arrival Rate")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_yscale('log')
        
        # 3. Decode Utilization vs Arrival Rate
        ax3 = axes[0, 2]
        for i, (config_name, config_results) in enumerate(results.items()):
            rates = [r.arrival_rate for r in config_results]
            decode_utils = [r.utilization_decode for r in config_results]
            ax3.plot(rates, decode_utils, '^-', label=config_name, color=colors[i % len(colors)], linewidth=2)
        
        ax3.set_xlabel("Arrival Rate (req/s)")
        ax3.set_ylabel("Decode Utilization")
        ax3.set_title("Decode Utilization vs Arrival Rate")
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Saturation')
        
        # 4. Queue Wait Times vs Arrival Rate
        ax4 = axes[1, 0]
        for i, (config_name, config_results) in enumerate(results.items()):
            rates = [r.arrival_rate for r in config_results]
            decode_wait = [r.queue_wait_time_decode for r in config_results]
            ax4.plot(rates, decode_wait, 'o-', label=f"{config_name} (Decode)", 
                    color=colors[i % len(colors)], linewidth=2)
        
        ax4.set_xlabel("Arrival Rate (req/s)")
        ax4.set_ylabel("Decode Queue Wait Time (s)")
        ax4.set_title("Decode Queue Wait Time vs Arrival Rate")
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_yscale('log')
        
        # 5. Throughput vs Arrival Rate
        ax5 = axes[1, 1]
        for i, (config_name, config_results) in enumerate(results.items()):
            rates = [r.arrival_rate for r in config_results]
            throughput = [r.throughput for r in config_results]
            ax5.plot(rates, throughput, 's-', label=config_name, color=colors[i % len(colors)], linewidth=2)
        
        # Add ideal throughput line
        max_rate = max([max([r.arrival_rate for r in config_results]) for config_results in results.values()])
        ax5.plot([0, max_rate], [0, max_rate], '--', color='gray', alpha=0.5, label='Ideal')
        
        ax5.set_xlabel("Arrival Rate (req/s)")
        ax5.set_ylabel("Throughput (req/s)")
        ax5.set_title("Throughput vs Arrival Rate")
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6. Bottleneck Analysis
        ax6 = axes[1, 2]
        for i, (config_name, config_results) in enumerate(results.items()):
            prefill_utils = [r.utilization_prefill for r in config_results]
            decode_utils = [r.utilization_decode for r in config_results]
            ax6.scatter(prefill_utils, decode_utils, s=50, alpha=0.7, 
                       label=config_name, color=colors[i % len(colors)])
        
        ax6.set_xlabel("Prefill Utilization")
        ax6.set_ylabel("Decode Utilization")
        ax6.set_title("Resource Utilization Analysis")
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        ax6.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
        ax6.axvline(x=1.0, color='red', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved arrival rate sweep analysis to {save_path}")
    
    def generate_arrival_rate_report(self, results: Dict[str, List[ArrivalRateResult]] = None,
                                   save_path: str = "arrival_rate_sweep_report.json"):
        """Generate detailed report of arrival rate sweep analysis."""
        if results is None:
            results = {"2_prefill_2_decode": self.results}
        
        report = {
            "analysis_parameters": {
                "simulation_seconds": self.sim_seconds,
                "warmup_seconds": self.warmup_seconds,
                "arrival_rates": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
            },
            "configurations": {},
            "key_insights": [],
            "bottleneck_analysis": {}
        }
        
        # Add configuration results
        for config_name, config_results in results.items():
            report["configurations"][config_name] = {
                "results": [],
                "bottleneck_threshold": None,
                "saturation_point": None
            }
            
            for result in config_results:
                result_data = {
                    "arrival_rate": result.arrival_rate,
                    "mean_ttft": result.mean_ttft,
                    "p99_ttft": result.p99_ttft,
                    "utilization_prefill": result.utilization_prefill,
                    "utilization_decode": result.utilization_decode,
                    "queue_wait_time_decode": result.queue_wait_time_decode,
                    "throughput": result.throughput
                }
                report["configurations"][config_name]["results"].append(result_data)
            
            # Find bottleneck threshold (when decode utilization > 0.8)
            bottleneck_results = [r for r in config_results if r.utilization_decode > 0.8]
            if bottleneck_results:
                bottleneck_threshold = min([r.arrival_rate for r in bottleneck_results])
                report["configurations"][config_name]["bottleneck_threshold"] = bottleneck_threshold
                report["key_insights"].append(
                    f"{config_name}: Bottleneck at {bottleneck_threshold:.1f} req/s"
                )
            
            # Find saturation point (when decode utilization > 0.95)
            saturation_results = [r for r in config_results if r.utilization_decode > 0.95]
            if saturation_results:
                saturation_point = min([r.arrival_rate for r in saturation_results])
                report["configurations"][config_name]["saturation_point"] = saturation_point
                report["key_insights"].append(
                    f"{config_name}: Saturation at {saturation_point:.1f} req/s"
                )
        
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Saved arrival rate sweep report to {save_path}")
        return report


def main():
    """Main function for arrival rate sweep analysis."""
    parser = argparse.ArgumentParser(description="Arrival Rate Sweep Analysis")
    parser.add_argument("--sim-seconds", type=float, default=300.0, help="Simulation duration")
    parser.add_argument("--warmup-seconds", type=float, default=30.0, help="Warmup period")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory")
    parser.add_argument("--config", type=str, default="all", 
                       choices=["all", "2_prefill_2_decode", "2_prefill_1_decode", "2_prefill_4_decode"],
                       help="Configuration to analyze")
    
    args = parser.parse_args()
    
    analyzer = ArrivalRateAnalyzer(sim_seconds=args.sim_seconds, warmup_seconds=args.warmup_seconds)
    
    print("🚀 Starting arrival rate sweep analysis (0.5 to 10 req/s)...")
    
    if args.config == "all":
        results = analyzer.run_multi_config_sweep()
    else:
        # Run single configuration
        config_map = {
            "2_prefill_2_decode": (2, 2, 2000.0),
            "2_prefill_1_decode": (2, 1, 2000.0),
            "2_prefill_4_decode": (2, 4, 2000.0),
        }
        
        prefill_gpus, decode_gpus, decode_rate = config_map[args.config]
        rates = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        config_results = analyzer.run_arrival_rate_sweep(rates, prefill_gpus, decode_gpus, decode_rate)
        results = {args.config: config_results}
    
    # Generate outputs
    analyzer.plot_arrival_rate_analysis(results, f"{args.output_dir}/arrival_rate_sweep.png")
    analyzer.generate_arrival_rate_report(results, f"{args.output_dir}/arrival_rate_sweep_report.json")
    
    print("\n🎯 Arrival Rate Sweep Analysis Summary:")
    print("=" * 50)
    
    for config_name, config_results in results.items():
        print(f"\n📊 {config_name}:")
        for result in config_results:
            if result.arrival_rate in [0.5, 2.0, 5.0, 10.0]:  # Show key points
                status = "🟢" if result.mean_ttft < 0.5 else "🟡" if result.mean_ttft < 1.0 else "🔴"
                print(f"  {status} {result.arrival_rate:.1f} req/s: {result.mean_ttft:.2f}s TTFT "
                      f"(Decode util: {result.utilization_decode:.2f})")
    
    print(f"\n📁 Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
