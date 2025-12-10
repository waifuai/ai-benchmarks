#!/usr/bin/env python3
"""
Benchmark Runner
Core logic for running benchmarks against models.
"""

import time
from typing import Dict, Optional, Tuple
from benchmarks.maze.evaluator import grade_maze
from benchmarks.maze.strategic_evaluator import grade_strategic_maze


def run_benchmark_on_model(model: str, benchmark: str) -> Dict:
    """Run a benchmark against an OpenRouter model."""
    from openrouter import OpenRouterClient, get_prompt_for_benchmark
    
    client = OpenRouterClient()
    prompt = get_prompt_for_benchmark(benchmark)
    
    # Generate response (no retries - move to next model on failure)
    start_time = time.time()
    try:
        response = client.generate(model, prompt)
        llm_output = response["content"]
        
        if not llm_output or not llm_output.strip():
            raise ValueError(f"Empty response from model {model}")
            
    except Exception as e:
        raise Exception(f"Error generating response from {model}: {e}")
        
    elapsed_time = time.time() - start_time
    
    # Grade the response
    if benchmark == "maze":
        result = grade_strategic_maze(llm_output)
    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")
    
    # Add model info to result
    result["model"] = model
    result["llm_response"] = llm_output
    result["token_usage"] = response["usage"]
    result["elapsed_seconds"] = round(elapsed_time, 2)
    
    return result


def run_benchmark_on_file(file_path: str, benchmark: str) -> Dict:
    """Run a benchmark on an existing LLM output file."""
    from benchmark_utils import read_llm_output
    
    llm_output = read_llm_output(file_path)
    
    # Grade the response
    if benchmark == "maze":
        result = grade_strategic_maze(llm_output)
    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")
    
    return result


def benchmark_single_model(model: str, benchmark: str) -> Tuple[str, Optional[Dict], Optional[str]]:
    """Benchmark a single model and return result tuple."""
    try:
        result = run_benchmark_on_model(model, benchmark)
        return (model, result, None)
    except Exception as e:
        return (model, None, str(e))


def show_leaderboard(benchmark: str = None):
    """Display the current leaderboard."""
    from leaderboard import Leaderboard
    lb = Leaderboard()
    leaderboard_text = lb.format_cli_table(benchmark)
    print(leaderboard_text)
    
    # Also log the leaderboard
    from benchmark_utils import LOG_FILE
    if LOG_FILE:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Leaderboard Export - {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(leaderboard_text)
            f.write("\n")