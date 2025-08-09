## TTFT in Disaggregated Prefill/Decode Serving

This document explains Time-To-First-Token (TTFT) under a disaggregated serving architecture where prefill and decode are handled by separate GPU pools, as in DistServe-style systems.

### What is TTFT?
- TTFT is the latency from request arrival until the first output token is emitted.
- In the disaggregated setting, a request passes two resource queues before TTFT:
  1) Prefill queue/pool → prefill compute (processes all prompt tokens)
  2) Decode queue/pool → first decode-step (emits first token)

Formally, for a request i arriving at time t_i:
\[ \mathrm{TTFT}_i = (W^p_i + S^p_i) + (W^d_i + S^{d,1}_i) \]
- \( W^p_i \): wait time in prefill queue
- \( S^p_i = \frac{\text{prompt\_tokens}_i}{r_p} \): prefill service time (r_p = prefill tokens/sec per GPU)
- \( W^d_i \): wait time in decode queue
- \( S^{d,1}_i = \frac{1}{r_d} \): first-token decode time (r_d = decode tokens/sec per GPU)

After the first token, the request continues decoding remaining tokens on the decode pool, but that does not affect TTFT.

### Resource model and capacity
- Prefill and decode are separate GPU pools:
  - Prefill pool: G_p GPUs; prefill rate r_p tokens/s per GPU
  - Decode pool: G_d GPUs; decode rate r_d tokens/s per GPU
- Service times:
  - Prefill per request: \( S^p = \frac{\text{prompt\_tokens}}{r_p} \)
  - First decode step: \( S^{d,1} = \frac{1}{r_d} \)
  - Remaining decode (post-TTFT): \( S^{d,\text{rest}} = \frac{\max(\text{output\_tokens}-1,0)}{r_d} \)
- Effective throughput is limited by the bottleneck stage (usually decode due to lower r_d and ongoing occupancy by remaining tokens).

### Queueing intuition
- As arrival rate λ approaches the capacity of either pool, its waiting time \( W \) grows rapidly (utilization ρ→1), causing TTFT to blow up.
- Disaggregation introduces two queues, so TTFT includes two waiting components. The earliest saturated pool dictates when TTFT starts increasing sharply.
- Variance matters: heavy-tailed prompt/output token distributions increase queueing delay via variability terms.

Approximate expectation (for intuition, not a closed-form guarantee):
\[ \mathbb{E}[\mathrm{TTFT}] \approx \mathbb{E}[W^p] + \mathbb{E}[S^p] + \mathbb{E}[W^d] + \mathbb{E}[S^{d,1}] \]
with \( \mathbb{E}[S^p] = \mathbb{E}[\text{prompt\_tokens}] / r_p \) and \( \mathbb{E}[S^{d,1}] = 1 / r_d \).

### Studying TTFT with this simulator
- Core knobs (YAML or CLI):
  - Arrival rate (λ): `arrival.rate_per_s`
  - Prefill pool: `cluster_disagg.prefill_gpus`, `prefill_tokens_per_s`
  - Decode pool: `cluster_disagg.decode_gpus`, `decode_tokens_per_s`
  - Token distributions: `prompt_tokens`, `output_tokens` with modes `log`, `real_mean_std`, `p50_p90`
- Outputs include: `mean_ttft_s`, `p50_ttft_s`, `p90_ttft_s`, `p99_ttft_s`, `utilization_prefill`, `utilization_decode`, `throughput_rps`.

Run examples
```
# Single run in disaggregated mode
python3 -m ttft_sim.run simulate --mode disagg --sim-seconds 600 --warmup-seconds 60

# Arrival-rate sweep (P50/P90/P99 vs λ, both modes)
python3 -m ttft_sim.sweep --rates 0.5,1,2,3,4,5 --sim-seconds 600 --warmup-seconds 60
# Produces: fig_ttft_vs_rate.png

# Prefill sensitivity (P50 vs λ across different prefill speeds)
python3 -m ttft_sim.sweep_prefill --rates 1,2,3,4 \
  --prefill 4000,8000,12000,16000 --mode disagg --sim-seconds 600 --warmup-seconds 60
# Produces: fig_ttft_vs_rate_prefill_disagg.png
```

### Interpreting results
- TTFT vs λ: Curves rise slowly in low load; once decode or prefill pool nears saturation, TTFT increases sharply.
- Prefill sensitivity: Higher `prefill_tokens_per_s` reduces \( S^p \) and TTFT, shifting the knee to higher λ; effect is strongest when prefill is close to bottleneck.
- Utilization: When `utilization_decode` ≈ 1.0, decode pool is bottleneck; when `utilization_prefill` ≈ 1.0, prefill is bottleneck.

### Tuning levers for lower TTFT
- Decode-side improvements (often first to saturate): increase `decode_gpus`, raise `decode_tokens_per_s`, reserve decode capacity for first tokens, prioritize first-token work.
- Prefill-side improvements: increase `prefill_gpus`, raise `prefill_tokens_per_s`, reduce prompt length (capping, retrieval trimming).
- Workload shaping: rate limiting/admission control; reduce variance (batching carefully, prompt normalization) to mitigate queueing tails.

### Practical notes
- Warmup handling: Metrics filter by event time; choose a warmup long enough to reach steady state.
- Distribution specification: Prefer `real_mean_std` or `p50_p90` when matching real traces; CLI echoes both log- and real-space parameters for verification.
- Throughput saturation: As λ exceeds bottleneck capacity, throughput flat-lines while TTFT diverges; use load shedding to avoid unstable regimes.

### Limitations and extensions
- Simplified token-level service model; no step-level batching/KV-cache contention yet.
- No network or model-switch overheads.
- Extensions: implement batched decode steps, prompt-aware scheduling, KV memory limits, heterogeneous GPUs, and trace-driven arrivals.

This framework provides a clear way to reason about TTFT in disaggregated serving: decompose waiting and service at prefill/decode pools, identify the bottleneck, and quantify the impact of capacity and workload changes on TTFT curves.
