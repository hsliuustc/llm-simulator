# TTFT Simulator (Monolithic vs Disaggregated Prefill/Decode)

This is a simple, compact simulator (<2k LOC) to study Time-To-First-Token (TTFT) for LLM serving under two architectures:

- Monolithic: each request holds a GPU from start to finish (prefill + full decode)
- Disaggregated: prefill and decode stages use separate GPU pools (as in DistServe) and requests move between them

The simulator is based on a discrete event simulation using SimPy.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ttft_sim/requirements.txt
python -m ttft_sim.run --help
```

## Example

Run a 600-second simulation with default parameters and disaggregated architecture:

```bash
python -m ttft_sim.run simulate --mode disagg --sim-seconds 600
```

Run monolithic for comparison:

```bash
python -m ttft_sim.run simulate --mode mono --sim-seconds 600
```

## Configuration

You can supply a YAML config to adjust workload and cluster parameters. See `ttft_sim/example_config.yaml` for a template.

```bash
python -m ttft_sim.run simulate --config ttft_sim/example_config.yaml
```

Key parameters:
- `arrival.rate_per_s`: Poisson arrivals per second
- `prompt_tokens` and `output_tokens` token distribution (lognormal):
  - Backward compatible (log-space):
    ```yaml
    prompt_tokens:
      mode: log
      mean: 6.0   # log-space mu
      sigma: 0.9  # log-space sigma
      min_value: 8
    ```
  - Real-space mean/std:
    ```yaml
    prompt_tokens:
      mode: real_mean_std
      mean: 1024   # tokens
      std: 512
      min_value: 8
    ```
  - Real-space percentiles:
    ```yaml
    prompt_tokens:
      mode: p50_p90
      p50: 128
      p90: 512
      min_value: 8
    ```
- `cluster`: number of GPUs and per-GPU token rates for prefill and decode
- `mode`: `mono` (monolithic) or `disagg` (prefill/decode disaggregated)

### Verify effective parameters
To ensure YAML numbers match your expectations, the CLI prints resolved distributions in both log-space and real-space:

```bash
python -m ttft_sim.run simulate --config ttft_sim/example_config.yaml
```

Look for `prompt_tokens_log`, `prompt_tokens_real`, `output_tokens_log`, and `output_tokens_real` in the JSON output.

## Outputs

- Reports mean, median, and percentile TTFT
- Basic throughput and utilization estimates

## Notes

- This is a simplified model intended for comparative study. It does not simulate step-level batching/KV cache; extensions welcome.
- It follows the spirit of DistServe by separating prefill and decode pools in `disagg` mode.