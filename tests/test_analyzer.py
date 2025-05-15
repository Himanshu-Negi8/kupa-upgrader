"""
Tests for the analyzer module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the functions directly to avoid circular imports during test execution
from kupa.analyzer import (
    analyze_directory, parse_k8s_yaml, find_yaml_files, check_for_breaking_changes,
    BreakingChange
)


def test_find_yaml_files(temp_k8s_dir):
    """Test finding YAML files in a directory."""
    yaml_files = find_yaml_files(temp_k8s_dir)
    
    # Check if we found the expected files
    assert len(yaml_files) == 3
    assert any(f.endswith("deployment.yaml") for f in yaml_files)
    assert any(f.endswith("ingress.yaml") for f in yaml_files)
    assert any(f.endswith("configmap.yaml") for f in yaml_files)


def test_parse_k8s_yaml(temp_k8s_dir):
    """Test parsing Kubernetes YAML files."""
    yaml_files = find_yaml_files(temp_k8s_dir)
    
    # Find the deployment.yaml file
    deployment_file = next(f for f in yaml_files if f.endswith("deployment.yaml"))
    resources = parse_k8s_yaml(deployment_file)
    
    # Check if we parsed the deployment correctly
    assert len(resources) == 1
    assert resources[0].kind == "Deployment"
    assert resources[0].api_version == "apps/v1beta2"
    assert resources[0].name == "test-deployment"
    assert resources[0].namespace == "default"


@patch('kupa.mcp.external_fetcher.fetch_from_k8s_docs')
@patch('kupa.mcp.model_client.query_model_for_changes')
def test_check_for_breaking_changes_model_confident(mock_query, mock_fetch, sample_k8s_resource):
    """Test checking for breaking changes with a confident model."""
    # Mock the model to return a breaking change
    mock_query.return_value = {
        "is_confident": True,
        "has_breaking_change": True,
        "change_type": "API_DEPRECATED",
        "description": "apps/v1beta2 is deprecated in v1.16+",
        "recommended_action": "Use apps/v1 instead",
        "updated_content": {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-app",
                "namespace": "default"
            }
        }
    }
    
    # Set up environment for OpenAI API key
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        breaking_change = check_for_breaking_changes(sample_k8s_resource, "v1.25")
    
        # Check if we detected the breaking change
        assert breaking_change is not None
        assert breaking_change.change_type == "API_DEPRECATED"
        assert breaking_change.resource.api_version == "apps/v1beta2"
        assert breaking_change.updated_content["apiVersion"] == "apps/v1"
        
        # Make sure we didn't need to fall back to external sources
        mock_query.assert_called_once()
        mock_fetch.assert_not_called()


@patch('kupa.mcp.external_fetcher.fetch_from_k8s_docs')
@patch('kupa.mcp.model_client.query_model_for_changes')
def test_check_for_breaking_changes_model_not_confident(mock_query, mock_fetch, sample_k8s_resource):
    """Test checking for breaking changes when model is not confident."""
    # Mock the model to return not confident
    mock_query.return_value = {
        "is_confident": False,
        "has_breaking_change": False,
        "description": "I'm not sure about this resource",
    }
    
    # Mock the external fetcher to return a breaking change
    mock_fetch.return_value = {
        "found_breaking_change": True,
        "change_type": "API_DEPRECATED",
        "description": "apps/v1beta2 was deprecated in Kubernetes v1.9 and removed in v1.16",
        "recommended_action": "Use apps/v1 instead",
        "updated_content": {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-app",
                "namespace": "default"
            }
        }
    }
    
    # Set up environment for OpenAI API key
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        breaking_change = check_for_breaking_changes(sample_k8s_resource, "v1.25")
        
        # Check if we detected the breaking change
        assert breaking_change is not None
        assert breaking_change.change_type == "API_DEPRECATED"
        assert breaking_change.resource.api_version == "apps/v1beta2"
        
        # Make sure we called both the model and the external fetcher
        mock_query.assert_called_once()
        mock_fetch.assert_called_once()


@patch('kupa.mcp.external_fetcher.fetch_from_k8s_docs')
@patch('kupa.analyzer.check_for_breaking_changes')
def test_analyze_directory(mock_check, mock_fetch, temp_k8s_dir):
    """Test analyzing a directory for breaking changes."""
    # Mock check_for_breaking_changes to return a breaking change for specific resources
    def mock_check_side_effect(resource, version):
        if resource.api_version == "apps/v1beta2":
            return BreakingChange(
                resource=resource,
                change_type="API_DEPRECATED",
                description="apps/v1beta2 is deprecated",
                recommended_action="Use apps/v1 instead",
                updated_content={"apiVersion": "apps/v1"}
            )
        elif resource.api_version == "extensions/v1beta1":
            return BreakingChange(
                resource=resource,
                change_type="API_DEPRECATED",
                description="extensions/v1beta1 is deprecated",
                recommended_action="Use networking.k8s.io/v1 instead",
                updated_content={"apiVersion": "networking.k8s.io/v1"}
            )
        else:
            return None
    
    mock_check.side_effect = mock_check_side_effect
    
    # Analyze the directory
    results = analyze_directory(temp_k8s_dir, "v1.25")
    
    # Check if we found the expected breaking changes
    assert len(results) == 2
    
    # Check if the correct number of resources were analyzed
    assert mock_check.call_count == 3  # 3 resources total
    
    # Check if the API versions are set correctly in the results
    api_versions = [r.resource.api_version for r in results]
    assert "apps/v1beta2" in api_versions
    assert "extensions/v1beta1" in api_versions
