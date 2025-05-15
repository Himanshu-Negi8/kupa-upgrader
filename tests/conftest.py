"""
Test configuration and fixtures for KuPa tests
"""

import os
import pytest
import tempfile
import shutil
import yaml


@pytest.fixture
def sample_k8s_resource():
    """Create a sample K8s resource for testing."""
    # Import at runtime to avoid circular imports
    from kupa.analyzer import K8sResource
    
    content = {
        "apiVersion": "apps/v1beta2",  # Deprecated version
        "kind": "Deployment",
        "metadata": {
            "name": "test-app",
            "namespace": "default"
        },
        "spec": {
            "replicas": 3,
            "selector": {
                "matchLabels": {
                    "app": "test-app"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "test-app"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "test-app",
                            "image": "nginx:latest",
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    
    return K8sResource(
        kind="Deployment",
        api_version="apps/v1beta2",
        name="test-app",
        namespace="default",
        file_path="/tmp/test-deployment.yaml",
        content=content
    )


@pytest.fixture
def temp_k8s_dir():
    """Create a temporary directory with Kubernetes YAML files."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Add some sample YAML files
    # Deprecated Deployment API version
    deployment = {
        "apiVersion": "apps/v1beta2",
        "kind": "Deployment",
        "metadata": {
            "name": "test-deployment",
            "namespace": "default"
        },
        "spec": {
            "replicas": 3,
            "selector": {
                "matchLabels": {
                    "app": "test"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "test"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "test-container",
                            "image": "nginx:latest"
                        }
                    ]
                }
            }
        }
    }
    
    # Deprecated Ingress API version
    ingress = {
        "apiVersion": "extensions/v1beta1",
        "kind": "Ingress",
        "metadata": {
            "name": "test-ingress",
            "namespace": "default"
        },
        "spec": {
            "rules": [
                {
                    "host": "example.com",
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "backend": {
                                    "serviceName": "test-service",
                                    "servicePort": 80
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    # Valid ConfigMap (no breaking changes)
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "test-configmap",
            "namespace": "default"
        },
        "data": {
            "key1": "value1",
            "key2": "value2"
        }
    }
    
    # Write YAML files
    with open(os.path.join(temp_dir, "deployment.yaml"), "w") as f:
        yaml.dump(deployment, f)
        
    with open(os.path.join(temp_dir, "ingress.yaml"), "w") as f:
        yaml.dump(ingress, f)
        
    with open(os.path.join(temp_dir, "configmap.yaml"), "w") as f:
        yaml.dump(configmap, f)
        
    yield temp_dir
    
    # Clean up
    shutil.rmtree(temp_dir)
