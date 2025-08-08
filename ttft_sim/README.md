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
python ttft_sim/run.py --help
```

## Example

Run a 600-second simulation with default parameters and disaggregated architecture:

```bash
python ttft_sim/run.py simulate --mode disagg --sim-seconds 600
```

Run monolithic for comparison:

```bash
python ttft_sim/run.py simulate --mode mono --sim-seconds 600
```

## Configuration

You can supply a YAML config to adjust workload and cluster parameters. See `ttft_sim/example_config.yaml` for a template.

```bash
python ttft_sim/run.py simulate --config ttft_sim/example_config.yaml
```

Key parameters:
- `arrival.rate_per_s`: Poisson arrivals per second
- `prompt_tokens`: lognormal distribution params for prompt length
- `output_tokens`: lognormal distribution params for output length
- `cluster`: number of GPUs and per-GPU token rates for prefill and decode
- `mode`: `mono` (monolithic) or `disagg` (prefill/decode disaggregated)

## Outputs

- Reports mean, median, and percentile TTFT
- Basic throughput and utilization estimates

## Notes

- This is a simplified model intended for comparative study. It does not simulate step-level batching/KV cache; extensions welcome.
- It follows the spirit of DistServe by separating prefill and decode pools in `disagg` mode.