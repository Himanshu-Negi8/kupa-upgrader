# Contributing to KuPa

Thank you for your interest in contributing to KuPa! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/kupa.git
cd kupa
```

2. **Set up a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies:**

```bash
make install-dev  # Alternative: pip install -e ".[dev]"
```

## Running Tests

To run the test suite:

```bash
make test  # Alternative: pytest -xvs tests/
```

## Code Style

We use Black and Flake8 for code formatting and linting:

```bash
# Check code style
make lint

# Format code
make format
```

## Building Documentation

Documentation is built using Sphinx:

```bash
cd docs
make html
```

## Pull Request Process

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Run tests and linting to ensure your code passes
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Environment Variables

For development, you'll need to set the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI model integration
- `GITHUB_TOKEN`: Your GitHub token for creating pull requests

## Project Structure

```
kupa/
├── cli.py               # Command line interface
├── analyzer/            # YAML parsing and analysis
├── mcp/                 # Model Context Protocol implementation
│   ├── model_client.py  # AI model integration
│   └── external_fetcher.py  # K8s docs fetcher
├── github_integration/  # GitHub repo handling
├── output/              # File output handling
└── api/                 # API server implementation
```

## Common Development Tasks

### Adding a New Command

1. Modify `kupa/cli.py` to add your new command
2. Update any related modules that your command depends on
3. Add tests in the `tests/` directory

### Adding a New Feature

1. First, decide which module your feature belongs to
2. Implement the feature in the appropriate module
3. Add tests for your feature
4. Update documentation if necessary

## Running the Server Locally

To run the API server locally:

```bash
python scripts/run_server.py --reload
```

## Docker Development

To build and run with Docker:

```bash
# Build the Docker image
docker build -t kupa .

# Run the Docker container
docker run -p 8080:8080 -e OPENAI_API_KEY=your_key -e GITHUB_TOKEN=your_token kupa server --port 8080
```

Or using Docker Compose:

```bash
docker-compose up
```
