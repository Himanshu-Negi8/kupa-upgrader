"""
GitHub integration module for cloning repositories and creating pull requests.
"""

import os
import logging
import tempfile
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

import git
from github import Github

from kupa.analyzer import BreakingChange
from kupa.output import write_yaml_file

# Initialize the logger
logger = logging.getLogger('kupa.github_integration')

def clone_repo(repo_url: str) -> str:
    """
    Clone a GitHub repository to a temporary directory.
    
    Args:
        repo_url: The GitHub repository URL or "owner/repo" format
        
    Returns:
        The path to the cloned repository
    """
    # Format the repo URL properly
    if "/" in repo_url and not repo_url.startswith(("http://", "https://", "git@")):
        # Assume it's in the format "owner/repo"
        repo_url = f"https://github.com/{repo_url}.git"
    
    logger.info(f"Cloning repository: {repo_url}")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Clone the repository
        git.Repo.clone_from(repo_url, temp_dir)
        logger.info(f"Repository cloned to {temp_dir}")
        return temp_dir
    except Exception as e:
        # Clean up on failure
        shutil.rmtree(temp_dir)
        logger.error(f"Error cloning repository: {e}")
        raise


def create_pull_request(repo_url: str, repo_path: str, breaking_changes: List[BreakingChange], 
                       kube_version: str) -> str:
    """
    Create a pull request with fixes for breaking changes.
    
    Args:
        repo_url: The GitHub repository URL or "owner/repo" format
        repo_path: The path to the cloned repository
        breaking_changes: List of breaking changes to fix
        kube_version: Target Kubernetes version
        
    Returns:
        The URL of the created pull request
    """
    # Format owner/repo from the URL
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
        
    if "github.com" in repo_url:
        parts = repo_url.split("github.com/")
        if len(parts) > 1:
            owner_repo = parts[1]
        else:
            owner_repo = repo_url
    else:
        owner_repo = repo_url
        
    if "/" not in owner_repo:
        raise ValueError(f"Invalid repository format: {repo_url}")
        
    # Parse the owner/repo
    owner, repo_name = owner_repo.split("/")[:2]
    
    try:
        # Create a GitHub API client
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
            
        g = Github(github_token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Create a new branch
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"kupa-k8s-upgrade-{kube_version}-{timestamp}"
        
        # Initialize Git repo object
        git_repo = git.Repo(repo_path)
        
        # Get the default branch
        default_branch = repo.default_branch
        
        # Create a new branch from the default branch
        git_repo.git.checkout("-b", branch_name, f"origin/{default_branch}")
        
        # Apply fixes to files
        for change in breaking_changes:
            resource = change.resource
            updated_content = change.updated_content
            
            # Write the updated YAML file
            write_yaml_file(resource.file_path, updated_content)
            
        # Commit the changes
        git_repo.git.add(".")
        commit_message = f"Fix Kubernetes breaking changes for version {kube_version}\n\n"
        commit_message += f"This commit fixes the following breaking changes:\n"
        
        for change in breaking_changes:
            commit_message += f"- {change.resource.file_path}: {change.description}\n"
            
        git_repo.git.commit("-m", commit_message)
        
        # Push the branch
        git_repo.git.push("--set-upstream", "origin", branch_name)
        
        # Create a pull request
        pr_title = f"Fix Kubernetes breaking changes for version {kube_version}"
        pr_body = commit_message
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            base=default_branch,
            head=branch_name
        )
        
        logger.info(f"Created pull request: {pr.html_url}")
        return pr.html_url
        
    except Exception as e:
        logger.error(f"Error creating pull request: {e}")
        raise
