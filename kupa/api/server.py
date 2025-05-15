"""
API server for providing a web interface to the KuPa tool.
"""

import logging
import tempfile
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from kupa.analyzer import analyze_directory
from kupa.github_integration import clone_repo, create_pull_request
from kupa.output import write_local_results

# Initialize the logger
logger = logging.getLogger('kupa.api.server')

app = FastAPI(
    title="KuPa - Kubernetes Upgrade Path Analyzer",
    description="API for detecting Kubernetes breaking changes in YAML manifests",
    version="0.1.0",
)

# Data models
class GithubRequest(BaseModel):
    repo_url: str
    create_pr: bool = False
    kube_version: str = "latest"

class AnalysisResponse(BaseModel):
    status: str
    message: str
    breaking_changes: Optional[List[Dict[str, Any]]] = None
    pr_url: Optional[str] = None
    file_changes: Optional[List[Dict[str, str]]] = None


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to KuPa API - Kubernetes Upgrade Path Analyzer"}
    
    
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "KuPa API",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    kube_version: str = Form("latest")
):
    """Analyze uploaded YAML files for Kubernetes breaking changes."""
    try:
        # Create a temp directory for the uploaded files
        temp_dir = tempfile.mkdtemp()
        
        # Save the uploaded files
        for file in files:
            if file.filename.endswith(('.yaml', '.yml')):
                file_path = os.path.join(temp_dir, file.filename)
                
                # Make sure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save the file
                with open(file_path, 'wb') as f:
                    f.write(await file.read())
        
        # Analyze the directory
        results = analyze_directory(temp_dir, kube_version)
        
        if results:
            # Write the results to files with timestamps
            write_local_results(temp_dir, results)
            
            # Convert results to a serializable format
            serializable_results = []
            file_changes = []
            
            for change in results:
                # Add the breaking change info
                serializable_results.append({
                    "resource_kind": change.resource.kind,
                    "resource_api_version": change.resource.api_version,
                    "resource_name": change.resource.name,
                    "resource_namespace": change.resource.namespace,
                    "file_path": os.path.basename(change.resource.file_path),
                    "change_type": change.change_type,
                    "description": change.description,
                    "recommended_action": change.recommended_action
                })
                
                # Check if we've already added this file
                file_path = os.path.basename(change.resource.file_path)
                if not any(fc["original_file"] == file_path for fc in file_changes):
                    # Find the updated file
                    dir_path = os.path.dirname(change.resource.file_path)
                    original_name = os.path.basename(change.resource.file_path)
                    name, ext = os.path.splitext(original_name)
                    
                    # Look for updated files
                    updated_files = [f for f in os.listdir(dir_path) 
                                     if f.startswith(f"{name}-updated-") and f.endswith(ext)]
                    
                    if updated_files:
                        # Sort by timestamp (part of the filename)
                        updated_files.sort(reverse=True)
                        file_changes.append({
                            "original_file": file_path,
                            "updated_file": updated_files[0],
                            "diff_file": f"{updated_files[0]}.diff.txt"
                        })
            
            # Schedule cleanup
            background_tasks.add_task(lambda: shutil.rmtree(temp_dir))
            
            return AnalysisResponse(
                status="success",
                message=f"Analysis complete. Found {len(results)} breaking changes.",
                breaking_changes=serializable_results,
                file_changes=file_changes
            )
        else:
            # Schedule cleanup
            background_tasks.add_task(lambda: shutil.rmtree(temp_dir))
            
            return AnalysisResponse(
                status="success",
                message="Analysis complete. No breaking changes found."
            )
            
    except Exception as e:
        logger.error(f"Error analyzing uploaded files: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing files: {str(e)}")


@app.post("/analyze/github", response_model=AnalysisResponse)
async def analyze_github(github_request: GithubRequest):
    """Analyze a GitHub repository for Kubernetes breaking changes."""
    try:
        # Clone the repository
        temp_dir = clone_repo(github_request.repo_url)
        
        try:
            # Analyze the cloned repo
            results = analyze_directory(temp_dir, github_request.kube_version)
            
            if results:
                # Convert results to a serializable format
                serializable_results = []
                
                for change in results:
                    serializable_results.append({
                        "resource_kind": change.resource.kind,
                        "resource_api_version": change.resource.api_version,
                        "resource_name": change.resource.name,
                        "resource_namespace": change.resource.namespace,
                        "file_path": os.path.relpath(change.resource.file_path, temp_dir),
                        "change_type": change.change_type,
                        "description": change.description,
                        "recommended_action": change.recommended_action
                    })
                
                # Create PR if requested
                pr_url = None
                if github_request.create_pr:
                    pr_url = create_pull_request(
                        github_request.repo_url, 
                        temp_dir, 
                        results, 
                        github_request.kube_version
                    )
                    
                return AnalysisResponse(
                    status="success",
                    message=f"Analysis complete. Found {len(results)} breaking changes." 
                            (f" Pull request created: {pr_url}" if pr_url else ""),
                    breaking_changes=serializable_results,
                    pr_url=pr_url
                )
            else:
                return AnalysisResponse(
                    status="success",
                    message="Analysis complete. No breaking changes found."
                )
                
        finally:
            # Clean up the temp directory
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"Error analyzing GitHub repository: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing repository: {str(e)}")


def start_server(port: int = 8080):
    """Start the FastAPI server."""
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    start_server()
