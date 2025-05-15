#!/usr/bin/env python3
"""
Example script showing how to use KuPa programmatically.
"""

import os
import sys
import logging

from kupa.analyzer import analyze_directory
from kupa.output import write_local_results
from kupa.config import load_config, get_kubernetes_version

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('kupa-example')

def main():
    # Print banner
    print("KuPa - Kubernetes Breaking Changes Analyzer")
    print("------------------------------------------")
    
    # Load configuration
    config = load_config()
    
    # Get Kubernetes version
    kube_version = get_kubernetes_version("latest")
    logger.info(f"Using Kubernetes version: {kube_version}")
    
    # Get examples directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    examples_dir = os.path.join(script_dir, "examples")
    
    if not os.path.exists(examples_dir):
        logger.error(f"Examples directory not found: {examples_dir}")
        sys.exit(1)
        
    logger.info(f"Analyzing Kubernetes resources in: {examples_dir}")
    
    # Analyze the directory
    results = analyze_directory(examples_dir, kube_version)
    
    if not results:
        logger.info("No breaking changes found.")
        return
        
    logger.info(f"Found {len(results)} breaking changes:")
    
    for i, change in enumerate(results, 1):
        resource = change.resource
        logger.info(f"{i}. {resource.kind}/{resource.api_version} '{resource.name}'")
        logger.info(f"   Change Type: {change.change_type}")
        logger.info(f"   Description: {change.description}")
        logger.info(f"   Recommended Action: {change.recommended_action}")
        logger.info("")
        
    # Write updated files
    write_local_results(examples_dir, results)
    logger.info("Updated files have been created with timestamps.")

if __name__ == "__main__":
    main()
