API Reference
=============

This section provides detailed documentation for the LLM Simulator API.

Core Module
-----------

.. automodule:: src.core
   :members:
   :undoc-members:
   :show-inheritance:

Simulator
~~~~~~~~~

.. automodule:: src.core.simulator
   :members:
   :undoc-members:
   :show-inheritance:

Configuration
~~~~~~~~~~~~~

.. automodule:: src.core.config
   :members:
   :undoc-members:
   :show-inheritance:

CLI Module
----------

.. automodule:: src.cli
   :members:
   :undoc-members:
   :show-inheritance:

Run Command
~~~~~~~~~~~

.. automodule:: src.cli.run
   :members:
   :undoc-members:
   :show-inheritance:

Compare Command
~~~~~~~~~~~~~~~

.. automodule:: src.cli.compare
   :members:
   :undoc-members:
   :show-inheritance:

Analysis Module
---------------

.. automodule:: src.analysis
   :members:
   :undoc-members:
   :show-inheritance:

Sweep Analysis
~~~~~~~~~~~~~~

.. automodule:: src.analysis.sweep
   :members:
   :undoc-members:
   :show-inheritance:

Prefill Sweep Analysis
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.analysis.sweep_prefill
   :members:
   :undoc-members:
   :show-inheritance:

Visualization
~~~~~~~~~~~~~

.. automodule:: src.analysis.visualize
   :members:
   :undoc-members:
   :show-inheritance:

Utils Module
------------

.. automodule:: src.utils
   :members:
   :undoc-members:
   :show-inheritance:

Scenarios
~~~~~~~~~

.. automodule:: src.utils.scenarios
   :members:
   :undoc-members:
   :show-inheritance:

Data Structures
---------------

Request
~~~~~~~~

.. autoclass:: src.core.simulator.Request
   :members:
   :undoc-members:
   :show-inheritance:

Metrics
~~~~~~~

.. autoclass:: src.core.simulator.Metrics
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Classes
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: src.core.config.SimConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.config.ArrivalConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.config.PromptConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.config.OutputConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.config.ClusterMonolithic
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.config.ClusterDisagg
   :members:
   :undoc-members:
   :show-inheritance:

Simulator Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: src.core.simulator.MonolithicSimulator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.simulator.DisaggregatedSimulator
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

Core Functions
~~~~~~~~~~~~~~

.. autofunction:: src.core.simulator.run_simulation

.. autofunction:: src.core.simulator.poisson_interarrival_time

.. autofunction:: src.core.simulator.lognormal_tokens

Configuration Functions
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: src.core.config.load_config

.. autofunction:: src.core.config._real_mean_std_to_log_params

.. autofunction:: src.core.config._p50_p90_to_log_params

.. autofunction:: src.core.config._parse_token_dist

CLI Functions
~~~~~~~~~~~~~

.. autofunction:: src.cli.run.simulate

.. autofunction:: src.cli.run._log_to_real

.. autofunction:: src.cli.compare.run_sim

.. autofunction:: src.cli.compare.main

Analysis Functions
~~~~~~~~~~~~~~~~~~

.. autofunction:: src.analysis.sweep.run_point

.. autofunction:: src.analysis.sweep.main

.. autofunction:: src.analysis.sweep_prefill.run_point

.. autofunction:: src.analysis.sweep_prefill.main

.. autofunction:: src.analysis.visualize.run_sim_with_details

.. autofunction:: src.analysis.visualize.plot_ttft_comparison

Utility Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: src.utils.scenarios.Scenario.apply

.. autofunction:: src.utils.scenarios.LightLoadDisagg.apply

.. autofunction:: src.utils.scenarios.HeavyLoadMono.apply

Constants
---------

.. data:: src.core.simulator.DEFAULT_RANDOM_SEED
   :annotation: = 42

.. data:: src.core.simulator.DEFAULT_SIM_SECONDS
   :annotation: = 600.0

.. data:: src.core.simulator.DEFAULT_WARMUP_SECONDS
   :annotation: = 60.0

Exceptions
----------

.. autoexception:: src.core.config.ValueError

   Raised when invalid configuration parameters are provided.

.. autoexception:: src.core.simulator.AssertionError

   Raised when invalid simulation parameters are provided.

Type Hints
----------

The simulator uses type hints throughout the codebase. Key types include:

.. code-block:: python

    from typing import List, Optional, Tuple, Dict, Any

    # Common type aliases
    LogNormalParams = Tuple[float, float, int]  # (mean, sigma, min_value)
    MonoParams = Tuple[int, float, float]       # (num_gpus, prefill_rate, decode_rate)
    DisaggParams = Tuple[int, int, float, float]  # (prefill_gpus, decode_gpus, prefill_rate, decode_rate)

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from src.core.simulator import run_simulation
    from src.core.config import SimConfig

    # Run a simple simulation
    metrics, stats = run_simulation(
        mode="disagg",
        sim_seconds=600.0,
        warmup_seconds=60.0,
        random_seed=42,
        arrival_rate_per_s=2.0,
        prompt_lognormal=(6.0, 0.9, 8),
        output_lognormal=(6.0, 1.1, 16),
        disagg_params=(2, 2, 8000.0, 2000.0)
    )

    print(f"Mean TTFT: {stats['mean_ttft_s']:.3f}s")

Configuration Usage
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from src.core.config import SimConfig, load_config

    # Load from YAML file
    config = load_config("examples/example_config.yaml")
    
    # Create programmatically
    config = SimConfig(
        mode="disagg",
        sim_seconds=600.0,
        warmup_seconds=60.0
    )
    
    # Access configuration
    print(f"Mode: {config.mode}")
    print(f"Arrival rate: {config.arrival.rate_per_s}")

CLI Usage
~~~~~~~~~

.. code-block:: python

    from src.cli.run import simulate
    import click

    # Run simulation via CLI
    with click.Context(click.Command('simulate')):
        simulate(
            mode="disagg",
            sim_seconds=600.0,
            warmup_seconds=60.0,
            seed=42,
            config=None,
            dump_ttft=None
        )

Analysis Usage
~~~~~~~~~~~~~~

.. code-block:: python

    from src.analysis.sweep import main as sweep_main
    from src.analysis.visualize import plot_ttft_comparison

    # Run sweep analysis
    sweep_main()
    
    # Generate visualization
    plot_ttft_comparison()
