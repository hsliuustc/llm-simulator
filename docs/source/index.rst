LLM Simulator Documentation
===========================

A comprehensive simulator for studying Time-To-First-Token (TTFT) performance in LLM serving systems, with support for both monolithic and disaggregated (DistServe-like) architectures.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   user_guide
   api_reference
   examples
   theory
   architecture
   contributing

.. image:: https://img.shields.io/badge/Python-3.8+-blue.svg
   :target: https://python.org
   :alt: Python 3.8+

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

Overview
--------

This project provides a discrete-event simulation framework to analyze TTFT performance under different LLM serving architectures:

* **Monolithic**: Each request holds a GPU from start to finish (prefill + full decode)
* **Disaggregated**: Prefill and decode stages use separate GPU pools (as in DistServe)

Key Features
------------

* **Flexible Configuration**: Support for multiple token distribution modes (log-space, real-space, percentiles)
* **Comprehensive Metrics**: TTFT percentiles (P50, P90, P99), throughput, GPU utilization
* **Visualization**: Built-in plotting for TTFT analysis
* **Documentation**: Detailed architecture and theory documentation
* **Extensible**: Clean architecture for adding new features

Quick Example
-------------

.. code-block:: python

    from src.core.simulator import run_simulation
    from src.core.config import SimConfig

    # Run a simulation
    config = SimConfig(mode="disagg", sim_seconds=600)
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

    print(f"Mean TTFT: {stats['mean_ttft_s']:.3f}s")
    print(f"P99 TTFT: {stats['p99_ttft_s']:.3f}s")

Installation
------------

.. code-block:: bash

    # Clone the repository
    git clone <repository-url>
    cd llm-simulator

    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -r src/requirements.txt

    # Install documentation dependencies
    pip install sphinx sphinx-rtd-theme myst-parser

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
