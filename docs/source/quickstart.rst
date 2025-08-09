Quick Start Guide
=================

This guide will help you get started with the LLM Simulator quickly. You'll learn how to run your first simulation and understand the basic concepts.

Prerequisites
-------------

Before starting, make sure you have:

1. Installed the LLM Simulator (see :doc:`installation`)
2. Activated your virtual environment
3. Basic understanding of Python

Basic Concepts
--------------

The LLM Simulator models two main architectures:

* **Monolithic**: Each request holds a GPU from start to finish (prefill + full decode)
* **Disaggregated**: Prefill and decode stages use separate GPU pools (as in DistServe)

Key Metrics
~~~~~~~~~~~

* **TTFT (Time-To-First-Token)**: Time from request arrival until the first output token
* **Throughput**: Requests processed per second
* **GPU Utilization**: Percentage of GPU time used

Your First Simulation
---------------------

1. **Run a Basic Simulation**

   .. code-block:: bash

       # Run a 600-second simulation with default parameters
       python -m src.cli.run simulate --mode disagg --sim-seconds 600

   This will output JSON statistics including TTFT metrics.

2. **Compare Architectures**

   .. code-block:: bash

       # Compare monolithic vs disaggregated
       python -m src.cli.compare

3. **Generate Visualizations**

   .. code-block:: bash

       # Generate TTFT vs arrival rate plot
       python -m src.analysis.sweep --rates 0.5,1,2,3,4,5

Using Configuration Files
-------------------------

1. **Create a Configuration File**

   Create a file named ``my_config.yaml``:

   .. code-block:: yaml

       mode: disagg
       sim_seconds: 600.0
       warmup_seconds: 60.0

       arrival:
         rate_per_s: 2.0

       prompt_tokens:
         mode: real_mean_std
         mean: 1024
         std: 512
         min_value: 8

       output_tokens:
         mode: real_mean_std
         mean: 256
         std: 128
         min_value: 16

       cluster_disagg:
         prefill_gpus: 2
         decode_gpus: 2
         prefill_tokens_per_s: 8000.0
         decode_tokens_per_s: 2000.0

2. **Run with Configuration**

   .. code-block:: bash

       python -m src.cli.run simulate --config my_config.yaml

Python API Usage
----------------

You can also use the simulator programmatically:

.. code-block:: python

    from src.core.simulator import run_simulation
    from src.core.config import SimConfig

    # Create configuration
    config = SimConfig(
        mode="disagg",
        sim_seconds=600.0,
        warmup_seconds=60.0
    )

    # Run simulation
    metrics, stats = run_simulation(
        mode=config.mode,
        sim_seconds=config.sim_seconds,
        warmup_seconds=config.warmup_seconds,
        random_seed=config.random_seed,
        arrival_rate_per_s=2.0,
        prompt_lognormal=(6.0, 0.9, 8),
        output_lognormal=(6.0, 1.1, 16),
        disagg_params=(2, 2, 8000.0, 2000.0)
    )

    # Print results
    print(f"Mean TTFT: {stats['mean_ttft_s']:.3f}s")
    print(f"P99 TTFT: {stats['p99_ttft_s']:.3f}s")
    print(f"Throughput: {stats['throughput_rps']:.2f} req/s")

Understanding Output
--------------------

The simulator outputs JSON statistics with the following key fields:

* **TTFT Statistics**:
  * ``mean_ttft_s``: Average TTFT in seconds
  * ``p50_ttft_s``: 50th percentile TTFT
  * ``p90_ttft_s``: 90th percentile TTFT
  * ``p99_ttft_s``: 99th percentile TTFT

* **Performance Metrics**:
  * ``throughput_rps``: Requests per second
  * ``utilization_prefill``: Prefill GPU utilization (disaggregated)
  * ``utilization_decode``: Decode GPU utilization (disaggregated)

* **Simulation Info**:
  * ``num_samples``: Number of completed requests
  * ``elapsed_s``: Total simulation time
  * ``mode``: Simulation mode (mono/disagg)

Example Output
~~~~~~~~~~~~~

.. code-block:: json

    {
      "num_samples": 1200,
      "mean_ttft_s": 0.245,
      "p50_ttft_s": 0.198,
      "p90_ttft_s": 0.456,
      "p99_ttft_s": 0.789,
      "elapsed_s": 600.0,
      "mode": "disagg",
      "throughput_rps": 2.0,
      "utilization_prefill": 0.65,
      "utilization_decode": 0.89
    }

Advanced Usage
--------------

1. **Sweep Analysis**

   .. code-block:: bash

       # Study TTFT vs arrival rate
       python -m src.analysis.sweep --rates 0.5,1,2,3,4,5

       # Study prefill rate sensitivity
       python -m src.analysis.sweep_prefill --rates 1,2,3,4 --prefill 4000,8000,12000,16000

2. **Custom Token Distributions**

   The simulator supports multiple token distribution modes:

   * **Log-space** (backward compatible):
     .. code-block:: yaml

         prompt_tokens:
           mode: log
           mean: 6.0   # log-space mu
           sigma: 0.9  # log-space sigma
           min_value: 8

   * **Real-space mean/std**:
     .. code-block:: yaml

         prompt_tokens:
           mode: real_mean_std
           mean: 1024   # tokens
           std: 512
           min_value: 8

   * **Real-space percentiles**:
     .. code-block:: yaml

         prompt_tokens:
           mode: p50_p90
           p50: 128
           p90: 512
           min_value: 8

3. **Dump Raw Data**

   .. code-block:: bash

       # Dump raw TTFT samples for custom analysis
       python -m src.cli.run simulate --mode disagg --dump-ttft ttft_samples.json

Next Steps
----------

Now that you've completed the quick start:

1. Read the :doc:`user_guide` for detailed usage instructions
2. Explore the :doc:`examples` for more complex scenarios
3. Check the :doc:`api_reference` for complete API documentation
4. Read the :doc:`theory` for theoretical background
5. Review the :doc:`architecture` for system design details

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~~

1. **Module not found errors**: Make sure you're in the correct directory and virtual environment is activated
2. **Configuration errors**: Check YAML syntax and required fields
3. **Memory issues**: Reduce simulation time or warmup period for large simulations

Getting Help
------------

If you encounter issues:

1. Check the :doc:`troubleshooting` section
2. Search existing issues on GitHub
3. Create a new issue with detailed information
