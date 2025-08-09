Examples
========

This section provides comprehensive examples of using the LLM Simulator for various scenarios.

Basic Examples
--------------

Simple Simulation
~~~~~~~~~~~~~~~~~

Run a basic simulation with default parameters:

.. code-block:: bash

    python -m src.cli.run simulate --mode disagg --sim-seconds 600

This will output JSON statistics including TTFT metrics.

Configuration File Example
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a configuration file ``my_config.yaml``:

.. code-block:: yaml

    mode: disagg
    sim_seconds: 600.0
    warmup_seconds: 60.0
    random_seed: 42

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

Run with the configuration:

.. code-block:: bash

    python -m src.cli.run simulate --config my_config.yaml

Python API Example
~~~~~~~~~~~~~~~~~~

Use the simulator programmatically:

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

Advanced Examples
-----------------

Sweep Analysis
~~~~~~~~~~~~~~

Study TTFT performance across different arrival rates:

.. code-block:: bash

    python -m src.analysis.sweep --rates 0.5,1,2,3,4,5 --sim-seconds 600

This generates a plot showing TTFT percentiles vs arrival rate.

Prefill Rate Sensitivity
~~~~~~~~~~~~~~~~~~~~~~~~

Study how TTFT varies with different prefill computation speeds:

.. code-block:: bash

    python -m src.analysis.sweep_prefill --rates 1,2,3,4 --prefill 4000,8000,12000,16000

This shows how TTFT varies with different prefill rates.

Custom Analysis
~~~~~~~~~~~~~~~

Dump raw TTFT samples for custom analysis:

.. code-block:: bash

    python -m src.cli.run simulate --mode disagg --dump-ttft ttft_samples.json

Then analyze the data:

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

Comparative Analysis
~~~~~~~~~~~~~~~~~~~

Compare monolithic vs disaggregated architectures:

.. code-block:: bash

    # Run both simulations
    python -m src.cli.run simulate --mode mono --sim-seconds 600 > mono_results.json
    python -m src.cli.run simulate --mode disagg --sim-seconds 600 > disagg_results.json

    # Compare results
    python -m src.cli.compare

Scenario Examples
-----------------

Light Load Scenario
~~~~~~~~~~~~~~~~~~~

Configuration for light load:

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

Heavy Load Scenario
~~~~~~~~~~~~~~~~~~~

Configuration for heavy load:

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

High Variance Scenario
~~~~~~~~~~~~~~~~~~~~~~

Configuration for high variance in token distributions:

.. code-block:: yaml

    mode: disagg
    sim_seconds: 600.0
    warmup_seconds: 60.0
    arrival:
      rate_per_s: 2.0
    prompt_tokens:
      mode: p50_p90
      p50: 128
      p90: 2048
      min_value: 8
    output_tokens:
      mode: p50_p90
      p50: 64
      p90: 512
      min_value: 16
    cluster_disagg:
      prefill_gpus: 2
      decode_gpus: 2
      prefill_tokens_per_s: 8000.0
      decode_tokens_per_s: 2000.0

Performance Tuning Examples
---------------------------

GPU Allocation Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Study the impact of different GPU allocations:

.. code-block:: bash

    # Test different GPU configurations
    for prefill_gpus in 1 2 4; do
        for decode_gpus in 1 2 4; do
            python -m src.cli.run simulate \
                --mode disagg \
                --sim-seconds 300 \
                --config examples/example_config.yaml \
                --dump-ttft "results_${prefill_gpus}p_${decode_gpus}d.json"
        done
    done

Token Rate Optimization
~~~~~~~~~~~~~~~~~~~~~~~

Study the impact of different token processing rates:

.. code-block:: bash

    # Test different prefill rates
    for prefill_rate in 4000 8000 12000 16000; do
        python -m src.cli.run simulate \
            --mode disagg \
            --sim-seconds 300 \
            --config examples/example_config.yaml \
            --dump-ttft "results_prefill_${prefill_rate}.json"
    done

Custom Analysis Scripts
-----------------------

Sensitivity Analysis Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    import subprocess
    import sys
    from typing import Dict, Any

    def run_simulation_with_params(mode: str, arrival_rate: float, gpus: int) -> Dict[str, Any]:
        """Run a simulation with given parameters."""
        cmd = [
            sys.executable, "-m", "src.cli.run", "simulate",
            "--mode", mode,
            "--sim-seconds", "300",
            "--warmup-seconds", "30"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def main():
        """Run sensitivity analysis."""
        results = []
        
        # Test different arrival rates and GPU counts
        for rate in [1.0, 2.0, 3.0, 4.0]:
            for gpus in [1, 2, 4]:
                try:
                    stats = run_simulation_with_params("disagg", rate, gpus)
                    results.append({
                        "arrival_rate": rate,
                        "gpus": gpus,
                        "mean_ttft": stats["mean_ttft_s"],
                        "p99_ttft": stats["p99_ttft_s"],
                        "throughput": stats["throughput_rps"]
                    })
                except Exception as e:
                    print(f"Error with rate={rate}, gpus={gpus}: {e}")

        # Save results
        with open("sensitivity_results.json", "w") as f:
            json.dump(results, f, indent=2)

        # Print summary
        print("Sensitivity Analysis Results:")
        for result in results:
            print(f"Rate: {result['arrival_rate']}, GPUs: {result['gpus']}, "
                  f"Mean TTFT: {result['mean_ttft']:.3f}s, "
                  f"P99 TTFT: {result['p99_ttft']:.3f}s")

    if __name__ == "__main__":
        main()

Batch Processing Script
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    import subprocess
    import sys
    from pathlib import Path

    def run_batch_simulations(config_files: list) -> dict:
        """Run multiple simulations with different config files."""
        results = {}
        
        for config_file in config_files:
            if not Path(config_file).exists():
                print(f"Config file {config_file} not found, skipping...")
                continue
                
            try:
                cmd = [
                    sys.executable, "-m", "src.cli.run", "simulate",
                    "--config", config_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                stats = json.loads(result.stdout)
                
                config_name = Path(config_file).stem
                results[config_name] = stats
                
                print(f"Completed {config_name}: Mean TTFT = {stats['mean_ttft_s']:.3f}s")
                
            except Exception as e:
                print(f"Error running {config_file}: {e}")
        
        return results

    def main():
        """Run batch simulations."""
        config_files = [
            "examples/light_load.yaml",
            "examples/heavy_load.yaml",
            "examples/high_variance.yaml"
        ]
        
        results = run_batch_simulations(config_files)
        
        # Save all results
        with open("batch_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\nBatch Processing Summary:")
        for config_name, stats in results.items():
            print(f"{config_name}: Mean TTFT = {stats['mean_ttft_s']:.3f}s, "
                  f"P99 TTFT = {stats['p99_ttft_s']:.3f}s")

    if __name__ == "__main__":
        main()

Visualization Examples
-----------------------

Custom Plotting
~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    import matplotlib.pyplot as plt
    import numpy as np

    def plot_ttft_comparison(results_files: list):
        """Create custom TTFT comparison plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        for results_file in results_files:
            with open(results_file, 'r') as f:
                stats = json.load(f)
            
            # Extract data
            mean_ttft = stats['mean_ttft_s']
            p99_ttft = stats['p99_ttft_s']
            
            # Plot on first subplot
            ax1.bar(results_file, mean_ttft, alpha=0.7, label='Mean TTFT')
            ax2.bar(results_file, p99_ttft, alpha=0.7, label='P99 TTFT')
        
        ax1.set_ylabel('Mean TTFT (seconds)')
        ax1.set_title('Mean TTFT Comparison')
        ax1.legend()
        
        ax2.set_ylabel('P99 TTFT (seconds)')
        ax2.set_title('P99 TTFT Comparison')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('custom_ttft_comparison.png', dpi=150, bbox_inches='tight')
        plt.show()

    # Usage
    results_files = ['mono_results.json', 'disagg_results.json']
    plot_ttft_comparison(results_files)

Heatmap Visualization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns

    def create_ttft_heatmap(results_data: list):
        """Create a heatmap of TTFT vs arrival rate and GPU count."""
        # Extract data
        arrival_rates = []
        gpu_counts = []
        ttft_values = []
        
        for result in results_data:
            arrival_rates.append(result['arrival_rate'])
            gpu_counts.append(result['gpus'])
            ttft_values.append(result['mean_ttft'])
        
        # Create pivot table
        import pandas as pd
        df = pd.DataFrame({
            'arrival_rate': arrival_rates,
            'gpus': gpu_counts,
            'ttft': ttft_values
        })
        
        pivot_table = df.pivot(index='gpus', columns='arrival_rate', values='ttft')
        
        # Create heatmap
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_table, annot=True, fmt='.3f', cmap='YlOrRd')
        plt.title('TTFT Heatmap: Arrival Rate vs GPU Count')
        plt.xlabel('Arrival Rate (req/s)')
        plt.ylabel('GPU Count')
        plt.tight_layout()
        plt.savefig('ttft_heatmap.png', dpi=150, bbox_inches='tight')
        plt.show()

    # Usage
    with open('sensitivity_results.json', 'r') as f:
        results_data = json.load(f)
    
    create_ttft_heatmap(results_data)
