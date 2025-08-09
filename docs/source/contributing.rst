Contributing
============

Thank you for your interest in contributing to the LLM Simulator! This document provides guidelines for contributing to the project.

Getting Started
--------------

Development Setup
~~~~~~~~~~~~~~~~~

1. **Fork the repository**:
   - Fork the project on GitHub
   - Clone your fork locally

2. **Set up development environment**:
   .. code-block:: bash

       # Clone your fork
       git clone https://github.com/yourusername/llm-simulator.git
       cd llm-simulator

       # Create virtual environment
       python -m venv .venv
       source .venv/bin/activate  # On Windows: .venv\Scripts\activate

       # Install dependencies
       pip install -r src/requirements.txt

       # Install development dependencies
       pip install sphinx sphinx-rtd-theme myst-parser pytest black flake8 mypy

3. **Verify installation**:
   .. code-block:: bash

       python -c "import src; print('Development setup successful!')"

Development Workflow
-------------------

Code Style
~~~~~~~~~~

The project follows PEP 8 style guidelines:

1. **Code formatting**: Use Black for automatic formatting
   .. code-block:: bash

       black src/

2. **Linting**: Use flake8 for style checking
   .. code-block:: bash

       flake8 src/

3. **Type checking**: Use mypy for type checking
   .. code-block:: bash

       mypy src/

4. **Import sorting**: Use isort for import organization
   .. code-block:: bash

       isort src/

Testing
~~~~~~~

1. **Run tests**:
   .. code-block:: bash

       pytest tests/

2. **Run specific tests**:
   .. code-block:: bash

       pytest tests/test_simulator.py -v

3. **Run with coverage**:
   .. code-block:: bash

       pytest --cov=src tests/

Documentation
~~~~~~~~~~~~~

1. **Build documentation**:
   .. code-block:: bash

       cd docs
       make html

2. **View documentation**:
   - Open `docs/build/html/index.html` in your browser

3. **Check documentation**:
   .. code-block:: bash

       sphinx-build -b linkcheck docs/source docs/build/html

Contribution Guidelines
----------------------

Types of Contributions
~~~~~~~~~~~~~~~~~~~~~

We welcome various types of contributions:

1. **Bug fixes**: Fix issues and improve reliability
2. **New features**: Add new simulation capabilities
3. **Documentation**: Improve docs and examples
4. **Performance**: Optimize simulation performance
5. **Testing**: Add tests and improve coverage

Before Contributing
~~~~~~~~~~~~~~~~~~~

1. **Check existing issues**: Search for similar issues or feature requests
2. **Discuss changes**: Open an issue to discuss major changes
3. **Follow guidelines**: Ensure your contribution follows project guidelines

Code Contribution Process
-------------------------

1. **Create a feature branch**:
   .. code-block:: bash

       git checkout -b feature/your-feature-name

2. **Make your changes**:
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   .. code-block:: bash

       # Run all tests
       pytest tests/

       # Run specific tests
       pytest tests/test_your_feature.py

       # Check code style
       black src/
       flake8 src/
       mypy src/

4. **Commit your changes**:
   .. code-block:: bash

       git add .
       git commit -m "Add feature: brief description"

5. **Push to your fork**:
   .. code-block:: bash

       git push origin feature/your-feature-name

6. **Create a pull request**:
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the pull request template

Pull Request Guidelines
----------------------

Pull Request Template
~~~~~~~~~~~~~~~~~~~~~

When creating a pull request, please include:

1. **Description**: Clear description of changes
2. **Type of change**: Bug fix, feature, documentation, etc.
3. **Testing**: How you tested your changes
4. **Documentation**: Any documentation updates needed
5. **Breaking changes**: Any breaking changes and migration guide

Example pull request:

```markdown
## Description
Add support for custom token distributions using percentiles.

## Type of change
- [ ] Bug fix
- [x] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- Added unit tests for percentile conversion functions
- Tested with example configurations
- Verified backward compatibility

## Documentation
- Updated user guide with percentile examples
- Added API documentation for new functions

## Breaking changes
None - this is a backward-compatible addition.
```

Review Process
~~~~~~~~~~~~~

1. **Code review**: All contributions require review
2. **CI/CD checks**: Automated tests must pass
3. **Documentation**: Documentation must be updated
4. **Testing**: Adequate test coverage required

Development Guidelines
---------------------

Code Quality
~~~~~~~~~~~

1. **Type hints**: Use type hints for all functions
2. **Docstrings**: Comprehensive docstrings for all functions
3. **Error handling**: Graceful error handling
4. **Logging**: Appropriate logging for debugging

Example:

.. code-block:: python

    from typing import Optional, Tuple

    def convert_percentiles_to_log_params(p50: float, p90: float) -> Tuple[float, float]:
        """
        Convert P50 and P90 percentiles to lognormal parameters.
        
        Args:
            p50: 50th percentile value
            p90: 90th percentile value
            
        Returns:
            Tuple of (mu, sigma) for lognormal distribution
            
        Raises:
            ValueError: If percentiles are invalid
        """
        if p50 <= 0 or p90 <= 0 or p90 <= p50:
            raise ValueError("Require 0 < p50 < p90 for lognormal")
        
        z90 = 1.2815515655446004  # standard normal quantile for 0.9
        mu = math.log(p50)
        sigma = (math.log(p90) - math.log(p50)) / z90
        
        return mu, sigma

Testing Guidelines
~~~~~~~~~~~~~~~~~

1. **Unit tests**: Test individual functions and classes
2. **Integration tests**: Test complete workflows
3. **Edge cases**: Test boundary conditions and error cases
4. **Performance tests**: Test performance for large simulations

Example test:

.. code-block:: python

    import pytest
    from src.core.config import convert_percentiles_to_log_params

    def test_convert_percentiles_to_log_params():
        """Test percentile to lognormal parameter conversion."""
        # Test valid inputs
        mu, sigma = convert_percentiles_to_log_params(100, 200)
        assert isinstance(mu, float)
        assert isinstance(sigma, float)
        assert sigma > 0
        
        # Test invalid inputs
        with pytest.raises(ValueError):
            convert_percentiles_to_log_params(0, 100)
        
        with pytest.raises(ValueError):
            convert_percentiles_to_log_params(200, 100)

Documentation Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

1. **API documentation**: Document all public APIs
2. **User guides**: Clear usage instructions
3. **Examples**: Practical usage examples
4. **Architecture docs**: System design documentation

Example docstring:

.. code-block:: python

    def run_simulation(
        mode: str,
        sim_seconds: float,
        warmup_seconds: float,
        random_seed: int,
        arrival_rate_per_s: float,
        prompt_lognormal: Tuple[float, float, int],
        output_lognormal: Tuple[float, float, int],
        mono_params: Optional[Tuple[int, float, float]] = None,
        disagg_params: Optional[Tuple[int, int, float, float]] = None,
    ) -> Tuple[Metrics, dict]:
        """
        Run a TTFT simulation with specified parameters.
        
        Args:
            mode: Simulation mode ('mono' or 'disagg')
            sim_seconds: Simulation duration in seconds
            warmup_seconds: Warmup period in seconds
            random_seed: Random seed for reproducibility
            arrival_rate_per_s: Poisson arrival rate
            prompt_lognormal: (mean, sigma, min_value) for prompt tokens
            output_lognormal: (mean, sigma, min_value) for output tokens
            mono_params: (num_gpus, prefill_rate, decode_rate) for monolithic mode
            disagg_params: (prefill_gpus, decode_gpus, prefill_rate, decode_rate) for disaggregated mode
            
        Returns:
            Tuple of (metrics, stats) where metrics contains raw data and stats contains summary statistics
            
        Raises:
            ValueError: If parameters are invalid
            AssertionError: If mode-specific parameters are missing
        """

Issue Reporting
--------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, please include:

1. **Environment**: Python version, OS, dependencies
2. **Reproduction**: Steps to reproduce the issue
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error messages and tracebacks

Example bug report:

```markdown
## Bug Description
Simulation crashes when using p50_p90 mode with invalid percentiles.

## Environment
- Python: 3.9.7
- OS: Ubuntu 20.04
- Dependencies: simpy==4.1.1, numpy==2.0.2

## Steps to Reproduce
1. Create config with p50_p90 mode
2. Set p50=200, p90=100 (invalid)
3. Run simulation

## Expected Behavior
Should raise ValueError with clear error message.

## Actual Behavior
Simulation crashes with cryptic error.

## Error Message
```
Traceback (most recent call last):
  File "src/cli/run.py", line 45, in simulate
    ...
ValueError: Invalid percentiles
```
```

Feature Requests
~~~~~~~~~~~~~~~~

When requesting features, please include:

1. **Use case**: Why you need this feature
2. **Proposed solution**: How you think it should work
3. **Alternatives**: Any alternative approaches considered
4. **Impact**: How this affects existing functionality

Community Guidelines
-------------------

Code of Conduct
~~~~~~~~~~~~~~~

1. **Be respectful**: Treat all contributors with respect
2. **Be constructive**: Provide constructive feedback
3. **Be inclusive**: Welcome contributors from all backgrounds
4. **Be patient**: Allow time for review and discussion

Communication
~~~~~~~~~~~~~

1. **GitHub issues**: Use issues for discussions and bug reports
2. **Pull requests**: Use PRs for code contributions
3. **Documentation**: Keep documentation up to date
4. **Examples**: Provide examples for new features

Getting Help
-----------

If you need help:

1. **Check documentation**: Read the user guide and API reference
2. **Search issues**: Look for similar issues on GitHub
3. **Ask questions**: Open an issue for questions
4. **Join discussions**: Participate in project discussions

Thank you for contributing to the LLM Simulator!
