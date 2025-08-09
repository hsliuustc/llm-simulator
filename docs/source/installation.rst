Installation Guide
==================

This guide will help you install and set up the LLM Simulator for your environment.

Prerequisites
-------------

* Python 3.8 or higher
* pip (Python package installer)
* Git (for cloning the repository)

System Requirements
-------------------

* **Operating System**: Linux, macOS, or Windows
* **Memory**: At least 4GB RAM (8GB recommended for large simulations)
* **Storage**: At least 1GB free space
* **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12

Installation Methods
--------------------

Method 1: From Source (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Clone the repository**:

   .. code-block:: bash

       git clone https://github.com/yourusername/llm-simulator.git
       cd llm-simulator

2. **Create a virtual environment**:

   .. code-block:: bash

       # On Linux/macOS
       python -m venv .venv
       source .venv/bin/activate

       # On Windows
       python -m venv .venv
       .venv\Scripts\activate

3. **Install dependencies**:

   .. code-block:: bash

       pip install -r src/requirements.txt

4. **Verify installation**:

   .. code-block:: bash

       python -c "import src; print('Installation successful!')"

Method 2: Using pip (Future)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the package is published to PyPI, you can install it using:

.. code-block:: bash

    pip install llm-simulator

Dependencies
------------

The following packages are automatically installed when you run ``pip install -r src/requirements.txt``:

* **simpy** (4.1.1): Discrete-event simulation framework
* **numpy** (2.0.2): Numerical computing library
* **PyYAML** (6.0.2): YAML parser and emitter
* **click** (8.1.7): Command-line interface creation kit
* **matplotlib** (3.9.0): Plotting library

Optional Dependencies
---------------------

For documentation development:

.. code-block:: bash

    pip install sphinx sphinx-rtd-theme myst-parser

For development and testing:

.. code-block:: bash

    pip install pytest black flake8 mypy

Configuration
-------------

After installation, you can configure the simulator using YAML files. See the :doc:`user_guide` for detailed configuration options.

Example configuration file (``examples/example_config.yaml``):

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

    cluster_disagg:
      prefill_gpus: 2
      decode_gpus: 2
      prefill_tokens_per_s: 8000.0
      decode_tokens_per_s: 2000.0

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~~

1. **ImportError: No module named 'src'**:
   
   Make sure you're in the correct directory and the virtual environment is activated.

2. **Permission denied errors**:
   
   On Linux/macOS, you might need to use ``sudo`` or fix permissions:
   
   .. code-block:: bash

       sudo pip install -r src/requirements.txt

3. **Python version issues**:
   
   Ensure you're using Python 3.8 or higher:
   
   .. code-block:: bash

       python --version

4. **Virtual environment issues**:
   
   If you encounter issues with virtual environments, try:
   
   .. code-block:: bash

       python -m venv --clear .venv
       source .venv/bin/activate
       pip install --upgrade pip
       pip install -r src/requirements.txt

Getting Help
------------

If you encounter any issues during installation:

1. Check the :doc:`troubleshooting` section
2. Search existing issues on GitHub
3. Create a new issue with detailed information about your environment

Next Steps
----------

After successful installation, you can:

1. Read the :doc:`quickstart` guide
2. Explore the :doc:`examples`
3. Check the :doc:`api_reference` for detailed API documentation
