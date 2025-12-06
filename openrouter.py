#!/usr/bin/env python3
"""
OpenRouter API Client
Handles communication with OpenRouter API for LLM benchmarking.
"""

import os
import requests
import time

from pathlib import Path
from typing import Optional, Dict, Any


class OpenRouterClient:
    """Client for interacting with the OpenRouter API."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If not provided, reads from 
                     ~/.api-openrouter file or OPENROUTER_API_KEY env var.
        """
        self.api_key = api_key
        
        # Try reading from ~/.api-openrouter file
        if not self.api_key:
            api_file = Path.home() / ".api-openrouter"
            if api_file.exists():
                try:
                    self.api_key = api_file.read_text().strip()
                except IOError:
                    pass
        
        # Fallback to environment variable
        if not self.api_key:
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Create ~/.api-openrouter file "
                "or set OPENROUTER_API_KEY environment variable."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-benchmarks",
            "X-Title": "AI Benchmark Suite"
        }
    
    def generate(
        self, 
        model: str, 
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a completion from a model.
        
        Args:
            model: Model identifier (e.g., "openai/gpt-4", "anthropic/claude-3-opus")
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Dict with 'content' (response text) and 'usage' (token counts)
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Backoff parameters
        retries = 0
        max_retries = 5
        base_delay = 10
        max_delay = 120

        while True:
            try:
                response = requests.post(
                    url, 
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120  # 2 minute timeout for slow models
                )
                response.raise_for_status()
                break  # Success, exit loop
                
            except requests.exceptions.HTTPError as e:
                is_rate_limit = (e.response.status_code == 429)
                is_server_error = (e.response.status_code >= 500)
                
                if (is_rate_limit or is_server_error) and retries < max_retries:
                    retries += 1
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    error_type = "Rate limit" if is_rate_limit else f"Server error {e.response.status_code}"
                    print(f"[{error_type}] Retrying in {delay}s... (Attempt {retries}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    # Reraise if not retryable or retries exhausted
                    if e.response.status_code == 401:
                        raise ValueError("Invalid OpenRouter API key")
                    elif e.response.status_code == 429:
                        raise RuntimeError("Rate limit exceeded. Please wait and try again.")
                    elif e.response.status_code == 400:
                        error_msg = e.response.json().get("error", {}).get("message", str(e))
                        raise ValueError(f"Bad request: {error_msg}")
                    else:
                        raise RuntimeError(f"API error: {e}")

            
        data = response.json()
            
        # Extract the content from the response
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        
        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "model": data.get("model", model)
        }

    
    def list_models(self) -> list:
        """
        Get list of available models from OpenRouter.
        
        Returns:
            List of model info dictionaries
        """
        url = f"{self.BASE_URL}/models"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch models: {e}")


def get_prompt_for_benchmark(benchmark: str) -> str:
    """
    Load the prompt for a specific benchmark.
    
    Args:
        benchmark: Name of the benchmark (e.g., "maze")
        
    Returns:
        The prompt text
    """
    from pathlib import Path
    
    prompt_path = Path(__file__).parent / "benchmarks" / benchmark / "prompt.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"No prompt found for benchmark: {benchmark}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == "__main__":
    # Quick test of the client
    try:
        client = OpenRouterClient()
        print("[OK] OpenRouter client initialized")
        
        # Try to list models
        models = client.list_models()
        print(f"[OK] Found {len(models)} available models")
        
        # Show first 5 models
        for model in models[:5]:
            print(f"  - {model.get('id', 'unknown')}")
            
    except ValueError as e:
        print(f"[ERROR] {e}")
    except RuntimeError as e:
        print(f"[ERROR] {e}")