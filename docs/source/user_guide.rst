User Guide
==========

This guide provides detailed information on using the LLM Simulator for various scenarios and configurations.

Configuration
-------------

The simulator uses YAML configuration files for easy parameter management.

Basic Configuration Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    # Simulation mode: mono (monolithic) or disagg (disaggregated)
    mode: disagg

    # Simulation parameters
    sim_seconds: 600.0
    warmup_seconds: 60.0
    random_seed: 42

    # Arrival configuration
    arrival:
      rate_per_s: 2.0

    # Token distributions
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

    # Cluster configuration
    cluster_mono:
      num_gpus: 4
      prefill_tokens_per_s: 8000.0
      decode_tokens_per_s: 2000.0

    cluster_disagg:
      prefill_gpus: 2
      decode_gpus: 2
      prefill_tokens_per_s: 8000.0
      decode_tokens_per_s: 2000.0

Token Distribution Modes
~~~~~~~~~~~~~~~~~~~~~~~~

The simulator supports three modes for specifying token distributions:

1. **Log-space Mode** (Backward Compatible):

   .. code-block:: yaml

       prompt_tokens:
         mode: log
         mean: 6.0   # log-space mu
         sigma: 0.9  # log-space sigma
         min_value: 8

2. **Real-space Mean/Std Mode**:

   .. code-block:: yaml

       prompt_tokens:
         mode: real_mean_std
         mean: 1024   # tokens
         std: 512
         min_value: 8

3. **Real-space Percentiles Mode**:

   .. code-block:: yaml

       prompt_tokens:
         mode: p50_p90
         p50: 128
         p90: 512
         min_value: 8

Command Line Interface
---------------------

Basic Commands
~~~~~~~~~~~~~~

1. **Run Simulation**:

   .. code-block:: bash

       # Basic simulation
       python -m src.cli.run simulate --mode disagg --sim-seconds 600

       # With configuration file
       python -m src.cli.run simulate --config examples/example_config.yaml

       # With custom parameters
       python -m src.cli.run simulate --mode mono --sim-seconds 300 --warmup-seconds 30

2. **Compare Architectures**:

   .. code-block:: bash

       python -m src.cli.compare

3. **Generate Visualizations**:

   .. code-block:: bash

       # TTFT vs arrival rate
       python -m src.analysis.sweep --rates 0.5,1,2,3,4,5

       # Prefill rate sensitivity
       python -m src.analysis.sweep_prefill --rates 1,2,3,4 --prefill 4000,8000,12000,16000

Advanced Usage
--------------

Custom Token Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create custom token distributions by specifying the appropriate mode:

.. code-block:: yaml

    # For heavy-tailed distributions
    prompt_tokens:
      mode: p50_p90
      p50: 64
      p90: 1024
      min_value: 8

    # For normal-like distributions
    output_tokens:
      mode: real_mean_std
      mean: 128
      std: 64
      min_value: 16

Performance Tuning
~~~~~~~~~~~~~~~~~~

1. **Simulation Duration**:
   - Use longer `sim_seconds` for more accurate statistics
   - Increase `warmup_seconds` to ensure steady-state analysis

2. **Resource Allocation**:
   - Balance prefill and decode GPU counts based on workload
   - Monitor utilization metrics to identify bottlenecks

3. **Memory Management**:
   - Reduce simulation time for large-scale experiments
   - Use `--dump-ttft` for post-processing analysis

Analysis and Visualization
--------------------------

Sweep Analysis
~~~~~~~~~~~~~~

The simulator provides built-in sweep analysis tools:

1. **Arrival Rate Sweep**:

   .. code-block:: bash

       python -m src.analysis.sweep --rates 0.5,1,2,3,4,5 --sim-seconds 600

   This generates a plot showing TTFT percentiles vs arrival rate.

2. **Prefill Rate Sensitivity**:

   .. code-block:: bash

       python -m src.analysis.sweep_prefill --rates 1,2,3,4 --prefill 4000,8000,12000,16000

   This shows how TTFT varies with different prefill computation speeds.

Custom Analysis
~~~~~~~~~~~~~~~

You can perform custom analysis by dumping raw data:

.. code-block:: bash

    # Dump raw TTFT samples
    python -m src.cli.run simulate --mode disagg --dump-ttft ttft_samples.json

Then analyze the data using your preferred tools:

.. code-block:: python

    import json
    import numpy as np
    import matplotlib.pyplot as plt

    # Load raw data
    with open('ttft_samples.json', 'r') as f:
        ttft_samples = json.load(f)

    # Custom analysis
    ttft_array = np.array(ttft_samples)
    print(f"Mean TTFT: {ttft_array.mean():.3f}s")
    print(f"Std TTFT: {ttft_array.std():.3f}s")

    # Custom plotting
    plt.hist(ttft_array, bins=50, alpha=0.7)
    plt.xlabel('TTFT (seconds)')
    plt.ylabel('Frequency')
    plt.title('TTFT Distribution')
    plt.show()

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

1. **Configuration Errors**:
   - Check YAML syntax
   - Ensure all required fields are present
   - Verify token distribution parameters

2. **Performance Issues**:
   - Reduce simulation time for large experiments
   - Check memory usage
   - Use appropriate warmup periods

3. **Import Errors**:
   - Ensure virtual environment is activated
   - Check Python path
   - Verify installation

4. **Visualization Issues**:
   - Install matplotlib: `pip install matplotlib`
   - Check display settings
   - Use appropriate backend

Best Practices
--------------

1. **Configuration Management**:
   - Use version control for configuration files
   - Document parameter choices
   - Use descriptive file names

2. **Simulation Design**:
   - Start with small simulations
   - Gradually increase complexity
   - Validate results with known scenarios

3. **Data Management**:
   - Save raw data for post-processing
   - Use consistent naming conventions
   - Document analysis procedures

4. **Performance Optimization**:
   - Profile simulation performance
   - Use appropriate simulation duration
   - Monitor resource usage

Examples
--------

Basic Examples
~~~~~~~~~~~~~~

1. **Light Load Scenario**:

   .. code-block:: yaml

       mode: disagg
       sim_seconds: 300.0
       warmup_seconds: 30.0
       arrival:
         rate_per_s: 1.0
       prompt_tokens:
         mode: real_mean_std
         mean: 512
         std: 256
         min_value: 8
       cluster_disagg:
         prefill_gpus: 1
         decode_gpus: 1
         prefill_tokens_per_s: 8000.0
         decode_tokens_per_s: 2000.0

2. **Heavy Load Scenario**:

   .. code-block:: yaml

       mode: mono
       sim_seconds: 600.0
       warmup_seconds: 60.0
       arrival:
         rate_per_s: 4.0
       prompt_tokens:
         mode: real_mean_std
         mean: 2048
         std: 1024
         min_value: 8
       cluster_mono:
         num_gpus: 4
         prefill_tokens_per_s: 8000.0
         decode_tokens_per_s: 2000.0

Advanced Examples
~~~~~~~~~~~~~~~~~

1. **Sensitivity Analysis**:

   .. code-block:: bash

       # Study impact of GPU count
       for gpus in 1 2 4 8; do
           python -m src.cli.run simulate \
               --mode disagg \
               --sim-seconds 300 \
               --config examples/example_config.yaml \
               --dump-ttft "results_${gpus}gpus.json"
       done

2. **Comparative Analysis**:

   .. code-block:: bash

       # Compare architectures under same load
       python -m src.cli.run simulate --mode mono --sim-seconds 600 > mono_results.json
       python -m src.cli.run simulate --mode disagg --sim-seconds 600 > disagg_results.json

3. **Custom Analysis Script**:

   .. code-block:: python

       import json
       import subprocess
       import sys

       def run_simulation_with_params(mode, arrival_rate, gpus):
           cmd = [
               sys.executable, "-m", "src.cli.run", "simulate",
               "--mode", mode,
               "--sim-seconds", "300",
               "--warmup-seconds", "30"
           ]
           result = subprocess.run(cmd, capture_output=True, text=True, check=True)
           return json.loads(result.stdout)

       # Run multiple simulations
       results = []
       for rate in [1.0, 2.0, 3.0, 4.0]:
           for gpus in [1, 2, 4]:
               stats = run_simulation_with_params("disagg", rate, gpus)
               results.append({
                   "arrival_rate": rate,
                   "gpus": gpus,
                   "mean_ttft": stats["mean_ttft_s"]
               })

       # Save results
       with open("sensitivity_results.json", "w") as f:
           json.dump(results, f, indent=2)
