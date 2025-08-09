#!/usr/bin/env python3
"""Queue Process Impact Study on TTFT - Comprehensive Analysis Tool."""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from ..core.config import SimConfig
from ..core.simulator import run_simulation
from ..utils.scenarios import (
    LowLoadFCFS, MediumLoadFCFS, HighLoadFCFS,
    SlowPrefillFCFS, SlowDecodeFCFS, BalancedFCFS,
    MonolithicFCFS, QueueSaturationStudy, VariableLoadFCFS
)


@dataclass
class QueueImpactResult:
    """Results from a queue impact study."""
    scenario_name: str
    arrival_rate: float
    mean_ttft: float
    p50_ttft: float
    p90_ttft: float
    p99_ttft: float
    throughput: float
    utilization_prefill: float = 0.0
    utilization_decode: float = 0.0
    utilization_gpu: float = 0.0
    queue_wait_time_prefill: float = 0.0
    queue_wait_time_decode: float = 0.0
    service_time_prefill: float = 0.0
    service_time_decode: float = 0.0


class QueueImpactAnalyzer:
    """Analyzer for queue process impact on TTFT."""
    
    def __init__(self, sim_seconds: float = 600.0, warmup_seconds: float = 60.0):
        self.sim_seconds = sim_seconds
        self.warmup_seconds = warmup_seconds
        self.results: List[QueueImpactResult] = []
    
    def run_scenario(self, scenario_class, **kwargs) -> QueueImpactResult:
        """Run a single scenario and return results."""
        cfg = SimConfig(sim_seconds=self.sim_seconds, warmup_seconds=self.warmup_seconds)
        scenario = scenario_class()
        cfg = scenario.apply(cfg)
        
        # Override with kwargs if provided
        for key, value in kwargs.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
            elif hasattr(cfg.arrival, key):
                setattr(cfg.arrival, key, value)
        
        # Build parameters for simulation
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
            mono_params=mono_params,
            disagg_params=disagg_params,
        )
        
        # Calculate queue wait times (approximate)
        if cfg.mode == "disagg":
            # Estimate queue wait times based on utilization and service times
            prefill_service_time = math.exp(cfg.prompt_tokens.mean + 0.5 * cfg.prompt_tokens.sigma**2) / cfg.cluster_disagg.prefill_tokens_per_s
            decode_service_time = 1.0 / cfg.cluster_disagg.decode_tokens_per_s
            
            # M/M/c queue approximation for wait time
            utilization_prefill = stats.get("utilization_prefill", 0.0)
            utilization_decode = stats.get("utilization_decode", 0.0)
            
            queue_wait_prefill = self._estimate_queue_wait_time(
                utilization_prefill, prefill_service_time, cfg.cluster_disagg.prefill_gpus
            )
            queue_wait_decode = self._estimate_queue_wait_time(
                utilization_decode, decode_service_time, cfg.cluster_disagg.decode_gpus
            )
        else:
            queue_wait_prefill = 0.0
            queue_wait_decode = 0.0
            prefill_service_time = 0.0
            decode_service_time = 0.0
        
        return QueueImpactResult(
            scenario_name=scenario.name,
            arrival_rate=cfg.arrival.rate_per_s,
            mean_ttft=stats["mean_ttft_s"],
            p50_ttft=stats["p50_ttft_s"],
            p90_ttft=stats["p90_ttft_s"],
            p99_ttft=stats["p99_ttft_s"],
            throughput=stats.get("throughput_rps", 0.0),
            utilization_prefill=stats.get("utilization_prefill", 0.0),
            utilization_decode=stats.get("utilization_decode", 0.0),
            utilization_gpu=stats.get("utilization_gpu", 0.0),
            queue_wait_time_prefill=queue_wait_prefill,
            queue_wait_time_decode=queue_wait_decode,
            service_time_prefill=prefill_service_time,
            service_time_decode=decode_service_time,
        )
    
    def _estimate_queue_wait_time(self, utilization: float, service_time: float, num_servers: int) -> float:
        """Estimate queue wait time using M/M/c queue approximation."""
        if utilization >= 1.0:
            return float('inf')  # Queue is saturated
        
        if num_servers == 1:
            # M/M/1 queue
            if utilization >= 1.0:
                return float('inf')
            return (utilization / (1 - utilization)) * service_time
        else:
            # M/M/c queue approximation
            if utilization >= num_servers:
                return float('inf')
            
            # Simplified approximation for M/M/c
            rho = utilization / num_servers
            if rho >= 1.0:
                return float('inf')
            
            # Approximate wait time using Erlang C formula approximation
            wait_time = (rho / (1 - rho)) * service_time / num_servers
            return max(0.0, wait_time)
    
    def run_load_sweep(self, scenario_class, rates: List[float]) -> List[QueueImpactResult]:
        """Run a scenario across different arrival rates."""
        results = []
        for rate in rates:
            result = self.run_scenario(scenario_class, rate_per_s=rate)
            results.append(result)
        return results
    
    def run_comprehensive_study(self) -> List[QueueImpactResult]:
        """Run comprehensive queue impact study with all scenarios."""
        scenarios = [
            (LowLoadFCFS, {}),
            (MediumLoadFCFS, {}),
            (HighLoadFCFS, {}),
            (SlowPrefillFCFS, {}),
            (SlowDecodeFCFS, {}),
            (BalancedFCFS, {}),
            (MonolithicFCFS, {}),
            (QueueSaturationStudy, {}),
            (VariableLoadFCFS, {}),
        ]
        
        results = []
        for scenario_class, kwargs in scenarios:
            try:
                result = self.run_scenario(scenario_class, **kwargs)
                results.append(result)
                print(f"✅ Completed {result.scenario_name}")
            except Exception as e:
                print(f"❌ Failed {scenario_class.__name__}: {e}")
        
        self.results = results
        return results
    
    def plot_queue_impact_analysis(self, save_path: str = "queue_impact_analysis.png"):
        """Create comprehensive visualization of queue impact analysis."""
        if not self.results:
            print("No results to plot. Run comprehensive_study() first.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("Queue Process Impact on TTFT - Comprehensive Analysis", fontsize=16)
        
        # 1. TTFT vs Arrival Rate (all scenarios)
        ax1 = axes[0, 0]
        for result in self.results:
            if "load" in result.scenario_name.lower():
                ax1.plot(result.arrival_rate, result.mean_ttft, 'o-', label=result.scenario_name)
        ax1.set_xlabel("Arrival Rate (req/s)")
        ax1.set_ylabel("Mean TTFT (s)")
        ax1.set_title("TTFT vs Arrival Rate")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. TTFT Percentiles Comparison
        ax2 = axes[0, 1]
        scenarios = [r.scenario_name for r in self.results]
        p50_values = [r.p50_ttft for r in self.results]
        p90_values = [r.p90_ttft for r in self.results]
        p99_values = [r.p99_ttft for r in self.results]
        
        x = np.arange(len(scenarios))
        width = 0.25
        
        ax2.bar(x - width, p50_values, width, label='P50', alpha=0.8)
        ax2.bar(x, p90_values, width, label='P90', alpha=0.8)
        ax2.bar(x + width, p99_values, width, label='P99', alpha=0.8)
        
        ax2.set_xlabel("Scenarios")
        ax2.set_ylabel("TTFT (s)")
        ax2.set_title("TTFT Percentiles by Scenario")
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Utilization Analysis
        ax3 = axes[0, 2]
        prefill_utils = [r.utilization_prefill for r in self.results if r.utilization_prefill > 0]
        decode_utils = [r.utilization_decode for r in self.results if r.utilization_decode > 0]
        gpu_utils = [r.utilization_gpu for r in self.results if r.utilization_gpu > 0]
        
        if prefill_utils:
            ax3.plot(range(len(prefill_utils)), prefill_utils, 'o-', label='Prefill', color='blue')
        if decode_utils:
            ax3.plot(range(len(decode_utils)), decode_utils, 's-', label='Decode', color='red')
        if gpu_utils:
            ax3.plot(range(len(gpu_utils)), gpu_utils, '^-', label='GPU (Mono)', color='green')
        
        ax3.set_xlabel("Scenario Index")
        ax3.set_ylabel("Utilization")
        ax3.set_title("Resource Utilization")
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Queue Wait Time Analysis
        ax4 = axes[1, 0]
        prefill_wait = [r.queue_wait_time_prefill for r in self.results]
        decode_wait = [r.queue_wait_time_decode for r in self.results]
        
        ax4.plot(range(len(prefill_wait)), prefill_wait, 'o-', label='Prefill Queue', color='blue')
        ax4.plot(range(len(decode_wait)), decode_wait, 's-', label='Decode Queue', color='red')
        
        ax4.set_xlabel("Scenario Index")
        ax4.set_ylabel("Queue Wait Time (s)")
        ax4.set_title("Queue Wait Times")
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. Service Time Analysis
        ax5 = axes[1, 1]
        prefill_service = [r.service_time_prefill for r in self.results]
        decode_service = [r.service_time_decode for r in self.results]
        
        ax5.plot(range(len(prefill_service)), prefill_service, 'o-', label='Prefill Service', color='blue')
        ax5.plot(range(len(decode_service)), decode_service, 's-', label='Decode Service', color='red')
        
        ax5.set_xlabel("Scenario Index")
        ax5.set_ylabel("Service Time (s)")
        ax5.set_title("Service Times")
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6. Throughput Analysis
        ax6 = axes[1, 2]
        throughputs = [r.throughput for r in self.results]
        arrival_rates = [r.arrival_rate for r in self.results]
        
        ax6.plot(arrival_rates, throughputs, 'o-', color='purple')
        ax6.plot([0, max(arrival_rates)], [0, max(arrival_rates)], '--', color='gray', alpha=0.5, label='Ideal')
        
        ax6.set_xlabel("Arrival Rate (req/s)")
        ax6.set_ylabel("Throughput (req/s)")
        ax6.set_title("Throughput vs Arrival Rate")
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved queue impact analysis to {save_path}")
    
    def generate_report(self, save_path: str = "queue_impact_report.json"):
        """Generate a comprehensive report of the queue impact study."""
        report = {
            "study_parameters": {
                "simulation_seconds": self.sim_seconds,
                "warmup_seconds": self.warmup_seconds,
                "total_scenarios": len(self.results)
            },
            "scenarios": [],
            "summary_statistics": {},
            "key_insights": []
        }
        
        # Add scenario results
        for result in self.results:
            scenario_data = {
                "name": result.scenario_name,
                "arrival_rate": result.arrival_rate,
                "ttft_metrics": {
                    "mean": result.mean_ttft,
                    "p50": result.p50_ttft,
                    "p90": result.p90_ttft,
                    "p99": result.p99_ttft
                },
                "performance_metrics": {
                    "throughput": result.throughput,
                    "utilization_prefill": result.utilization_prefill,
                    "utilization_decode": result.utilization_decode,
                    "utilization_gpu": result.utilization_gpu
                },
                "queue_metrics": {
                    "wait_time_prefill": result.queue_wait_time_prefill,
                    "wait_time_decode": result.queue_wait_time_decode,
                    "service_time_prefill": result.service_time_prefill,
                    "service_time_decode": result.service_time_decode
                }
            }
            report["scenarios"].append(scenario_data)
        
        # Calculate summary statistics
        ttft_values = [r.mean_ttft for r in self.results]
        report["summary_statistics"] = {
            "mean_ttft_range": (min(ttft_values), max(ttft_values)),
            "ttft_variance": np.var(ttft_values),
            "scenarios_with_high_queueing": len([r for r in self.results if r.mean_ttft > 1.0]),
            "scenarios_with_low_queueing": len([r for r in self.results if r.mean_ttft < 0.5])
        }
        
        # Generate key insights
        insights = []
        for result in self.results:
            if result.mean_ttft > 2.0:
                insights.append(f"High queueing impact in {result.scenario_name}: {result.mean_ttft:.2f}s TTFT")
            if result.utilization_prefill > 0.9:
                insights.append(f"Prefill bottleneck in {result.scenario_name}: {result.utilization_prefill:.2f} utilization")
            if result.utilization_decode > 0.9:
                insights.append(f"Decode bottleneck in {result.scenario_name}: {result.utilization_decode:.2f} utilization")
        
        report["key_insights"] = insights
        
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Saved comprehensive report to {save_path}")
        return report


def main():
    """Main function for queue impact analysis."""
    parser = argparse.ArgumentParser(description="Queue Process Impact Study on TTFT")
    parser.add_argument("--sim-seconds", type=float, default=600.0, help="Simulation duration")
    parser.add_argument("--warmup-seconds", type=float, default=60.0, help="Warmup period")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory")
    parser.add_argument("--scenario", type=str, help="Run specific scenario")
    parser.add_argument("--load-sweep", action="store_true", help="Run load sweep analysis")
    parser.add_argument("--rates", type=str, default="0.5,1,2,3,4,5", help="Arrival rates for load sweep")
    
    args = parser.parse_args()
    
    analyzer = QueueImpactAnalyzer(sim_seconds=args.sim_seconds, warmup_seconds=args.warmup_seconds)
    
    if args.scenario:
        # Run specific scenario
        scenario_map = {
            "low_load": LowLoadFCFS,
            "medium_load": MediumLoadFCFS,
            "high_load": HighLoadFCFS,
            "slow_prefill": SlowPrefillFCFS,
            "slow_decode": SlowDecodeFCFS,
            "balanced": BalancedFCFS,
            "monolithic": MonolithicFCFS,
            "saturation": QueueSaturationStudy,
            "variable": VariableLoadFCFS,
        }
        
        if args.scenario not in scenario_map:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available scenarios: {list(scenario_map.keys())}")
            return
        
        scenario_class = scenario_map[args.scenario]
        
        if args.load_sweep:
            rates = [float(x) for x in args.rates.split(",")]
            results = analyzer.run_load_sweep(scenario_class, rates)
            print(f"Completed load sweep for {args.scenario}")
        else:
            result = analyzer.run_scenario(scenario_class)
            results = [result]
            print(f"Completed single scenario: {args.scenario}")
    else:
        # Run comprehensive study
        print("🚀 Starting comprehensive queue impact study...")
        results = analyzer.run_comprehensive_study()
        print(f"✅ Completed {len(results)} scenarios")
    
    # Generate visualizations and report
    analyzer.results = results
    analyzer.plot_queue_impact_analysis(f"{args.output_dir}/queue_impact_analysis.png")
    analyzer.generate_report(f"{args.output_dir}/queue_impact_report.json")
    
    print("\n🎯 Queue Impact Study Complete!")
    print("Key findings:")
    for result in results:
        if result.mean_ttft > 1.0:
            print(f"  - {result.scenario_name}: High TTFT ({result.mean_ttft:.2f}s) due to queueing")
        elif result.mean_ttft < 0.3:
            print(f"  - {result.scenario_name}: Low TTFT ({result.mean_ttft:.2f}s) - minimal queueing")


if __name__ == "__main__":
    main()
