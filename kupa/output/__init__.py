"""
Output module for writing results to files with timestamps.
"""

import os
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional

from kupa.analyzer import BreakingChange

# Initialize the logger
logger = logging.getLogger('kupa.output')

def write_yaml_file(file_path: str, content: Dict[str, Any]) -> None:
    """
    Write a dictionary as YAML to a file.
    
    Args:
        file_path: The file path to write to
        content: The dictionary to write as YAML
    """
    with open(file_path, 'w') as f:
        yaml.dump(content, f, default_flow_style=False)
        

def generate_timestamped_path(original_path: str) -> str:
    """
    Generate a timestamped version of a file path.
    
    Args:
        original_path: The original file path
        
    Returns:
        The new file path with a timestamp
    """
    dir_name = os.path.dirname(original_path)
    file_name = os.path.basename(original_path)
    name, ext = os.path.splitext(file_name)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_name = f"{name}-updated-{timestamp}{ext}"
    
    return os.path.join(dir_name, new_name)


def write_local_results(directory: str, breaking_changes: List[BreakingChange]) -> None:
    """
    Write the results of the analysis to local files with timestamps.
    
    Args:
        directory: The base directory
        breaking_changes: List of breaking changes
    """
    if not breaking_changes:
        logger.info("No breaking changes detected. No files will be written.")
        return
        
    file_changes = {}
    for change in breaking_changes:
        file_path = change.resource.file_path
        
        # Group changes by file path
        if file_path not in file_changes:
            file_changes[file_path] = []
        file_changes[file_path].append(change)
    
    # Process each file that has changes
    for file_path, changes in file_changes.items():
        # Read the original YAML file
        with open(file_path, 'r') as f:
            documents = list(yaml.safe_load_all(f))
            
        # Apply changes to the documents
        for change in changes:
            resource = change.resource
            for i, doc in enumerate(documents):
                # Find the matching document in the file
                if is_same_resource(doc, resource.content):
                    # Replace with updated content
                    documents[i] = change.updated_content
                    break
        
        # Write the updated documents to a new timestamped file
        new_file_path = generate_timestamped_path(file_path)
        with open(new_file_path, 'w') as f:
            yaml.dump_all(documents, f, default_flow_style=False)
            
        logger.info(f"Updated file written to: {new_file_path}")
        
        # Create a diff file with explanations
        diff_path = f"{new_file_path}.diff.txt"
        with open(diff_path, 'w') as f:
            f.write(f"# Changes made to {os.path.basename(file_path)}\n")
            f.write(f"# Original file: {file_path}\n")
            f.write(f"# Updated file: {new_file_path}\n\n")
            
            for change in changes:
                f.write(f"## Resource: {change.resource.kind}/{change.resource.api_version} '{change.resource.name}'\n")
                f.write(f"Change type: {change.change_type}\n")
                f.write(f"Description: {change.description}\n")
                f.write(f"Recommended action: {change.recommended_action}\n\n")
                
        logger.info(f"Explanation file written to: {diff_path}")


def is_same_resource(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> bool:
    """
    Check if two Kubernetes resource documents are the same.
    
    This is a simplified check that just looks at kind, apiVersion, and metadata.name
    
    Args:
        doc1: First document
        doc2: Second document
        
    Returns:
        True if they represent the same resource, False otherwise
    """
    if not isinstance(doc1, dict) or not isinstance(doc2, dict):
        return False
        
    # Check kind and apiVersion
    if doc1.get('kind') != doc2.get('kind') or doc1.get('apiVersion') != doc2.get('apiVersion'):
        return False
        
    # Check metadata.name
    metadata1 = doc1.get('metadata', {})
    metadata2 = doc2.get('metadata', {})
    
    if metadata1.get('name') != metadata2.get('name'):
        return False
        
    # Optionally check namespace
    if metadata1.get('namespace') != metadata2.get('namespace'):
        return False
        
    return True
