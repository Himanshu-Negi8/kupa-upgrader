"""
Model Context Protocol (MCP) client for querying AI models about Kubernetes breaking changes.
"""

import logging
import os
import json
from typing import Dict, Any, Optional
import requests

import openai
from openai import OpenAI

from kupa.analyzer import K8sResource
from kupa.config import load_config

# Initialize the logger
logger = logging.getLogger('kupa.mcp.model_client')

def query_model_for_changes(resource: K8sResource, target_k8s_version: str) -> Dict[str, Any]:
    """
    Query the AI model for breaking changes in the given Kubernetes resource.
    
    Args:
        resource: The Kubernetes resource to check
        target_k8s_version: The target Kubernetes version
        
    Returns:
        Dict with the model's response including:
        - is_confident: Whether the model is confident in its answer
        - has_breaking_change: Whether a breaking change was detected
        - change_type: The type of breaking change (if any)
        - description: Description of the breaking change
        - recommended_action: Recommended action to fix the issue
        - updated_content: Updated resource content with fixes applied
    """
    try:
        # Load configuration
        config = load_config()
        ai_config = config.get("ai_model", {})
        
        # Get model settings
        model_provider = ai_config.get("provider", "openai")
        model_name = ai_config.get("model", "gpt-4-turbo")
        temperature = ai_config.get("temperature", 0.1)
        max_tokens = ai_config.get("max_tokens", 4000)
        
        # Format the query for the model
        resource_yaml = json.dumps(resource.content, indent=2)
        prompt = f"""
        I have a Kubernetes resource of kind {resource.kind} with apiVersion {resource.api_version}.
        I want to know if there are any breaking changes when upgrading to Kubernetes version {target_k8s_version}.
        
        Here is the resource:
        ```yaml
        {resource_yaml}
        ```
        
        Please analyze this resource and tell me:
        1. Are there any breaking changes for this resource in Kubernetes {target_k8s_version}?
        2. If yes, what is the change type (API_DEPRECATED, FIELD_REMOVED, etc.)?
        3. Description of the breaking change
        4. Recommended action to fix it
        5. The updated YAML that would fix the issue
        
        Please format your response as JSON with the following structure:
        {{
            "has_breaking_change": true/false,
            "change_type": "string",
            "description": "string",
            "recommended_action": "string",
            "updated_content": {{}} // the fixed resource as JSON
        }}
        """
        
        if os.environ.get("MODEL_PROVIDER") == "ollama":
            try:
                # First check if the Ollama server is running and which models are available
                logger.info("Using Ollama as model provider. Checking available models...")
                ollama_models_url = "http://localhost:11434/api/tags"
                models_response = requests.get(ollama_models_url)
                models_response.raise_for_status()
                available_models = models_response.json().get("models", [])
                
                # Get model name from config (default to llama3)
                ollama_model = ai_config.get("model", "llama3")
                available_model_names = [model.get("name").split(":")[0] for model in available_models]
                
                # Make sure we have a model that exists
                if not any(ollama_model.startswith(name) for name in available_model_names):
                    logger.warning(f"Model {ollama_model} not found in Ollama. Available models: {available_model_names}")
                    if "llama3" in available_model_names:
                        logger.info("Falling back to llama3 model")
                        ollama_model = "llama3"
                    else:
                        logger.warning(f"No suitable models found in Ollama. Using first available: {available_model_names[0]}")
                        ollama_model = available_model_names[0]
                
                # Query local Ollama server
                logger.info(f"Querying Ollama with model: {ollama_model}")
                ollama_url = "http://localhost:11434/api/generate"
                ollama_payload = {
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                }
                ollama_response = requests.post(ollama_url, json=ollama_payload)
                ollama_response.raise_for_status()
                response_json = ollama_response.json()
                # Ollama returns the response in the 'response' field
                response_text = response_json["response"]
                logger.debug(f"Got response from Ollama: {response_text[:100]}...")
                
                # Helper function to extract JSON from potential free-form text
                def extract_json_from_text(text):
                    import re
                    # Find JSON pattern between curly braces
                    json_pattern = re.search(r'({[\s\S]*?})', text)
                    if json_pattern:
                        potential_json = json_pattern.group(1)
                        try:
                            return json.loads(potential_json)
                        except json.JSONDecodeError:
                            pass
                    
                    # Try with code block format ```json ... ```
                    code_block_pattern = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
                    if code_block_pattern:
                        potential_json = code_block_pattern.group(1)
                        try:
                            return json.loads(potential_json)
                        except json.JSONDecodeError:
                            pass
                    
                    # Return a default response if no valid JSON found
                    logger.warning("Could not extract valid JSON from Ollama response")
                    return {
                        "has_breaking_change": True,
                        "change_type": "API_DEPRECATED",
                        "description": "Could not parse model response. Using static fallback information.",
                        "recommended_action": "Check manually or try again.",
                        "updated_content": {}
                    }

                # Try to extract JSON from the response
                try:
                    model_response = extract_json_from_text(response_text)
                    # Create a mock response object that matches the expected structure
                    response = type('OllamaResponse', (), {"choices": [type('Choice', (), {"message": type('Message', (), {"content": json.dumps(model_response)})()})()]})()
                except Exception as e:
                    logger.error(f"Error extracting JSON from Ollama response: {e}")
                    raise
            except requests.exceptions.ConnectionError:
                logger.error("Failed to connect to Ollama server. Is it running? Try: ollama serve")
                raise
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error from Ollama: {e}")
                raise
            except KeyError as e:
                logger.error(f"Unexpected response format from Ollama: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error querying Ollama: {e}")
                raise
        elif model_provider.lower() == "openai":
            # Initialize OpenAI client
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'your-api-key'))
            
            # Call the OpenAI API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a Kubernetes expert assistant that helps identify breaking changes in Kubernetes resources when upgrading versions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Parse the JSON response
        response_text = response.choices[0].message.content
        model_response = json.loads(response_text)
        
        # Add confidence level based on the model's ability to provide an answer
        is_confident = True
        if "confidence" in model_response:
            is_confident = model_response["confidence"] > 0.7
        elif "I'm not sure" in model_response.get("description", "") or "uncertain" in model_response.get("description", "").lower():
            is_confident = False
            
        # Add confidence to the response
        model_response["is_confident"] = is_confident
        
        return model_response
        
    except Exception as e:
        logger.error(f"Error querying AI model: {e}")
        # Return a default response indicating the model couldn't provide an answer
        return {
            "is_confident": False,
            "has_breaking_change": False,
            "change_type": None,
            "description": f"Error querying AI model: {str(e)}",
            "recommended_action": "Please check manually or try again later.",
            "updated_content": resource.content
        }
