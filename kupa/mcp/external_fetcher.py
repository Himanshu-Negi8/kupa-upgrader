"""
External fetcher for retrieving Kubernetes breaking changes information from official sources.
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

from kupa.config import load_config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kupa.analyzer import K8sResource

# Initialize the logger
logger = logging.getLogger('kupa.mcp.external_fetcher')

def _fetch_k8s_docs(url: str) -> Optional[str]:
    """
    Fetch content from Kubernetes documentation.
    
    Args:
        url: The URL to fetch from
        
    Returns:
        The content as text, or None if the fetch fails
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Error fetching from {url}: {e}")
        return None


def _fetch_changelog(version: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse Kubernetes changelog for a specific version.
    
    Args:
        version: The Kubernetes version to fetch changelog for
        
    Returns:
        Dictionary containing change information
    """
    # Load configuration
    config = load_config()
    changelog_base_url = config["external_sources"]["changelog_url"]
    
    # Format the version (remove 'v' prefix if present)
    version_num = version.lstrip('v')
    
    try:
        # Try different possible changelog URLs
        changelog_urls = [
            f"{changelog_base_url}/CHANGELOG-{version_num}.md",
            f"{changelog_base_url}/{version_num}/CHANGELOG-{version_num}.md",
            f"https://raw.githubusercontent.com/kubernetes/kubernetes/master/CHANGELOG/CHANGELOG-{version_num}.md"
        ]
        
        changelog_content = None
        for url in changelog_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                changelog_content = response.text
                break
            except:
                continue
                
        if not changelog_content:
            logger.warning(f"Could not fetch changelog for version {version}")
            return None
            
        # Parse the changelog for breaking changes
        changes = {
            "api_changes": [],
            "deprecations": [],
            "removals": [],
            "other_changes": []
        }
        
        # Look for sections indicating breaking changes
        sections = re.split(r'#+\s+', changelog_content)
        for section in sections:
            section_lower = section.lower()
            
            if any(term in section_lower for term in ["deprecat", "breaking", "removal", "api change"]):
                # Extract bullet points
                bullets = re.findall(r'\*\s+([^\n]+)', section)
                
                # Categorize the changes
                for bullet in bullets:
                    if "API" in bullet or "apiVersion" in bullet:
                        changes["api_changes"].append(bullet)
                    elif "deprecat" in bullet.lower():
                        changes["deprecations"].append(bullet)
                    elif "remov" in bullet.lower():
                        changes["removals"].append(bullet)
                    else:
                        changes["other_changes"].append(bullet)
                        
        return changes
        
    except Exception as e:
        logger.warning(f"Error parsing changelog for version {version}: {e}")
        return None


def _check_api_reference(resource: 'K8sResource', target_version: str) -> Optional[Dict[str, Any]]:
    """
    Check Kubernetes API reference for changes to a specific resource.
    
    Args:
        resource: The Kubernetes resource to check
        target_version: The target Kubernetes version
        
    Returns:
        Dictionary containing API reference information
    """
    # Load configuration
    config = load_config()
    api_ref_url = config["external_sources"]["api_reference_url"]
    
    try:
        # Fetch API reference
        content = _fetch_k8s_docs(api_ref_url)
        if not content:
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for the resource kind in the API reference
        resource_section = None
        for section in soup.find_all(['h1', 'h2', 'h3']):
            if resource.kind.lower() in section.text.lower():
                resource_section = section
                break
                
        if not resource_section:
            return None
            
        # Look for version information
        version_info = {
            "current_versions": [],
            "deprecated_versions": [],
            "replacement_version": None
        }
        
        # Find version information in the surrounding text
        for sibling in resource_section.find_next_siblings():
            text = sibling.text.lower()
            
            # Look for version information
            if "version" in text:
                if "deprecated" in text or "removed" in text:
                    # Extract versions using regex
                    versions = re.findall(r'[v\d\.]+\d+', text)
                    version_info["deprecated_versions"].extend(versions)
                elif "use" in text or "replace" in text:
                    # Extract replacement version
                    versions = re.findall(r'[v\d\.]+\d+', text)
                    if versions:
                        version_info["replacement_version"] = versions[0]
                else:
                    # Extract current versions
                    versions = re.findall(r'[v\d\.]+\d+', text)
                    version_info["current_versions"].extend(versions)
                        
        return version_info
        
    except Exception as e:
        logger.warning(f"Error checking API reference: {e}")
        return None


def fetch_from_k8s_docs(resource: 'K8sResource', target_k8s_version: str) -> Dict[str, Any]:
    """
    Fetch information about breaking changes from Kubernetes documentation.
    
    This function checks:
    1. The changelog for the target version
    2. The API reference documentation
    3. The deprecation guide
    
    Args:
        resource: The Kubernetes resource to check
        target_k8s_version: The target Kubernetes version
        
    Returns:
        Dictionary containing:
        - found_breaking_change: Whether a breaking change was found
        - change_type: The type of breaking change
        - description: Description of the breaking change
        - recommended_action: Recommended action to fix it
        - updated_content: Updated resource content
    """
    logger.info(f"Checking external sources for {resource} targeting version {target_k8s_version}")
    
    # Get changelog information
    changelog = _fetch_changelog(target_k8s_version)
    
    # Check API reference
    api_info = _check_api_reference(resource, target_k8s_version)
    
    # Initialize response
    result = {
        "found_breaking_change": False,
        "change_type": None,
        "description": None,
        "recommended_action": None,
        "updated_content": resource.content.copy()
    }
    
    # Check for API version deprecation/removal
    if api_info:
        current_version = resource.api_version
        if current_version in api_info["deprecated_versions"]:
            result.update({
                "found_breaking_change": True,
                "change_type": "API_DEPRECATED",
                "description": f"API version {current_version} is deprecated",
                "recommended_action": f"Use {api_info['replacement_version']} instead" if api_info["replacement_version"]
                                    else "Update to a supported version"
            })
            
            # Update the content with the new API version if available
            if api_info["replacement_version"]:
                updated_content = result["updated_content"]
                updated_content["apiVersion"] = api_info["replacement_version"]
                result["updated_content"] = updated_content
                
    # Check changelog for additional breaking changes
    if changelog:
        resource_kind = resource.kind.lower()
        api_version = resource.api_version.lower()
        
        # Look for relevant changes in the changelog
        for change_type, changes in changelog.items():
            for change in changes:
                change_lower = change.lower()
                
                # Check if the change is relevant to this resource
                if resource_kind in change_lower or api_version in change_lower:
                    # Extract action from the change description
                    action_match = re.search(r'use\s+([^\s\.]+)', change_lower)
                    recommended_action = f"Use {action_match.group(1)}" if action_match else "Check documentation for the new format"
                    
                    result.update({
                        "found_breaking_change": True,
                        "change_type": change_type.upper().rstrip('S'),
                        "description": change,
                        "recommended_action": recommended_action
                    })
                    
                    # Try to update the content based on the change
                    if "apiVersion" in change:
                        version_match = re.search(r'([a-zA-Z0-9\./-]+/v[0-9a-zA-Z\.]+)', change)
                        if version_match:
                            updated_content = result["updated_content"]
                            updated_content["apiVersion"] = version_match.group(1)
                            result["updated_content"] = updated_content
                            
                    break
                
    return result