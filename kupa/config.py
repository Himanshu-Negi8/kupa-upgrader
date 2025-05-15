"""
Configuration loader for KuPa.
"""

import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger('kupa.config')

# Default configuration
DEFAULT_CONFIG = {
    "kubernetes_versions": {
        "latest": "v1.28.0",
        "lts": "v1.24.0"
    },
    "ai_model": {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.1,
        "max_tokens": 4000
    },
    "external_sources": {
        "docs_url": "https://kubernetes.io/docs",
        "api_reference_url": "https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/",
        "changelog_url": "https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG"
    },
    "github": {
        "default_branch_prefix": "kupa-k8s-upgrade-",
        "commit_message_template": "Fix Kubernetes breaking changes for version {version}",
        "pr_title_template": "Fix Kubernetes breaking changes for version {version}"
    }
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load KuPa configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file. If None, tries to find it in standard locations.
        
    Returns:
        The loaded configuration as a dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to find configuration file
    if not config_path:
        # Check standard locations
        candidates = [
            os.path.join(os.getcwd(), "kupa.yaml"),
            os.path.join(os.getcwd(), "config", "kupa.yaml"),
            os.path.expanduser("~/.config/kupa.yaml"),
            "/etc/kupa/kupa.yaml"
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                config_path = candidate
                break
    
    # Load configuration if found
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                
                # Update configuration with user settings
                if user_config:
                    _update_dict_recursive(config, user_config)
                    
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Error loading configuration from {config_path}: {e}")
    else:
        logger.info("No configuration file found, using defaults")
    
    return config


def _update_dict_recursive(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Update a dictionary recursively.
    
    Args:
        target: The dictionary to update
        source: The dictionary with updates
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _update_dict_recursive(target[key], value)
        else:
            target[key] = value


def get_kubernetes_version(version: str) -> str:
    """
    Get the actual Kubernetes version from a version alias.
    
    Args:
        version: The version or alias (e.g., 'latest', 'lts')
        
    Returns:
        The actual Kubernetes version
    """
    config = load_config()
    kubernetes_versions = config.get("kubernetes_versions", {})
    
    # Check if it's an alias
    if version.lower() in kubernetes_versions:
        return kubernetes_versions[version.lower()]
        
    # Return as-is if not an alias
    return version
