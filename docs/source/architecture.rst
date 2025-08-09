Architecture
===========

This section provides a detailed overview of the LLM Simulator's architecture and design principles.

System Overview
---------------

The LLM Simulator is designed as a modular, extensible discrete-event simulation framework for studying Time-To-First-Token (TTFT) performance in LLM serving systems.

Key Design Principles
~~~~~~~~~~~~~~~~~~~~~

1. **Modularity**: Clear separation of concerns between simulation engine, configuration, and analysis
2. **Extensibility**: Easy to add new features and simulation scenarios
3. **Usability**: Simple CLI interface and comprehensive documentation
4. **Performance**: Efficient simulation for large-scale experiments
5. **Reproducibility**: Deterministic results with configurable random seeds

Architecture Components
----------------------

Core Module (src/core/)
~~~~~~~~~~~~~~~~~~~~~~~

The core module contains the fundamental simulation components:

**Simulator Engine** (``simulator.py``)
- Discrete-event simulation using SimPy
- Request processing and resource management
- Metrics collection and statistics computation

**Configuration Management** (``config.py``)
- YAML-based configuration system
- Multiple token distribution modes
- Parameter validation and conversion

Key Classes:

.. code-block:: python

    class Request:
        """Represents a single user request with prompt and output tokens."""
        
    class Metrics:
        """Collects and manages simulation metrics and statistics."""
        
    class MonolithicSimulator:
        """Simulates monolithic LLM serving architecture."""
        
    class DisaggregatedSimulator:
        """Simulates disaggregated prefill/decode architecture."""

CLI Module (src/cli/)
~~~~~~~~~~~~~~~~~~~~

The CLI module provides command-line interfaces:

**Run Command** (``run.py``)
- Main simulation execution interface
- Configuration file support
- Raw data export capabilities

**Compare Command** (``compare.py``)
- Quick comparison of monolithic vs disaggregated modes
- Automated performance analysis

Analysis Module (src/analysis/)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The analysis module provides tools for studying simulation results:

**Sweep Analysis** (``sweep.py``)
- Arrival rate sensitivity analysis
- TTFT percentile plotting

**Prefill Sensitivity** (``sweep_prefill.py``)
- Prefill rate impact analysis
- Multi-parameter studies

**Visualization** (``visualize.py``)
- TTFT distribution plotting
- Comparative analysis visualization

Utils Module (src/utils/)
~~~~~~~~~~~~~~~~~~~~~~~~~

The utils module contains helper functions and predefined scenarios:

**Scenarios** (``scenarios.py``)
- Predefined simulation configurations
- Common workload patterns

Data Flow
---------

Request Processing Flow
~~~~~~~~~~~~~~~~~~~~~~~

1. **Request Generation**:
   - Poisson arrival process
   - Lognormal token distribution sampling
   - Request object creation

2. **Resource Allocation**:
   - GPU pool acquisition
   - Queue management
   - Resource contention handling

3. **Processing Stages**:
   - Prefill stage (all prompt tokens)
   - Decode stage (first token for TTFT)
   - Remaining decode (post-TTFT)

4. **Metrics Collection**:
   - TTFT measurement
   - GPU utilization tracking
   - Throughput computation

Monolithic Architecture
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    Request → GPU Pool → [Prefill + Decode] → Completion
                ↑
            Resource
           Management

Disaggregated Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    Request → Prefill Pool → Decode Pool → Completion
                ↑              ↑
            Resource        Resource
           Management     Management

Configuration System
--------------------

YAML Configuration Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simulator uses a hierarchical YAML configuration system:

.. code-block:: yaml

    # Top-level simulation parameters
    mode: disagg                    # Simulation mode
    sim_seconds: 600.0             # Simulation duration
    warmup_seconds: 60.0           # Warmup period
    random_seed: 42                # Random seed

    # Arrival configuration
    arrival:
      rate_per_s: 2.0             # Poisson arrival rate

    # Token distributions
    prompt_tokens:
      mode: real_mean_std         # Distribution mode
      mean: 1024                  # Mean tokens
      std: 512                    # Standard deviation
      min_value: 8                # Minimum value

    # Cluster configuration
    cluster_disagg:
      prefill_gpus: 2             # Prefill GPU count
      decode_gpus: 2              # Decode GPU count
      prefill_tokens_per_s: 8000.0 # Prefill rate
      decode_tokens_per_s: 2000.0  # Decode rate

Token Distribution Modes
~~~~~~~~~~~~~~~~~~~~~~~~

The simulator supports three modes for specifying token distributions:

1. **Log-space Mode** (Backward Compatible):
   - Direct specification of log-space parameters
   - Compatible with existing configurations

2. **Real-space Mean/Std Mode**:
   - Human-readable mean and standard deviation
   - Automatic conversion to log-space

3. **Real-space Percentiles Mode**:
   - Specification using P50 and P90 percentiles
   - Useful for matching real-world distributions

Metrics and Statistics
----------------------

TTFT Metrics
~~~~~~~~~~~~

The simulator computes comprehensive TTFT statistics:

- **Mean TTFT**: Average time-to-first-token
- **P50 TTFT**: 50th percentile (median)
- **P90 TTFT**: 90th percentile
- **P99 TTFT**: 99th percentile

Performance Metrics
~~~~~~~~~~~~~~~~~~~

Additional performance metrics include:

- **Throughput**: Requests per second
- **GPU Utilization**: Fraction of time GPUs are busy
- **Queue Lengths**: Average waiting times
- **Service Times**: Processing times per stage

Data Collection
~~~~~~~~~~~~~~~

Metrics are collected using:

1. **Event-based collection**: TTFT measured at first token emission
2. **Time-based filtering**: Warmup period exclusion
3. **Statistical aggregation**: Percentile computation using numpy

Extensibility
-------------

Adding New Features
~~~~~~~~~~~~~~~~~~~

The simulator is designed for easy extension:

1. **New Simulators**: Implement custom simulator classes
2. **New Metrics**: Extend Metrics class with additional statistics
3. **New Distributions**: Add distribution modes to configuration system
4. **New Analysis**: Create analysis scripts in analysis module

Example Extension
~~~~~~~~~~~~~~~~~

Adding a new simulator:

.. code-block:: python

    class CustomSimulator:
        def __init__(self, env, **kwargs):
            # Initialize custom simulator
            pass
            
        def process(self, req, metrics):
            # Implement custom processing logic
            pass

Adding new metrics:

.. code-block:: python

    class ExtendedMetrics(Metrics):
        def __init__(self):
            super().__init__()
            self.custom_metric = 0.0
            
        def add_custom_metric(self, value):
            self.custom_metric += value

Performance Considerations
-------------------------

Simulation Performance
~~~~~~~~~~~~~~~~~~~~~~

The simulator is optimized for:

1. **Large-scale experiments**: Efficient memory usage
2. **Fast execution**: Optimized data structures
3. **Reproducible results**: Deterministic random number generation

Performance Tips
~~~~~~~~~~~~~~~~

1. **Simulation duration**: Balance accuracy vs execution time
2. **Warmup period**: Choose appropriate warmup length
3. **Memory usage**: Monitor for large simulations
4. **Parallel execution**: Run multiple simulations in parallel

Scalability
~~~~~~~~~~~

The simulator can handle:

- **Large arrival rates**: Up to 100+ requests/second
- **Long simulations**: 1000+ seconds
- **Complex scenarios**: Multiple GPU pools and stages

Limitations and Future Work
---------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

1. **Simplified service model**: No step-level batching
2. **No network overhead**: Instant resource transfers
3. **Homogeneous resources**: Same GPU types
4. **No admission control**: All requests accepted
5. **FIFO scheduling**: No priority queues

Future Extensions
~~~~~~~~~~~~~~~~~

1. **Batching support**: Step-level batching and KV-cache management
2. **Heterogeneous resources**: Different GPU types and rates
3. **Network modeling**: Transfer overheads between pools
4. **Advanced scheduling**: Priority queues and preemption
5. **Trace-driven workloads**: Real arrival patterns
6. **Power modeling**: Energy consumption and thermal effects

Development Guidelines
----------------------

Code Style
~~~~~~~~~~

1. **Type hints**: Use type hints throughout
2. **Documentation**: Comprehensive docstrings
3. **Testing**: Unit tests for core functionality
4. **Error handling**: Graceful error handling

Testing Strategy
~~~~~~~~~~~~~~~~

1. **Unit tests**: Test individual components
2. **Integration tests**: Test complete workflows
3. **Performance tests**: Validate simulation performance
4. **Regression tests**: Ensure backward compatibility

Documentation
~~~~~~~~~~~~~

1. **API documentation**: Comprehensive API reference
2. **User guides**: Step-by-step usage instructions
3. **Examples**: Practical usage examples
4. **Architecture docs**: System design documentation

Contributing
------------

Development Setup
~~~~~~~~~~~~~~~~~

1. **Environment setup**: Virtual environment and dependencies
2. **Code formatting**: Black and flake8
3. **Testing**: pytest framework
4. **Documentation**: Sphinx documentation

Contribution Process
~~~~~~~~~~~~~~~~~~~

1. **Feature requests**: GitHub issues
2. **Code review**: Pull request review process
3. **Testing**: Ensure all tests pass
4. **Documentation**: Update relevant documentation

This architecture provides a solid foundation for studying TTFT performance in LLM serving systems while maintaining flexibility for future extensions and improvements.
