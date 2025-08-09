Theory
======

This section provides the theoretical background for Time-To-First-Token (TTFT) analysis in LLM serving systems.

TTFT in Disaggregated Prefill/Decode Serving
--------------------------------------------

What is TTFT?
~~~~~~~~~~~~

TTFT is the latency from request arrival until the first output token is emitted. In the disaggregated setting, a request passes two resource queues before TTFT:

1. Prefill queue/pool → prefill compute (processes all prompt tokens)
2. Decode queue/pool → first decode-step (emits first token)

Formally, for a request i arriving at time t_i:

.. math::

    \mathrm{TTFT}_i = (W^p_i + S^p_i) + (W^d_i + S^{d,1}_i)

Where:

- :math:`W^p_i`: wait time in prefill queue
- :math:`S^p_i = \frac{\text{prompt\_tokens}_i}{r_p}`: prefill service time (r_p = prefill tokens/sec per GPU)
- :math:`W^d_i`: wait time in decode queue
- :math:`S^{d,1}_i = \frac{1}{r_d}`: first-token decode time (r_d = decode tokens/sec per GPU)

After the first token, the request continues decoding remaining tokens on the decode pool, but that does not affect TTFT.

Resource Model and Capacity
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prefill and decode are separate GPU pools:

- Prefill pool: G_p GPUs; prefill rate r_p tokens/s per GPU
- Decode pool: G_d GPUs; decode rate r_d tokens/s per GPU

Service times:

- Prefill per request: :math:`S^p = \frac{\text{prompt\_tokens}}{r_p}`
- First decode step: :math:`S^{d,1} = \frac{1}{r_d}`
- Remaining decode (post-TTFT): :math:`S^{d,\text{rest}} = \frac{\max(\text{output\_tokens}-1,0)}{r_d}`

Effective throughput is limited by the bottleneck stage (usually decode due to lower r_d and ongoing occupancy by remaining tokens).

Queueing Intuition
~~~~~~~~~~~~~~~~~~

As arrival rate λ approaches the capacity of either pool, its waiting time :math:`W` grows rapidly (utilization ρ→1), causing TTFT to blow up.

Disaggregation introduces two queues, so TTFT includes two waiting components. The earliest saturated pool dictates when TTFT starts increasing sharply.

Variance matters: heavy-tailed prompt/output token distributions increase queueing delay via variability terms.

Approximate expectation (for intuition, not a closed-form guarantee):

.. math::

    \mathbb{E}[\mathrm{TTFT}] \approx \mathbb{E}[W^p] + \mathbb{E}[S^p] + \mathbb{E}[W^d] + \mathbb{E}[S^{d,1}]

With :math:`\mathbb{E}[S^p] = \mathbb{E}[\text{prompt\_tokens}] / r_p` and :math:`\mathbb{E}[S^{d,1}] = 1 / r_d`.

Studying TTFT with the Simulator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Core knobs (YAML or CLI):

- Arrival rate (λ): ``arrival.rate_per_s``
- Prefill pool: ``cluster_disagg.prefill_gpus``, ``prefill_tokens_per_s``
- Decode pool: ``cluster_disagg.decode_gpus``, ``decode_tokens_per_s``
- Token distributions: ``prompt_tokens``, ``output_tokens`` with modes ``log``, ``real_mean_std``, ``p50_p90``

Outputs include: ``mean_ttft_s``, ``p50_ttft_s``, ``p90_ttft_s``, ``p99_ttft_s``, ``utilization_prefill``, ``utilization_decode``, ``throughput_rps``.

Run examples:

.. code-block:: bash

    # Single run in disaggregated mode
    python -m src.cli.run simulate --mode disagg --sim-seconds 600 --warmup-seconds 60

    # Arrival-rate sweep (P50/P90/P99 vs λ, both modes)
    python -m src.analysis.sweep --rates 0.5,1,2,3,4,5 --sim-seconds 600 --warmup-seconds 60

    # Prefill sensitivity (P50 vs λ across different prefill speeds)
    python -m src.analysis.sweep_prefill --rates 1,2,3,4 --prefill 4000,8000,12000,16000 --mode disagg --sim-seconds 600 --warmup-seconds 60

Interpreting Results
~~~~~~~~~~~~~~~~~~~

TTFT vs λ: Curves rise slowly in low load; once decode or prefill pool nears saturation, TTFT increases sharply.

Prefill sensitivity: Higher ``prefill_tokens_per_s`` reduces :math:`S^p` and TTFT, shifting the knee to higher λ; effect is strongest when prefill is close to bottleneck.

Utilization: When ``utilization_decode`` ≈ 1.0, decode pool is bottleneck; when ``utilization_prefill`` ≈ 1.0, prefill is bottleneck.

Tuning Levers for Lower TTFT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Decode-side improvements (often first to saturate):

- Increase ``decode_gpus``
- Raise ``decode_tokens_per_s``
- Reserve decode capacity for first tokens
- Prioritize first-token work

Prefill-side improvements:

- Increase ``prefill_gpus``
- Raise ``prefill_tokens_per_s``
- Reduce prompt length (capping, retrieval trimming)

Workload shaping:

- Rate limiting/admission control
- Reduce variance (batching carefully, prompt normalization) to mitigate queueing tails

Practical Notes
~~~~~~~~~~~~~~~

Warmup handling: Metrics filter by event time; choose a warmup long enough to reach steady state.

Distribution specification: Prefer ``real_mean_std`` or ``p50_p90`` when matching real traces; CLI echoes both log- and real-space parameters for verification.

Throughput saturation: As λ exceeds bottleneck capacity, throughput flat-lines while TTFT diverges; use load shedding to avoid unstable regimes.

Limitations and Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Simplified token-level service model; no step-level batching/KV-cache contention yet.

No network or model-switch overheads.

Extensions: implement batched decode steps, prompt-aware scheduling, KV memory limits, heterogeneous GPUs, and trace-driven arrivals.

Mathematical Framework
----------------------

Queueing Theory Basics
~~~~~~~~~~~~~~~~~~~~~~

The simulator models LLM serving as a queueing system with:

1. **Arrival Process**: Poisson arrivals with rate λ (requests/second)
2. **Service Process**: Deterministic service times based on token counts and processing rates
3. **Resource Constraints**: Limited GPU pools for prefill and decode stages

For a single-server queue with Poisson arrivals and general service times (M/G/1):

.. math::

    W = \frac{\lambda \sigma^2 + \rho^2}{2(1-\rho)}

Where:

- :math:`W`: average waiting time
- :math:`\lambda`: arrival rate
- :math:`\sigma^2`: variance of service time
- :math:`\rho`: utilization (:math:`\lambda \cdot \text{mean service time}`)

Token Distribution Modeling
~~~~~~~~~~~~~~~~~~~~~~~~~~

The simulator uses lognormal distributions for token counts, which are common in natural language processing:

.. math::

    f(x) = \frac{1}{x \sigma \sqrt{2\pi}} \exp\left(-\frac{(\ln x - \mu)^2}{2\sigma^2}\right)

Parameters can be specified in multiple ways:

1. **Log-space**: Direct specification of :math:`\mu` and :math:`\sigma`
2. **Real-space mean/std**: Converted to log-space using:

   .. math::

       \sigma^2 = \ln(1 + \frac{\text{std}^2}{\text{mean}^2})
       \mu = \ln(\text{mean}) - \frac{\sigma^2}{2}

3. **Percentiles**: Converted using normal quantiles:

   .. math::

       \mu = \ln(P_{50})
       \sigma = \frac{\ln(P_{90}) - \ln(P_{50})}{z_{0.9}}

Performance Metrics
-------------------

TTFT Percentiles
~~~~~~~~~~~~~~~~

The simulator computes multiple percentiles of TTFT:

- **P50 (Median)**: 50th percentile - typical performance
- **P90**: 90th percentile - performance under load
- **P99**: 99th percentile - worst-case performance

These are computed using numpy's percentile function on the filtered TTFT samples (excluding warmup period).

Throughput Analysis
~~~~~~~~~~~~~~~~~~~

Throughput is measured as completed requests per second:

.. math::

    \text{Throughput} = \frac{\text{completed\_requests}}{\text{elapsed\_time}}

Under steady-state conditions, throughput should approach the arrival rate λ, but may be limited by resource constraints.

GPU Utilization
~~~~~~~~~~~~~~~

GPU utilization measures the fraction of time GPUs are busy:

.. math::

    \text{Utilization} = \frac{\text{total\_gpu\_time}}{\text{num\_gpus} \times \text{elapsed\_time}}

For disaggregated systems, utilization is computed separately for prefill and decode pools.

Bottleneck Analysis
~~~~~~~~~~~~~~~~~~~

The simulator helps identify bottlenecks by monitoring:

1. **Queue lengths**: Average waiting times in prefill and decode queues
2. **Utilization**: GPU utilization in each pool
3. **Service times**: Average processing times for each stage

When utilization approaches 1.0, that pool becomes the bottleneck.

Simulation Methodology
----------------------

Discrete Event Simulation
~~~~~~~~~~~~~~~~~~~~~~~~

The simulator uses SimPy, a discrete-event simulation framework. Key events include:

1. **Request Arrival**: Generated according to Poisson process
2. **Resource Acquisition**: Request waits for available GPU
3. **Service Completion**: Request finishes processing stage
4. **Resource Release**: GPU becomes available for next request

Warmup Period
~~~~~~~~~~~~~

To ensure steady-state analysis, the simulator excludes an initial warmup period from metrics computation. This helps avoid transient effects from:

- Empty initial queues
- Cold-start effects
- System initialization

The warmup period should be long enough for the system to reach steady state, typically 10-20% of total simulation time.

Statistical Validity
~~~~~~~~~~~~~~~~~~~

The simulator provides:

- **Sample size**: Number of completed requests used for statistics
- **Confidence intervals**: Can be computed from raw TTFT samples
- **Reproducibility**: Deterministic results with fixed random seed

For reliable results, aim for at least 1000 completed requests per simulation.

Validation and Verification
---------------------------

The simulator includes several validation mechanisms:

1. **Parameter verification**: CLI outputs resolved distribution parameters
2. **Consistency checks**: Ensures configuration parameters are valid
3. **Performance bounds**: Results should be physically reasonable

Expected behaviors:

- TTFT increases with arrival rate
- TTFT decreases with more GPUs
- Utilization increases with load
- Throughput saturates at bottleneck capacity

Limitations
-----------

Current Limitations
~~~~~~~~~~~~~~~~~~~

1. **Simplified service model**: No step-level batching or KV-cache contention
2. **No network overhead**: Assumes instant resource transfers
3. **Homogeneous resources**: All GPUs have same processing rates
4. **No admission control**: All requests are accepted
5. **No priority scheduling**: FIFO queue discipline

Future Extensions
~~~~~~~~~~~~~~~~~

1. **Batching support**: Model step-level batching and KV-cache management
2. **Heterogeneous resources**: Different GPU types and processing rates
3. **Network modeling**: Include transfer overheads between pools
4. **Advanced scheduling**: Priority queues, preemption, admission control
5. **Trace-driven workloads**: Support for real arrival patterns
6. **Power modeling**: Energy consumption and thermal effects
