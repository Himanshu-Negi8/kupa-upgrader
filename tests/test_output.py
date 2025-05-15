"""
Tests for the output module.
"""

import os
import yaml
import pytest
from unittest.mock import MagicMock

from kupa.output import generate_timestamped_path, write_yaml_file, write_local_results


def test_generate_timestamped_path(monkeypatch):
    """Test generating a timestamped file path."""
    # Mock datetime to return a fixed timestamp
    class MockDatetime:
        @staticmethod
        def now():
            return MagicMock(strftime=lambda fmt: "20250515123456")
    
    monkeypatch.setattr('kupa.output.datetime', MockDatetime)
    
    # Test with a simple file path
    path = generate_timestamped_path("/tmp/test.yaml")
    assert path == "/tmp/test-updated-20250515123456.yaml"
    
    # Test with a complex file path
    path = generate_timestamped_path("/tmp/dir/subdir/test.yaml")
    assert path == "/tmp/dir/subdir/test-updated-20250515123456.yaml"


def test_write_yaml_file(tmp_path):
    """Test writing YAML content to a file."""
    test_file = os.path.join(tmp_path, "test.yaml")
    content = {"test": "content", "nested": {"key": "value"}}
    
    write_yaml_file(test_file, content)
    
    # Check if the file was created
    assert os.path.exists(test_file)
    
    # Check if the content was written correctly
    with open(test_file, "r") as f:
        loaded = yaml.safe_load(f)
        assert loaded == content


def test_write_local_results(tmp_path, monkeypatch):
    """Test writing local results with breaking changes."""
    # Mock datetime to return a fixed timestamp
    class MockDatetime:
        @staticmethod
        def now():
            return MagicMock(strftime=lambda fmt: "20250515123456")
    
    monkeypatch.setattr('kupa.output.datetime', MockDatetime)
    
    # Create test files
    test_file = os.path.join(tmp_path, "deployment.yaml")
    test_content = {
        "apiVersion": "apps/v1beta2",
        "kind": "Deployment",
        "metadata": {
            "name": "test-app",
            "namespace": "default"
        },
        "spec": {
            "replicas": 3
        }
    }
    
    with open(test_file, "w") as f:
        yaml.dump(test_content, f)
    
    # Create a mock breaking change
    mock_resource = MagicMock(
        kind="Deployment",
        api_version="apps/v1beta2",
        name="test-app",
        namespace="default",
        file_path=test_file,
        content=test_content
    )
    
    updated_content = test_content.copy()
    updated_content["apiVersion"] = "apps/v1"
    
    mock_change = MagicMock(
        resource=mock_resource,
        change_type="API_DEPRECATED",
        description="apps/v1beta2 is deprecated",
        recommended_action="Use apps/v1 instead",
        updated_content=updated_content
    )
    
    # Call write_local_results
    write_local_results(str(tmp_path), [mock_change])
    
    # Check if the new file was created
    new_file = os.path.join(tmp_path, "deployment-updated-20250515123456.yaml")
    assert os.path.exists(new_file)
    
    # Check if the diff file was created
    diff_file = new_file + ".diff.txt"
    assert os.path.exists(diff_file)
    
    # Check if the content was updated correctly
    with open(new_file, "r") as f:
        updated = yaml.safe_load(f)
        assert updated["apiVersion"] == "apps/v1"
    
    # Check if the diff file contains the expected content
    with open(diff_file, "r") as f:
        diff_content = f.read()
        assert "apps/v1beta2" in diff_content
        assert "API_DEPRECATED" in diff_content
