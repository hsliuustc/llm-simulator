#!/usr/bin/env python3
"""Decode Queue Impact Analysis - Specialized study of decode queue effects on TTFT."""

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
class DecodeQueueResult:
    """Results from decode queue analysis."""
    scenario_name: str
    prefill_gpus: int
    decode_gpus: int
    decode_rate: float
    arrival_rate: float
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


class DecodeQueueAnalyzer:
    """Analyzer for decode queue impact on TTFT."""
    
    def __init__(self, sim_seconds: float = 600.0, warmup_seconds: float = 60.0):
        self.sim_seconds = sim_seconds
        self.warmup_seconds = warmup_seconds
        self.results: List[DecodeQueueResult] = []
    
    def run_decode_scenario(self, 
                          prefill_gpus: int = 2,
                          decode_gpus: int = 2,
                          decode_rate: float = 2000.0,
                          arrival_rate: float = 2.0,
                          scenario_name: str = "custom") -> DecodeQueueResult:
        """Run a specific decode queue scenario."""
        
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
        
        return DecodeQueueResult(
            scenario_name=scenario_name,
            prefill_gpus=prefill_gpus,
            decode_gpus=decode_gpus,
            decode_rate=decode_rate,
            arrival_rate=arrival_rate,
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
    
    def run_decode_node_comparison(self) -> List[DecodeQueueResult]:
        """Run comparison of different decode node configurations."""
        scenarios = [
            # Baseline: 2 prefill, 2 decode
            (2, 2, 2000.0, 2.0, "2_prefill_2_decode_baseline"),
            
            # Reduced decode nodes: 2 prefill, 1 decode
            (2, 1, 2000.0, 2.0, "2_prefill_1_decode"),
            
            # Increased decode nodes: 2 prefill, 4 decode
            (2, 4, 2000.0, 2.0, "2_prefill_4_decode"),
            
            # Slow decode rate: 2 prefill, 2 decode, slow rate
            (2, 2, 1000.0, 2.0, "2_prefill_2_decode_slow"),
            
            # High load: 2 prefill, 2 decode, high arrival
            (2, 2, 2000.0, 4.0, "2_prefill_2_decode_high_load"),
            
            # Balanced: 2 prefill, 2 decode, balanced rates
            (2, 2, 4000.0, 2.0, "2_prefill_2_decode_balanced"),
        ]
        
        results = []
        for prefill_gpus, decode_gpus, decode_rate, arrival_rate, name in scenarios:
            try:
                result = self.run_decode_scenario(
                    prefill_gpus=prefill_gpus,
                    decode_gpus=decode_gpus,
                    decode_rate=decode_rate,
                    arrival_rate=arrival_rate,
                    scenario_name=name
                )
                results.append(result)
                print(f"✅ Completed {name}: {result.mean_ttft:.2f}s TTFT")
            except Exception as e:
                print(f"❌ Failed {name}: {e}")
        
        self.results = results
        return results
    
    def plot_decode_impact_analysis(self, save_path: str = "decode_queue_impact.png"):
        """Create visualization of decode queue impact."""
        if not self.results:
            print("No results to plot. Run decode_node_comparison() first.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("Decode Queue Impact on TTFT - Node Configuration Analysis", fontsize=16)
        
        # 1. TTFT Comparison by Configuration
        ax1 = axes[0, 0]
        scenarios = [r.scenario_name for r in self.results]
        ttft_values = [r.mean_ttft for r in self.results]
        
        bars = ax1.bar(scenarios, ttft_values, color=['blue' if '2_decode' in s else 'red' for s in scenarios])
        ax1.set_xlabel("Configuration")
        ax1.set_ylabel("Mean TTFT (s)")
        ax1.set_title("TTFT by Decode Configuration")
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, ttft_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}s', ha='center', va='bottom', fontsize=8)
        
        # 2. Decode Utilization vs TTFT
        ax2 = axes[0, 1]
        decode_utils = [r.utilization_decode for r in self.results]
        ax2.scatter(decode_utils, ttft_values, s=100, alpha=0.7)
        ax2.set_xlabel("Decode Utilization")
        ax2.set_ylabel("Mean TTFT (s)")
        ax2.set_title("TTFT vs Decode Utilization")
        ax2.grid(True, alpha=0.3)
        
        # Add labels for points
        for i, (util, ttft, name) in enumerate(zip(decode_utils, ttft_values, scenarios)):
            ax2.annotate(name.split('_')[-1], (util, ttft), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 3. Queue Wait Times Comparison
        ax3 = axes[0, 2]
        prefill_wait = [r.queue_wait_time_prefill for r in self.results]
        decode_wait = [r.queue_wait_time_decode for r in self.results]
        
        x = np.arange(len(scenarios))
        width = 0.35
        
        ax3.bar(x - width/2, prefill_wait, width, label='Prefill Queue', alpha=0.8)
        ax3.bar(x + width/2, decode_wait, width, label='Decode Queue', alpha=0.8)
        
        ax3.set_xlabel("Configuration")
        ax3.set_ylabel("Queue Wait Time (s)")
        ax3.set_title("Queue Wait Times by Configuration")
        ax3.set_xticks(x)
        ax3.set_xticklabels([s.split('_')[-1] for s in scenarios], rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Decode Nodes vs TTFT
        ax4 = axes[1, 0]
        decode_nodes = [r.decode_gpus for r in self.results]
        ax4.scatter(decode_nodes, ttft_values, s=100, alpha=0.7, color='green')
        ax4.set_xlabel("Number of Decode Nodes")
        ax4.set_ylabel("Mean TTFT (s)")
        ax4.set_title("TTFT vs Decode Nodes")
        ax4.grid(True, alpha=0.3)
        
        # 5. Decode Rate vs TTFT
        ax5 = axes[1, 1]
        decode_rates = [r.decode_rate for r in self.results]
        ax5.scatter(decode_rates, ttft_values, s=100, alpha=0.7, color='purple')
        ax5.set_xlabel("Decode Rate (tokens/s)")
        ax5.set_ylabel("Mean TTFT (s)")
        ax5.set_title("TTFT vs Decode Rate")
        ax5.grid(True, alpha=0.3)
        
        # 6. Bottleneck Analysis
        ax6 = axes[1, 2]
        prefill_utils = [r.utilization_prefill for r in self.results]
        decode_utils = [r.utilization_decode for r in self.results]
        
        ax6.scatter(prefill_utils, decode_utils, s=100, alpha=0.7, c=ttft_values, cmap='viridis')
        ax6.set_xlabel("Prefill Utilization")
        ax6.set_ylabel("Decode Utilization")
        ax6.set_title("Resource Utilization (color = TTFT)")
        ax6.grid(True, alpha=0.3)
        
        # Add colorbar
        scatter = ax6.scatter(prefill_utils, decode_utils, s=100, alpha=0.7, c=ttft_values, cmap='viridis')
        plt.colorbar(scatter, ax=ax6, label='TTFT (s)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved decode queue impact analysis to {save_path}")
    
    def generate_decode_report(self, save_path: str = "decode_queue_report.json"):
        """Generate detailed report of decode queue analysis."""
        report = {
            "analysis_parameters": {
                "simulation_seconds": self.sim_seconds,
                "warmup_seconds": self.warmup_seconds,
                "total_scenarios": len(self.results)
            },
            "scenarios": [],
            "key_insights": [],
            "recommendations": []
        }
        
        # Add scenario results
        for result in self.results:
            scenario_data = {
                "name": result.scenario_name,
                "configuration": {
                    "prefill_gpus": result.prefill_gpus,
                    "decode_gpus": result.decode_gpus,
                    "decode_rate": result.decode_rate,
                    "arrival_rate": result.arrival_rate
                },
                "performance": {
                    "mean_ttft": result.mean_ttft,
                    "p50_ttft": result.p50_ttft,
                    "p90_ttft": result.p90_ttft,
                    "p99_ttft": result.p99_ttft
                },
                "queue_metrics": {
                    "prefill_wait": result.queue_wait_time_prefill,
                    "decode_wait": result.queue_wait_time_decode,
                    "prefill_service": result.service_time_prefill,
                    "decode_service": result.service_time_decode
                },
                "utilization": {
                    "prefill": result.utilization_prefill,
                    "decode": result.utilization_decode
                }
            }
            report["scenarios"].append(scenario_data)
        
        # Generate insights
        for result in self.results:
            if result.mean_ttft > 10.0:
                report["key_insights"].append(
                    f"High TTFT in {result.scenario_name}: {result.mean_ttft:.2f}s - decode bottleneck detected"
                )
            if result.utilization_decode > 0.9:
                report["key_insights"].append(
                    f"Decode bottleneck in {result.scenario_name}: {result.utilization_decode:.2f} utilization"
                )
            if result.queue_wait_time_decode > result.queue_wait_time_prefill * 2:
                report["key_insights"].append(
                    f"Decode queue dominates in {result.scenario_name}: {result.queue_wait_time_decode:.2f}s vs {result.queue_wait_time_prefill:.2f}s"
                )
        
        # Generate recommendations
        best_scenario = min(self.results, key=lambda x: x.mean_ttft)
        report["recommendations"].append(
            f"Best configuration: {best_scenario.scenario_name} with {best_scenario.mean_ttft:.2f}s TTFT"
        )
        
        decode_bottlenecks = [r for r in self.results if r.utilization_decode > 0.8]
        if decode_bottlenecks:
            report["recommendations"].append(
                f"Consider increasing decode capacity for {len(decode_bottlenecks)} scenarios"
            )
        
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Saved decode queue report to {save_path}")
        return report


def main():
    """Main function for decode queue analysis."""
    parser = argparse.ArgumentParser(description="Decode Queue Impact Analysis")
    parser.add_argument("--sim-seconds", type=float, default=300.0, help="Simulation duration")
    parser.add_argument("--warmup-seconds", type=float, default=30.0, help="Warmup period")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory")
    
    args = parser.parse_args()
    
    analyzer = DecodeQueueAnalyzer(sim_seconds=args.sim_seconds, warmup_seconds=args.warmup_seconds)
    
    print("🚀 Starting decode queue impact analysis...")
    results = analyzer.run_decode_node_comparison()
    
    # Generate outputs
    analyzer.plot_decode_impact_analysis(f"{args.output_dir}/decode_queue_impact.png")
    analyzer.generate_decode_report(f"{args.output_dir}/decode_queue_report.json")
    
    print("\n🎯 Decode Queue Impact Analysis Summary:")
    print("=" * 50)
    for result in results:
        status = "🟢" if result.mean_ttft < 0.5 else "🟡" if result.mean_ttft < 1.0 else "🔴"
        print(f"{status} {result.scenario_name}: {result.mean_ttft:.2f}s TTFT "
              f"(Decode: {result.decode_gpus} nodes, {result.decode_rate} tokens/s)")
    
    print("\n🔍 Key Insights:")
    decode_bottlenecks = [r for r in results if r.utilization_decode > 0.8]
    if decode_bottlenecks:
        print("  Decode bottlenecks detected:")
        for result in decode_bottlenecks:
            print(f"    - {result.scenario_name}: {result.utilization_decode:.2f} utilization")
    
    print(f"\n📁 Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
