"""
Tests for the configuration module.
"""

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, mock_open

from kupa.config import load_config, get_kubernetes_version, _update_dict_recursive


def test_update_dict_recursive():
    """Test recursive dictionary update."""
    target = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        }
    }
    source = {
        "b": {
            "c": 4
        },
        "e": 5
    }
    
    _update_dict_recursive(target, source)
    
    assert target == {
        "a": 1,
        "b": {
            "c": 4,
            "d": 3
        },
        "e": 5
    }


def test_load_config_default():
    """Test loading default configuration when no file is provided."""
    # Mock so it doesn't find any config files
    with patch('os.path.exists', return_value=False):
        config = load_config()
    
    # Check if default values are set
    assert "kubernetes_versions" in config
    assert "ai_model" in config
    assert "external_sources" in config
    assert "github" in config


def test_load_config_custom():
    """Test loading custom configuration."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "kubernetes_versions": {
                "latest": "v1.29.0",
                "custom": "v1.20.0"
            }
        }, f)
    
    try:
        # Load the config
        config = load_config(f.name)
        
        # Check if our custom values are set
        assert config["kubernetes_versions"]["latest"] == "v1.29.0"
        assert config["kubernetes_versions"]["custom"] == "v1.20.0"
        
        # Check if other default values are still present
        assert "ai_model" in config
        assert "external_sources" in config
    finally:
        # Clean up
        os.unlink(f.name)


def test_get_kubernetes_version():
    """Test getting Kubernetes version from alias or direct version."""
    # Test with alias
    with patch('kupa.config.load_config', return_value={
        "kubernetes_versions": {
            "latest": "v1.28.0",
            "lts": "v1.24.0"
        }
    }):
        assert get_kubernetes_version("latest") == "v1.28.0"
        assert get_kubernetes_version("lts") == "v1.24.0"
        
        # Test with direct version
        assert get_kubernetes_version("v1.22.0") == "v1.22.0"
