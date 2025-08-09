#!/usr/bin/env python3
"""Queue Impact Study CLI - Easy-to-use interface for queue process impact analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..analysis.queue_impact import QueueImpactAnalyzer
from ..utils.scenarios import (
    LowLoadFCFS, MediumLoadFCFS, HighLoadFCFS,
    SlowPrefillFCFS, SlowDecodeFCFS, BalancedFCFS,
    MonolithicFCFS, QueueSaturationStudy, VariableLoadFCFS
)


def main():
    """Main CLI function for queue impact studies."""
    parser = argparse.ArgumentParser(
        description="Queue Process Impact Study on TTFT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run comprehensive study with all scenarios
  python -m src.cli.queue_study --comprehensive

  # Run specific scenario
  python -m src.cli.queue_study --scenario low_load

  # Run load sweep for a scenario
  python -m src.cli.queue_study --scenario medium_load --load-sweep --rates 0.5,1,2,3,4

  # Run with custom parameters
  python -m src.cli.queue_study --scenario high_load --sim-seconds 1200 --warmup-seconds 120

Available scenarios:
  - low_load: Low load baseline (0.5 req/s)
  - medium_load: Medium load (2.0 req/s)
  - high_load: High load (4.0 req/s)
  - slow_prefill: Slow prefill processing
  - slow_decode: Slow decode processing
  - balanced: Balanced processing times
  - monolithic: Monolithic architecture comparison
  - saturation: Queue saturation study (6.0 req/s)
  - variable: Variable load with high variance
        """
    )
    
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Run comprehensive study with all scenarios")
    parser.add_argument("--scenario", type=str, choices=[
        "low_load", "medium_load", "high_load", "slow_prefill", 
        "slow_decode", "balanced", "monolithic", "saturation", "variable"
    ], help="Run specific scenario")
    parser.add_argument("--load-sweep", action="store_true",
                       help="Run load sweep analysis for the specified scenario")
    parser.add_argument("--rates", type=str, default="0.5,1,2,3,4,5",
                       help="Arrival rates for load sweep (comma-separated)")
    parser.add_argument("--sim-seconds", type=float, default=600.0,
                       help="Simulation duration in seconds")
    parser.add_argument("--warmup-seconds", type=float, default=60.0,
                       help="Warmup period in seconds")
    parser.add_argument("--output-dir", type=str, default=".",
                       help="Output directory for results")
    parser.add_argument("--no-plots", action="store_true",
                       help="Skip generating plots")
    parser.add_argument("--no-report", action="store_true",
                       help="Skip generating JSON report")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.comprehensive and not args.scenario:
        parser.error("Must specify either --comprehensive or --scenario")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize analyzer
    analyzer = QueueImpactAnalyzer(
        sim_seconds=args.sim_seconds,
        warmup_seconds=args.warmup_seconds
    )
    
    # Scenario mapping
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
    
    try:
        if args.comprehensive:
            print("🚀 Starting comprehensive queue impact study...")
            print("This will run all scenarios and may take several minutes.")
            results = analyzer.run_comprehensive_study()
            print(f"✅ Completed {len(results)} scenarios")
            
        elif args.scenario:
            scenario_class = scenario_map[args.scenario]
            
            if args.load_sweep:
                rates = [float(x.strip()) for x in args.rates.split(",")]
                print(f"🔄 Running load sweep for {args.scenario} with rates: {rates}")
                results = analyzer.run_load_sweep(scenario_class, rates)
                print(f"✅ Completed load sweep with {len(results)} data points")
            else:
                print(f"🎯 Running scenario: {args.scenario}")
                result = analyzer.run_scenario(scenario_class)
                results = [result]
                print(f"✅ Completed scenario: {args.scenario}")
        
        # Generate outputs
        if not args.no_plots:
            plot_path = output_dir / "queue_impact_analysis.png"
            analyzer.results = results
            analyzer.plot_queue_impact_analysis(str(plot_path))
        
        if not args.no_report:
            report_path = output_dir / "queue_impact_report.json"
            analyzer.results = results
            analyzer.generate_report(str(report_path))
        
        # Print summary
        print("\n🎯 Queue Impact Study Summary:")
        print("=" * 50)
        for result in results:
            status = "🟢" if result.mean_ttft < 0.5 else "🟡" if result.mean_ttft < 1.0 else "🔴"
            print(f"{status} {result.scenario_name}: {result.mean_ttft:.2f}s TTFT "
                  f"(P50: {result.p50_ttft:.2f}s, P99: {result.p99_ttft:.2f}s)")
        
        # Key insights
        print("\n🔍 Key Insights:")
        high_ttft_scenarios = [r for r in results if r.mean_ttft > 1.0]
        if high_ttft_scenarios:
            print("  High TTFT scenarios (queueing impact):")
            for result in high_ttft_scenarios:
                print(f"    - {result.scenario_name}: {result.mean_ttft:.2f}s")
        
        bottleneck_scenarios = [r for r in results if r.utilization_prefill > 0.9 or r.utilization_decode > 0.9]
        if bottleneck_scenarios:
            print("  Bottleneck scenarios:")
            for result in bottleneck_scenarios:
                if result.utilization_prefill > 0.9:
                    print(f"    - {result.scenario_name}: Prefill bottleneck ({result.utilization_prefill:.2f})")
                if result.utilization_decode > 0.9:
                    print(f"    - {result.scenario_name}: Decode bottleneck ({result.utilization_decode:.2f})")
        
        print(f"\n📁 Results saved to: {output_dir.absolute()}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Study interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during study: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
