# TTFT Simulator Summary

## Overview

This is a compact (<600 LOC) discrete event simulator for studying Time-To-First-Token (TTFT) performance under two LLM serving architectures:

1. **Monolithic**: Each request holds a GPU from prefill through full decode
2. **Disaggregated**: Prefill and decode stages use separate GPU pools (like DistServe)

## Architecture

### Core Components

- **`simulator.py`** (183 LOC): Main simulation engine using SimPy
  - `MonolithicSimulator`: Single GPU pool for entire request lifecycle
  - `DisaggregatedSimulator`: Separate pools for prefill and decode stages
  - `Metrics`: TTFT tracking with proper warmup filtering

- **`config.py`** (85 LOC): Configuration management with dataclasses
  - Workload parameters (arrival rate, token distributions)
  - Cluster parameters (GPU counts, token rates)
  - YAML config loading

- **`run.py`** (65 LOC): CLI interface using Click
  - Command-line simulation execution
  - Config overrides and YAML loading

- **`compare.py`** (45 LOC): Automated comparison script
- **`visualize.py`** (70 LOC): Optional matplotlib visualization

### Key Features

- **Realistic Workload**: Poisson arrivals, lognormal token distributions
- **Proper Warmup**: Event-time based filtering (not TTFT-value based)
- **Flexible Config**: YAML configs, CLI overrides, scenario presets
- **Comprehensive Metrics**: Mean, P50, P90, P99 TTFT statistics

## Simulation Results

### Default Configuration
- Arrival rate: 2.0 req/s
- Prompt tokens: lognormal(6.0, 0.9) with min=8
- Output tokens: lognormal(6.0, 1.1) with min=16
- Cluster: 4 GPUs total (2+2 for disaggregated)
- Token rates: 8000 prefill, 2000 decode tokens/s

### Sample Results (300s simulation)
```
Monolithic:
  Mean TTFT: 0.088s
  P50 TTFT: 0.055s  
  P90 TTFT: 0.203s
  P99 TTFT: 0.552s

Disaggregated:
  Mean TTFT: 0.122s (+37.7%)
  P50 TTFT: 0.066s (+20.5%)
  P90 TTFT: 0.281s (+38.1%)
  P99 TTFT: 0.829s (+50.2%)
```

## Key Insights

1. **Disaggregated is slower**: Expected due to double queueing (prefill + decode pools)
2. **Tail latency impact**: P99 degradation is more severe than mean
3. **Resource efficiency**: Disaggregated allows better resource utilization but at TTFT cost
4. **Configurability**: Easy to explore different workload/cluster scenarios

## Usage Examples

```bash
# Quick comparison
python ttft_sim/compare.py

# Custom simulation
python -m ttft_sim.run simulate --mode disagg --sim-seconds 600

# With config file
python -m ttft_sim.run simulate --config ttft_sim/example_config.yaml

# Visualization (requires matplotlib)
python ttft_sim/visualize.py
```

## Extensions

The simulator is designed for easy extension:
- Add more sophisticated batching logic
- Implement KV cache modeling
- Add different scheduling policies
- Support for heterogeneous workloads
- Integration with real trace data

## Limitations

- Simplified token-level modeling (no step-level batching)
- No memory constraints or model loading overhead
- Assumes perfect load balancing
- No network latency or communication overhead

This simulator provides a solid foundation for studying TTFT trade-offs in LLM serving architectures, following the spirit of DistServe's prefill/decode disaggregation approach. 