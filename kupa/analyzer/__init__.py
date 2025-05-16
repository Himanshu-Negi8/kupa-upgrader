"""
Analyzer module for scanning Kubernetes YAML files and detecting breaking changes.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from packaging.version import Version

# Import these later to avoid circular imports
# from kupa.mcp.model_client import query_model_for_changes
# from kupa.mcp.external_fetcher import fetch_from_k8s_docs

logger = logging.getLogger('kupa.analyzer')

class K8sResource:
    """Class representing a Kubernetes resource found in a YAML file."""
    
    def __init__(self, kind: str, api_version: str, name: str, namespace: Optional[str], 
                 file_path: str, content: Dict[str, Any]):
        self.kind = kind
        self.api_version = api_version
        self.name = name
        self.namespace = namespace
        self.file_path = file_path
        self.content = content

    def __str__(self):
        if self.namespace:
            return f"{self.kind}/{self.api_version} '{self.namespace}/{self.name}'"
        return f"{self.kind}/{self.api_version} '{self.name}'"


class BreakingChange:
    """Class representing a breaking change detected in a Kubernetes resource."""
    
    def __init__(self, resource: K8sResource, change_type: str, description: str, 
                 recommended_action: str, updated_content: Dict[str, Any]):
        self.resource = resource
        self.change_type = change_type  # e.g., 'API_DEPRECATED', 'FIELD_REMOVED', etc.
        self.description = description
        self.recommended_action = recommended_action
        self.updated_content = updated_content


def find_yaml_files(path: str) -> List[str]:
    """Find all YAML files in a directory recursively or return the path if it's a file."""
    yaml_files = []
    
    # Check if path is a file
    if os.path.isfile(path):
        if path.endswith(('.yaml', '.yml')):
            yaml_files.append(path)
        return yaml_files
    
    # If path is a directory, walk through it
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(os.path.join(root, file))
    return yaml_files


def parse_k8s_yaml(file_path: str) -> List[K8sResource]:
    """Parse a YAML file and extract Kubernetes resources."""
    resources = []
    
    try:
        with open(file_path, 'r') as f:
            # Parse multi-document YAML file
            docs = list(yaml.safe_load_all(f))
        
        for doc in docs:
            if not doc:
                continue
                
            # Check if this is a Kubernetes resource
            if not (isinstance(doc, dict) and doc.get('kind') and doc.get('apiVersion')):
                continue
                
            kind = doc.get('kind')
            api_version = doc.get('apiVersion')
            
            # Extract name and namespace
            metadata = doc.get('metadata', {})
            name = metadata.get('name', 'unnamed')
            namespace = metadata.get('namespace')
            
            resource = K8sResource(
                kind=kind,
                api_version=api_version,
                name=name,
                namespace=namespace,
                file_path=file_path,
                content=doc
            )
            resources.append(resource)
            
    except Exception as e:
        logger.warning(f"Error parsing YAML file {file_path}: {e}")
        
    return resources


# Add a static fallback for deprecated/removed API versions
DEPRECATED_API_VERSIONS = {
    # Deployments
    ("Deployment", "apps/v1beta1"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "apps/v1beta1 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    ("Deployment", "apps/v1beta2"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "apps/v1beta2 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    ("Deployment", "extensions/v1beta1"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "extensions/v1beta1 for Deployments was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    
    # StatefulSets
    ("StatefulSet", "apps/v1beta1"): {
        "removed_in": "v1.16.0", 
        "replacement": "apps/v1",
        "description": "apps/v1beta1 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    ("StatefulSet", "apps/v1beta2"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "apps/v1beta2 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    
    # DaemonSets
    ("DaemonSet", "apps/v1beta2"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "apps/v1beta2 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    ("DaemonSet", "extensions/v1beta1"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "extensions/v1beta1 for DaemonSets was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    
    # ReplicaSets
    ("ReplicaSet", "apps/v1beta2"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "apps/v1beta2 was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    ("ReplicaSet", "extensions/v1beta1"): {
        "removed_in": "v1.16.0",
        "replacement": "apps/v1",
        "description": "extensions/v1beta1 for ReplicaSets was removed in Kubernetes v1.16. Use apps/v1 instead."
    },
    
    # Ingress
    ("Ingress", "extensions/v1beta1"): {
        "removed_in": "v1.22.0",
        "replacement": "networking.k8s.io/v1",
        "description": "extensions/v1beta1 was removed in Kubernetes v1.22. Use networking.k8s.io/v1 instead."
    },
    ("Ingress", "networking.k8s.io/v1beta1"): {
        "removed_in": "v1.22.0",
        "replacement": "networking.k8s.io/v1",
        "description": "networking.k8s.io/v1beta1 was removed in Kubernetes v1.22. Use networking.k8s.io/v1 instead."
    },
    
    # NetworkPolicies
    ("NetworkPolicy", "extensions/v1beta1"): {
        "removed_in": "v1.16.0",
        "replacement": "networking.k8s.io/v1",
        "description": "extensions/v1beta1 for NetworkPolicies was removed in Kubernetes v1.16. Use networking.k8s.io/v1 instead."
    },
    
    # PodSecurityPolicies
    ("PodSecurityPolicy", "extensions/v1beta1"): {
        "removed_in": "v1.21.0",
        "replacement": "policy/v1beta1",
        "description": "extensions/v1beta1 for PodSecurityPolicies was removed in Kubernetes v1.21. Use policy/v1beta1 instead."
    },
    ("PodSecurityPolicy", "policy/v1beta1"): {
        "removed_in": "v1.25.0", 
        "replacement": "None - PSPs are removed entirely",
        "description": "PodSecurityPolicy was entirely removed in Kubernetes v1.25. Use Pod Security Standards and Admission instead."
    },
    
    # CRDs
    ("CustomResourceDefinition", "apiextensions.k8s.io/v1beta1"): {
        "removed_in": "v1.22.0",
        "replacement": "apiextensions.k8s.io/v1",
        "description": "apiextensions.k8s.io/v1beta1 was removed in Kubernetes v1.22. Use apiextensions.k8s.io/v1 instead."
    }
}

def check_for_breaking_changes(resource: K8sResource, target_k8s_version: str) -> Optional[BreakingChange]:
    """
    Check if a Kubernetes resource has breaking changes in the target version.
    
    This function checks for breaking changes using AI models if available,
    with fallback to external K8s documentation. If no API key is available,
    it directly uses the external documentation.
    """
    # Import here to avoid circular imports
    import os
    from kupa.mcp.model_client import query_model_for_changes
    from kupa.mcp.external_fetcher import fetch_from_k8s_docs
    
    # Check if we have an OpenAI API key (required for model queries)
    api_key_available = os.environ.get('OPENAI_API_KEY') not in [None, '', 'your-api-key']
    
    if os.environ.get("MODEL_PROVIDER") == "ollama":
        logger.info("Using Ollama model provider.")

        try:
            model_result = query_model_for_changes(resource, target_k8s_version)
            if model_result.get('is_confident', False) and model_result.get('has_breaking_change', False):
                logger.info(f"Ollama model found breaking change for {resource}")
                return BreakingChange(
                    resource=resource,
                    change_type=model_result.get('change_type'),
                    description=model_result.get('description'),
                    recommended_action=model_result.get('recommended_action'),
                    updated_content=model_result.get('updated_content')
                )
        except Exception as e:
            logger.warning(f"Error querying Ollama model: {e}. Falling back to external sources.")

    # If API key is available, first try with the AI model
    if api_key_available:
        logger.info(f"API key available. Querying AI model for {resource}")
        try:
            model_result = query_model_for_changes(resource, target_k8s_version)
            
            # If model is confident about a breaking change, use its results
            if model_result.get('is_confident', False) and model_result.get('has_breaking_change', False):
                logger.info(f"AI model found breaking change for {resource}")
                return BreakingChange(
                    resource=resource,
                    change_type=model_result.get('change_type'),
                    description=model_result.get('description'),
                    recommended_action=model_result.get('recommended_action'),
                    updated_content=model_result.get('updated_content')
                )
        except Exception as e:
            logger.warning(f"Error querying AI model: {e}. Falling back to external sources.")
            # Continue to external sources if model query fails
    
    # Always check external K8s documentation
    logger.info(f"Checking external K8s documentation for {resource}")
    external_result = fetch_from_k8s_docs(resource, target_k8s_version)
    
    if external_result.get('found_breaking_change'):
        logger.info(f"External sources found breaking change for {resource}")
        return BreakingChange(
            resource=resource,
            change_type=external_result.get('change_type'),
            description=external_result.get('description'),
            recommended_action=external_result.get('recommended_action'),
            updated_content=external_result.get('updated_content')
        )
    
    # Static fallback: check for known deprecated/removed API versions
    key = (resource.kind, resource.api_version)
    if key in DEPRECATED_API_VERSIONS:
        logger.info(f"Checking static fallback for {key}")  
        info = DEPRECATED_API_VERSIONS[key]
        if Version(target_k8s_version.lstrip('v')) >= Version(info["removed_in"].lstrip('v')):
            updated_content = resource.content.copy()
            updated_content["apiVersion"] = info["replacement"]
            return BreakingChange(
                resource=resource,
                change_type="API_REMOVED",
                description=info["description"],
                recommended_action=f"Update apiVersion to {info['replacement']}",
                updated_content=updated_content
            )
    
    # No breaking change found
    return None


def analyze_directory(directory_path: str, target_k8s_version: str) -> List[BreakingChange]:
    """
    Analyze a directory for Kubernetes resources and check for breaking changes.
    
    Args:
        directory_path: Path to the directory containing Kubernetes YAML files
        target_k8s_version: Target Kubernetes version to check against
        
    Returns:
        List of breaking changes detected
    """
    logger.info(f"Analyzing directory: {directory_path}")
    yaml_files = find_yaml_files(directory_path)
    logger.info(f"Found {len(yaml_files)} YAML files")
    
    all_resources = []
    for yaml_file in yaml_files:
        resources = parse_k8s_yaml(yaml_file)
        all_resources.extend(resources)
    
    logger.info(f"Found {len(all_resources)} Kubernetes resources")
    
    # Check each resource for breaking changes
    breaking_changes = []
    for resource in all_resources:
        breaking_change = check_for_breaking_changes(resource, target_k8s_version)
        if breaking_change:
            logger.info(f"Found breaking change in {resource}")
            breaking_changes.append(breaking_change)
    
    logger.info(f"Found {len(breaking_changes)} breaking changes")
    return breaking_changes
