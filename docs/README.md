# LLM Simulator Documentation

This directory contains the documentation for the LLM Simulator project.

## Building Documentation

### Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Building HTML Documentation

```bash
make html
```

The built documentation will be available in `build/html/index.html`.

### Building Other Formats

```bash
# PDF documentation
make latexpdf

# EPUB documentation
make epub

# Single HTML file
make singlehtml
```

## Documentation Structure

- `source/`: Source files for the documentation
  - `index.rst`: Main documentation index
  - `installation.rst`: Installation guide
  - `quickstart.rst`: Quick start guide
  - `user_guide.rst`: User guide
  - `api_reference.rst`: API reference
  - `examples.rst`: Examples and tutorials
  - `theory.rst`: Theoretical background
  - `architecture.rst`: System architecture
  - `contributing.rst`: Contributing guidelines
- `build/`: Built documentation (generated)
- `requirements.txt`: Documentation dependencies

## Development

### Adding New Documentation

1. Create a new `.rst` file in `source/`
2. Add it to the toctree in `source/index.rst`
3. Build and test the documentation

### Updating API Documentation

The API documentation is automatically generated from docstrings. To update:

1. Update docstrings in the source code
2. Rebuild the documentation: `make html`

### Testing Documentation

```bash
# Check for broken links
make linkcheck

# Check for spelling errors
make spelling
```

## ReadTheDocs Integration

This documentation is configured for ReadTheDocs. The main configuration is in `source/conf.py`.

### Local ReadTheDocs Build

To test the ReadTheDocs build locally:

```bash
# Install readthedocs-build
pip install readthedocs-build

# Build documentation
readthedocs-build
```

## Contributing

When contributing to the documentation:

1. Follow the existing style and structure
2. Use clear, concise language
3. Include examples where appropriate
4. Test the documentation build
5. Update the table of contents if needed

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure the source code is in the Python path
2. **Build errors**: Check that all dependencies are installed
3. **Missing modules**: Ensure all modules are properly documented

### Getting Help

If you encounter issues:

1. Check the Sphinx documentation
2. Look at existing documentation files
3. Ask for help in the project issues
