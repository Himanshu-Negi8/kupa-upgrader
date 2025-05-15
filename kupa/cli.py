#!/usr/bin/env python3
"""
KuPa - Kubernetes Upgrade Path Analyzer
CLI interface for detecting Kubernetes breaking changes in YAML manifests
"""

import click
import logging
import os
import sys
from pathlib import Path

# Import configs first
from kupa.config import load_config, get_kubernetes_version
from kupa.analyzer import analyze_directory
from kupa.output import write_local_results
from kupa.github_integration import clone_repo, create_pull_request
from kupa.api import start_server
# Other imports will be loaded when needed
# This prevents circular imports

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('kupa')

@click.group()
@click.version_option()
def cli():
    """KuPa - Kubernetes Upgrade Path Analyzer

    Tool for detecting breaking changes in Kubernetes YAML resources
    when upgrading to a newer Kubernetes version.
    """
    pass


@cli.command()
@click.option('--path', type=click.Path(exists=True), help='Path to local directory containing Kubernetes YAML files')
@click.option('--kube-version', default='latest', help='Target Kubernetes version to check against')
@click.option('--config', type=click.Path(exists=True), help='Path to the configuration file')
def analyze_local(path, kube_version, config):
    """Analyze local directory for K8s breaking changes."""
    if not path:
        logger.error("Error: --path must be specified")
        sys.exit(1)

    # Load configuration
    load_config(config)
    
    # Get actual Kubernetes version
    actual_kube_version = get_kubernetes_version(kube_version)
    
    abs_path = os.path.abspath(path)
    logger.info(f"Analyzing Kubernetes resources in: {abs_path}")
    logger.info(f"Target Kubernetes version: {actual_kube_version}")
    
    try:
        results = analyze_directory(abs_path, actual_kube_version)
        if results:
            write_local_results(abs_path, results)
            logger.info(f"Analysis complete! Found {len(results)} breaking changes.")
            logger.info("Updated files have been created with timestamps.")
        else:
            logger.info("Analysis complete! No breaking changes found.")
    except Exception as e:
        logger.error(f"Error analyzing directory: {e}")
        sys.exit(1)


@cli.command()
@click.option('--repo', required=True, help='GitHub repository URL (format: owner/repo)')
@click.option('--create-pr', is_flag=True, help='Create a PR for changes')
@click.option('--kube-version', default='latest', help='Target Kubernetes version to check against')
@click.option('--config', type=click.Path(exists=True), help='Path to the configuration file')
def analyze_github(repo, create_pr, kube_version, config):
    """Analyze GitHub repo for K8s breaking changes."""
    # Load configuration
    load_config(config)
    
    # Get actual Kubernetes version
    actual_kube_version = get_kubernetes_version(kube_version)
    
    logger.info(f"Analyzing Kubernetes resources in GitHub repo: {repo}")
    logger.info(f"Target Kubernetes version: {actual_kube_version}")
    
    try:
        # Clone the repo to a temp directory
        temp_dir = clone_repo(repo)
        
        # Analyze the cloned repo
        results = analyze_directory(temp_dir, actual_kube_version)
        
        if not results:
            logger.info("Analysis complete! No breaking changes found.")
            return
            
        if create_pr:
            # Create a new branch, commit changes, and create a PR
            pr_url = create_pull_request(repo, temp_dir, results, actual_kube_version)
            logger.info(f"Pull request created: {pr_url}")
        else:
            # Just output what would change without creating a PR
            logger.info(f"Analysis complete! Found {len(results)} breaking changes.")
            logger.info("Changes detected but PR creation was not requested. Add --create-pr to create a PR.")
            write_local_results(temp_dir, results)
            
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        sys.exit(1)


@cli.command()
@click.option('--port', default=8080, help='Port for server mode')
@click.option('--config', type=click.Path(exists=True), help='Path to the configuration file')
def server(port, config):
    """Run as an API server."""
    # Load configuration
    load_config(config)
    
    logger.info(f"Starting KuPa server on port {port}...")
    start_server(port)


def main():
    """Main entry point for the CLI."""
    # Print banner
    print("KuPa - Kubernetes Breaking Changes Analyzer")
    print("------------------------------------------")
    cli()


if __name__ == "__main__":
    main()
