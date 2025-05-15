# KuPa - Kubernetes Upgrade Path Analyzer

KuPa is a tool for detecting breaking changes in Kubernetes YAML resources when upgrading to a newer Kubernetes version. It uses both AI models and official Kubernetes documentation to identify breaking changes and suggest fixes.

## Features

- Scan local directories for Kubernetes YAML resources
- Clone and analyze GitHub repositories
- Create pull requests with fixes for GitHub repositories
- Output updated files with timestamps for local directories
- Use AI models to detect breaking changes with fallback to official Kubernetes docs
- Run as a CLI tool or API server

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/kupa.git
cd kupa

# Run the install script
./install.sh
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kupa.git
cd kupa

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Development Installation

```bash
# For development with testing tools
./install.sh --dev
# Or manually:
pip install -e ".[dev]"
```

### Using Docker

```bash
# Build the Docker image
docker build -t kupa .

# Run the Docker container
docker run -it kupa --help
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI model integration
- `GITHUB_TOKEN`: Your GitHub token for creating pull requests

## Usage

### CLI Tool

#### Analyze Local Directory

```bash
# Analyze a local directory
kupa analyze-local --path /path/to/kubernetes/manifests --kube-version v1.25
```

#### Analyze GitHub Repository

```bash
# Analyze a GitHub repository
kupa analyze-github --repo owner/repo --kube-version v1.25

# Create a pull request with fixes
kupa analyze-github --repo owner/repo --kube-version v1.25 --create-pr
```

#### Run as Server

```bash
# Run the API server
kupa server --port 8080
```

### API Endpoints

When running in server mode, the following API endpoints are available:

- `GET /`: Root endpoint
- `POST /analyze/upload`: Analyze uploaded YAML files
- `POST /analyze/github`: Analyze a GitHub repository

#### API Examples

**Analyze uploaded files:**

```bash
curl -X POST -F "files=@deployment.yaml" -F "kube-version=v1.25" http://localhost:8080/analyze/upload
```

**Analyze GitHub repository:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"repo_url": "owner/repo", "kube_version": "v1.25", "create_pr": false}' http://localhost:8080/analyze/github
```

## Architecture

KuPa is built on the Model Context Protocol (MCP) concept and includes:

1. **YAML Scanner**: Recursively finds and parses Kubernetes YAML files.
2. **AI Model Client**: Sends resource info to an AI model and receives breaking change info.
3. **External Fetcher**: Scrapes or queries Kubernetes official docs if the AI model is unsure.
4. **File Updater**: Applies suggested changes and writes new files (with timestamp) or commits to a branch.
5. **PR Creator**: For GitHub repos, automates branch, commit, and PR creation.

## Directory Structure

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

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=kupa tests/
```

### Code Formatting

```bash
# Check code style
make lint

# Format code
make format
```

### Building Documentation

```bash
cd docs
make html
```

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details.

## License

MIT
