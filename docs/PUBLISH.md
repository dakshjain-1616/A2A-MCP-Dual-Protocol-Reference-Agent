# Publishing Guide

## Preparing for Release

### Version Bump

```python
# Update version in pyproject.toml
[project]
version = "0.1.0"  # → "0.2.0"

# Update version in __init__.py
__version__ = "0.2.0"
```

### Changelog

Create or update `CHANGELOG.md`:

```markdown
## [0.1.0] - 2024-01-15

### Added
- Initial release
- A2A protocol implementation
- MCP server support
- DeepSeek integration
- Gradio UI
- CLI interface
```

### Final Checks

```bash
# Run full test suite
make test

# Run linting
make lint

# Check types
mypy src/a2a_mcp_agent

# Clean build artifacts
make clean
```

## Building the Package

### Install Build Tools

```bash
pip install build twine
```

### Build

```bash
# Build source and wheel
python -m build

# Output in dist/
ls dist/
# a2a_mcp_reference_agent-0.1.0.tar.gz
# a2a_mcp_reference_agent-0.1.0-py3-none-any.whl
```

### Verify

```bash
# Check package
twine check dist/*

# Should output:
# Checking dist/*.tar.gz: PASSED
# Checking dist/*.whl: PASSED
```

## Publishing to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ a2a-mcp-reference-agent
```

### Production PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Install from PyPI
pip install a2a-mcp-reference-agent
```

## Docker Publishing

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
RUN pip install -e .

# Expose ports
EXPOSE 8000 7860

# Run A2A server
CMD ["python", "-m", "a2a_mcp_agent.a2a_server"]
```

### Build and Push

```bash
# Build
docker build -t a2a-mcp-agent:latest .

# Tag
docker tag a2a-mcp-agent:latest username/a2a-mcp-agent:0.1.0
docker tag a2a-mcp-agent:latest username/a2a-mcp-agent:latest

# Push
docker push username/a2a-mcp-agent:0.1.0
docker push username/a2a-mcp-agent:latest
```

## GitHub Release

### Create Tag

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag
git push origin v0.1.0
```

### Release Notes

Create release on GitHub with:

1. Tag: v0.1.0
2. Title: Version 0.1.0
3. Description:

```markdown
## What's New

- Initial release
- A2A protocol support
- MCP server integration
- DeepSeek LLM client

## Installation

```bash
pip install a2a-mcp-reference-agent==0.1.0
```

## Documentation

See [README.md](README.md) for usage instructions.
```

## Documentation Publishing

### MkDocs (Optional)

```bash
# Install
pip install mkdocs mkdocs-material

# Setup
mkdocs new .

# Serve locally
mkdocs serve

# Build
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### ReadTheDocs

Create `.readthedocs.yml`:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - dev

sphinx:
  configuration: docs/conf.py
```

## Post-Publish Verification

### PyPI Installation

```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install a2a-mcp-reference-agent

# Verify
a2a-mcp-agent --help
python -c "import a2a_mcp_agent; print(a2a_mcp_agent.__version__)"
```

### Docker Verification

```bash
# Pull and run
docker run -p 8000:8000 username/a2a-mcp-agent:latest

# Test
curl http://localhost:8000/health
```

## Maintenance

### Security Updates

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade package-name
```

### Deprecation Policy

1. Mark deprecated features with warnings
2. Maintain for 2 minor versions
3. Remove in major version

```python
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated, use new_function",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

## Troubleshooting

### Build Failures

```bash
# Clean and rebuild
make clean
rm -rf build/ dist/ *.egg-info
python -m build
```

### Upload Failures

```bash
# Check credentials
cat ~/.pypirc

# Verify token
pip install keyring
keyring get https://upload.pypi.org/legacy/ __token__
```

### Version Conflicts

```bash
# Check installed version
pip show a2a-mcp-reference-agent

# Force reinstall
pip install --force-reinstall --no-cache-dir a2a-mcp-reference-agent
```

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Documentation](https://docs.pypi.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Docker Hub](https://hub.docker.com/)
