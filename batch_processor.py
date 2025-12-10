#!/usr/bin/env python3
"""
Batch Processor
Batch operations and model management functionality.
"""

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from benchmark_utils import log_message
from benchmark_runner import benchmark_single_model


def move_model_to_skip(model_name: str):
    """Move a failed model from models_todo.txt to models_skip.txt."""
    try:
        root_dir = Path(__file__).parent
        models_file = root_dir / "models_todo.txt"
        skip_file = root_dir / "models_skip.txt"
        
        # Add to skip file
        with open(skip_file, 'a', encoding='utf-8') as f:
            f.write(f"{model_name}\n")
            
        # Remove from models file
        if models_file.exists():
            with open(models_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(models_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != model_name:
                        f.write(line)
                        
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to move model to skip list: {e}\n")


def move_model_to_limited(model_name: str):
    """Move a rate-limited model from models_todo.txt to models_limited.txt."""
    try:
        root_dir = Path(__file__).parent
        models_file = root_dir / "models_todo.txt"
        limited_file = root_dir / "models_limited.txt"
        
        # Add to limited file
        with open(limited_file, 'a', encoding='utf-8') as f:
            f.write(f"{model_name}\n")
            
        # Remove from models file
        if models_file.exists():
            with open(models_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open(models_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != model_name:
                        f.write(line)
                        
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to move model to limited list: {e}\n")


def run_all_models(benchmark: str, sequential: bool = False):
    """Run benchmarks on all models from models_todo.txt, skipping those already tested."""
    from leaderboard import Leaderboard
    
    models_file = Path(__file__).parent / "models_todo.txt"
    if not models_file.exists():
        log_message("[ERROR] models_todo.txt not found")
        return
    
    lb = Leaderboard()
    
    with open(models_file, 'r', encoding='utf-8') as f:
        all_models = [line.strip() for line in f if line.strip()]
    
    # Filter out already tested models
    models_to_test = []
    for model in all_models:
        existing = lb.get_result(model, benchmark)
        if existing:
            skip_message = f"[SKIP] {model} - already has score: {existing['score']}"
            log_message(skip_message)
        else:
            models_to_test.append(model)
    
    if not models_to_test:
        log_message("[DONE] All models already tested")
        from benchmark_runner import show_leaderboard
        show_leaderboard(benchmark)
        return
    
    log_message(f"\n[RUN-ALL] Testing {len(models_to_test)} models {'sequentially' if sequential else 'in parallel'}...")
    
    tested = 0
    errors = 0
    
    if sequential:
        # Sequential execution with progress bar
        pbar = tqdm(total=len(models_to_test), desc="Benchmarking", unit="model")
        
        for model in models_to_test:
            tqdm.write(f"[TESTING] {model}")
            model_name, result, error = benchmark_single_model(model, benchmark)
            
            if error:
                tqdm.write(f"[ERROR] {model}: {error}")
                # Log the error message
                log_message(f"[ERROR] {model}: {error}")
                
                # Check if this is a rate limit error
                if "Rate limit exceeded" in error:
                    move_model_to_limited(model)
                    tqdm.write(f"[LIMITED] Moved {model} to models_limited.txt")
                    log_message(f"[LIMITED] Moved {model} to models_limited.txt")
                else:
                    move_model_to_skip(model)
                    tqdm.write(f"[SKIP] Moved {model} to models_skip.txt")
                    log_message(f"[SKIP] Moved {model} to models_skip.txt")
                # Remove this failed/limited model from total count
                pbar.total -= 1
                errors += 1
            else:
                lb.add_result(
                    model_name,
                    benchmark,
                    result["score"],
                    {
                        "token_usage": result.get("token_usage", {}),
                        "elapsed_seconds": result.get("elapsed_seconds", 0)
                    }
                )
                done_message = f"[DONE] {model}: Score {result['score']} ({result.get('elapsed_seconds', 0)}s)"
                tqdm.write(done_message)
                log_message(done_message)
                tested += 1
            
            pbar.update(1)
        
        pbar.close()
    else:
        # Parallel execution
        log_message(f"[PARALLEL] Starting {len(models_to_test)} concurrent API calls...")
        
        with ThreadPoolExecutor(max_workers=len(models_to_test)) as executor:
            futures = {
                executor.submit(benchmark_single_model, model, benchmark): model 
                for model in models_to_test
            }
            
            for future in as_completed(futures):
                model_name, result, error = future.result()
                
                if error:
                    error_message = f"[ERROR] {model_name}: {error}"
                    print(error_message)
                    log_message(error_message)
                    # Check if this is a rate limit error
                    if "Rate limit exceeded" in error:
                        move_model_to_limited(model_name)
                        limited_message = f"[LIMITED] Moved {model_name} to models_limited.txt"
                        print(limited_message)
                        log_message(limited_message)
                    else:
                        move_model_to_skip(model_name)
                        skip_message = f"[SKIP] Moved {model_name} to models_skip.txt"
                        print(skip_message)
                        log_message(skip_message)
                    errors += 1
                else:
                    lb.add_result(
                        model_name,
                        benchmark,
                        result["score"],
                        {
                            "token_usage": result.get("token_usage", {}),
                            "elapsed_seconds": result.get("elapsed_seconds", 0)
                        }
                    )
                    done_message = f"[DONE] {model_name}: Score {result['score']} ({result.get('elapsed_seconds', 0)}s)"
                    print(done_message)
                    log_message(done_message)
                    tested += 1
    
    log_message(f"\n{'='*60}")
    log_message(f"[COMPLETE] Tested: {tested}, Errors: {errors}")
    log_message('='*60)
    
    from benchmark_runner import show_leaderboard
    show_leaderboard(benchmark)