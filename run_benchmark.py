#!/usr/bin/env python3
"""
AI Benchmark CLI
Main entry point for running LLM spatial reasoning benchmarks.
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from benchmarks.maze.evaluator import grade_maze
from benchmarks.maze.strategic_evaluator import grade_strategic_maze

# Global log file path
LOG_FILE = None

def setup_logging():
    """Set up timestamped logging to logs/ directory."""
    global LOG_FILE
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    LOG_FILE = logs_dir / f"{timestamp}.txt"
    
    # Initialize log file with header
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Benchmark Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write("=" * 60 + "\n\n")

def log_message(message):
    """Write a message to the log file and also print to console."""
    if LOG_FILE:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(message + "\n")
    
    # Also print to console (preserving existing behavior)
    print(message)

def read_llm_output(file_path: str) -> str:
    """Read the LLM output file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")


def format_score_report(result: dict) -> str:
    """Format the score report for pretty printing."""
    if "error" in result:
        return f"[ERROR] {result['error']}\nScore: {result['score']}"
    
    score = result["score"]
    base_score = result.get("base_score", 0)
    structure_penalty = result.get("structure_penalty", 0)
    
    report = []
    report.append("[RESULTS] STRATEGIC MAZE BENCHMARK")
    report.append("=" * 40)
    report.append(f"Total Score: {score} points")
    report.append(f"Base Score: {base_score} points")
    
    if structure_penalty != 0:
        penalty_percent = int(structure_penalty * 100)
        report.append(f"Structure Penalty: {penalty_percent}% (Traps > Walls)")
    
    report.append("")
    report.append("SCORE BREAKDOWN:")
    report.append("-" * 20)
    
    components = result.get("components", {})
    for component_name, component_data in components.items():
        score_val = component_data.get("score", 0)
        desc = component_data.get("description", "")
        report.append(f"{component_name.title():12}: {score_val:6.1f} pts - {desc}")
    
    report.append("")
    report.append("MAZE ANALYSIS:")
    report.append("-" * 16)
    
    maze_info = result.get("maze_info", {})
    dimensions = maze_info.get("dimensions", "Unknown")
    elements = maze_info.get("elements", {})
    solvable = maze_info.get("solvable", False)
    complexity = maze_info.get("complexity_ratio", 0)
    
    report.append(f"Dimensions: {dimensions}")
    report.append(f"Elements: S={elements.get('S', 0)}, E={elements.get('E', 0)}, "
                  f"K={elements.get('K', 0)}, D={elements.get('D', 0)}, "
                  f"T={elements.get('T', 0)}, #={elements.get('#', 0)}")
    report.append(f"Solvable: {'Yes' if solvable else 'No'}")
    report.append(f"Complexity Ratio: {complexity:.2f}")
    
    # Show strategic elements if present
    strategic_elements = maze_info.get("strategic_elements", {})
    if strategic_elements:
        report.append(f"Strategic Elements: {strategic_elements}")
    
    if structure_penalty != 0:
        report.append("")
        report.append("[WARNING] This maze violates the structure constraint!")
        report.append("         Traps must not significantly outnumber walls.")
    
    return "\n".join(report)


def run_benchmark_on_model(model: str, benchmark: str) -> dict:
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
    
    # Save the LLM output to output/<model-name>/
    safe_model_name = model.replace("/", "_").replace(":", "_")
    output_dir = Path(__file__).parent / "output" / safe_model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{benchmark}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(llm_output)
    
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


def show_leaderboard(benchmark: str = None):
    """Display the current leaderboard."""
    from leaderboard import Leaderboard
    lb = Leaderboard()
    leaderboard_text = lb.format_cli_table(benchmark)
    print(leaderboard_text)
    
    # Also log the leaderboard
    if LOG_FILE:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write("\n" + leaderboard_text + "\n")


def benchmark_single_model(model: str, benchmark: str):
    """Benchmark a single model and return result tuple."""
    try:
        result = run_benchmark_on_model(model, benchmark)
        return (model, result, None)
    except Exception as e:
        return (model, None, str(e))


def move_model_to_skip(model_name: str):
    """Move a failed model from models.txt to models_skip.txt."""
    try:
        root_dir = Path(__file__).parent
        models_file = root_dir / "models.txt"
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
    """Move a rate-limited model from models.txt to models_limited.txt."""
    try:
        root_dir = Path(__file__).parent
        models_file = root_dir / "models.txt"
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


def run_all_models(benchmark: str, sequential: bool = False, retries: int = 1):
    """Run benchmarks on all models from models.txt, skipping those already tested."""
    from leaderboard import Leaderboard
    
    models_file = Path(__file__).parent / "models.txt"
    if not models_file.exists():
        log_message("[ERROR] models.txt not found")
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
    
    show_leaderboard(benchmark)


def rescore_all_outputs(benchmark: str):
    """Re-score all existing outputs and update leaderboard."""
    from leaderboard import Leaderboard
    
    lb = Leaderboard()
    root_dir = Path(__file__).parent
    output_dir = root_dir / "output"
    models_file = root_dir / "models.txt"
    
    if not output_dir.exists():
        log_message("[ERROR] No output directory found")
        return
        
    # Gather all potential models
    all_models = set()
    
    # 1. From models.txt
    if models_file.exists():
        with open(models_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_models.add(line.strip())
    
    # 2. From leaderboard
    # We can't easily get keys without loading, but we can assume LB is loaded in `lb.data`
    if "models" in lb.data:
        all_models.update(lb.data["models"].keys())
        
    # 3. From output directories (try to reverse engineer or just list them)
    # It's hard to map valid folder names back to model IDs if we don't have the map.
    # So we rely on the models we know.
    
    log_message(f"[RESCORE] Re-evaluating {len(all_models)} potential models for {benchmark}...")
    
    updated = 0
    errors = 0
    skipped = 0
    
    for model in tqdm(sorted(all_models), desc="Rescoring"):
        safe_model_name = model.replace("/", "_").replace(":", "_")
        model_dir = output_dir / safe_model_name
        
        # Search for all benchmark output files
        output_files = list(model_dir.glob(f"{benchmark}*.txt"))
        
        if not output_files:
            continue
            
        for output_file in output_files:
            try:
                # Read maze
                with open(output_file, 'r', encoding='utf-8') as f:
                    llm_output = f.read()
                
                # Grade
                if benchmark == "maze":
                    result = grade_strategic_maze(llm_output)
                else:
                    continue
                    
                # Add model info
                result["model"] = model
                
                # Save new score details
                # Save new score details
                score_file = output_file.with_name(output_file.stem + "_score.json")
                
                # Try to preserve existing details (time, tokens)
                existing_details = {}
                if score_file.exists():
                    try:
                        with open(score_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            existing_details = {
                                "elapsed_seconds": existing_data.get("elapsed_seconds", 0),
                                "token_usage": existing_data.get("token_usage", {})
                            }
                    except:
                        pass
                
                clean_result = {k: v for k, v in result.items() if k != "llm_response"}
                # Merge preserved details
                clean_result.update(existing_details)
                
                with open(score_file, 'w', encoding='utf-8') as f:
                    json.dump(clean_result, f, indent=2)
                
                # Update leaderboard
                lb.add_result(model, benchmark, result["score"], existing_details)
                updated += 1
                
            except Exception as e:
                errors += 1 

    log_message(f"\n[COMPLETE] Updated: {updated}, Errors: {errors}")
    show_leaderboard(benchmark)


def ingest_manual_output(file_path: str, benchmark: str):
    """Ingest a manual output file and update the system."""
    from leaderboard import Leaderboard
    import re
    import time
    
    path = Path(file_path)
    if not path.exists():
        log_message(f"[ERROR] Ingest file not found: {file_path}")
        return
        

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content:
            log_message("[ERROR] Empty ingest file")
            return
            
        # Split content by "model:" (case-insensitive) to find blocks
        model_header_pattern = re.compile(r'^(?:model|MODEL):\s*(.+)$', re.MULTILINE)
        
        matches = list(model_header_pattern.finditer(content))
        
        if not matches:
             log_message("[ERROR] No 'model: <name>' headers found.")
             return
             
        log_message(f"[INGEST] Found {len(matches)} model entries in {file_path}")
        
        for i, match in enumerate(matches):
            model_name = match.group(1).strip()
            start_pos = match.end()
            
            # End position is the start of the next match, or end of file
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(content)
            
            block_content = content[start_pos:end_pos]
            
            # Extract time if present
            time_match = re.search(r'(?m)^(?:time|TIME):\s*([\d\.]+)', block_content)
            elapsed_seconds = 0.0
            if time_match:
                try:
                    elapsed_seconds = float(time_match.group(1))
                except ValueError:
                    pass
            
            # The rest is the maze content. We need to strip "time:" line and optional "maze:" label if present
            # Actually, simpler to just treat everything else as potential maze content
            # The evaluator is robust enough to extract maze from text.
            llm_output = block_content
            
            # Save to output directory
            safe_model_name = model_name.replace("/", "_").replace(":", "_")
            output_dir = Path(__file__).parent / "output" / safe_model_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use timestamp to allow multiple runs
            timestamp = int(time.time())
            # Add small delay to ensure unique timestamps in fast loops
            time.sleep(0.1)
            output_file = output_dir / f"{benchmark}_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(llm_output)
                
            log_message(f"  > Processing '{model_name}'...")
                
            # Grade
            if benchmark == "maze":
                result = grade_strategic_maze(llm_output)
            else:
                raise ValueError(f"Unknown benchmark: {benchmark}")
                
            result["model"] = model_name
            result["elapsed_seconds"] = elapsed_seconds
            result["token_usage"] = {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}
            
            # Save score
            score_file = output_dir / f"{benchmark}_score.json"
            clean_result = {k: v for k, v in result.items() if k != "llm_response"}
            with open(score_file, 'w', encoding='utf-8') as f:
                json.dump(clean_result, f, indent=2)
                
            # Update leaderboard
            lb = Leaderboard()
            lb.add_result(
                model_name,
                benchmark,
                result["score"],
                {
                    "token_usage": result["token_usage"],
                    "elapsed_seconds": result["elapsed_seconds"]
                }
            )
            
            score_message = f"    - Score: {result['score']} (Time: {elapsed_seconds}s)"
            log_message(score_message)

        log_message("\n[SUCCESS] All entries processed and leaderboard updated.")
        show_leaderboard(benchmark)
        
    except Exception as e:
        log_message(f"[ERROR] Failed to ingest: {e}")


def main():
    """Main CLI function."""
    # Set up logging at the start
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="AI Benchmark - Strategic Spatial Reasoning Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py --input llm_output.txt
  python run_benchmark.py --model openai/gpt-4 --add-to-leaderboard
  python run_benchmark.py --run-all
  python run_benchmark.py --run-all --sequential
  python run_benchmark.py --leaderboard
  python run_benchmark.py --rescore
  python run_benchmark.py --ingest output.txt
        """
    )
    
    parser.add_argument("--input", "-i", help="Path to file containing LLM output")
    parser.add_argument("--model", "-m", help="OpenRouter model to benchmark")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--benchmark", "-b", default="maze", choices=["maze"])
    parser.add_argument("--leaderboard", "-l", action="store_true", help="Display leaderboard")
    parser.add_argument("--add-to-leaderboard", "-a", action="store_true", help="Save to leaderboard")
    parser.add_argument("--run-all", action="store_true", help="Run all models from models.txt")
    parser.add_argument("--sequential", "-s", action="store_true", help="Run sequentially instead of parallel")
    parser.add_argument("--retries", type=int, default=0, help="Number of retries on empty output (default: 0)")
    parser.add_argument("--rescore", action="store_true", help="Re-score all existing mazes in output/ directory")
    parser.add_argument("--ingest", help="Path to file for manual ingestion (Format: Line 1 'MODEL: name', rest is maze)")
    
    args = parser.parse_args()
    
    if args.ingest:
        ingest_manual_output(args.ingest, args.benchmark)
        return
    
    if args.rescore:
        rescore_all_outputs(args.benchmark)
        return
    
    if args.leaderboard:
        show_leaderboard(args.benchmark)
        return
    
    # Default behavior: run-all sequentially if no specific action is specified
    if not args.input and not args.model:
        # Default to sequential unless --run-all is explicitly used (which respects --sequential flag)
        run_all_models(args.benchmark, sequential=True if not args.run_all else args.sequential, retries=args.retries)
        return
    
    try:
        if args.model:
            log_message(f"[BENCHMARK] Running {args.benchmark} benchmark on {args.model}")
            print(f"[BENCHMARK] Running {args.benchmark} benchmark on {args.model}")
            result = run_benchmark_on_model(args.model, args.benchmark)
            received_message = f"[RECEIVED] Response ({result['token_usage']['completion_tokens']} tokens) in {result['elapsed_seconds']}s"
            log_message(received_message)
            print(received_message)
            
            if args.add_to_leaderboard:
                from leaderboard import Leaderboard
                lb = Leaderboard()
                lb.add_result(
                    args.model, 
                    args.benchmark, 
                    result["score"],
                    {
                        "token_usage": result.get("token_usage", {}),
                        "elapsed_seconds": result.get("elapsed_seconds", 0)
                    }
                )
                saved_message = "[SAVED] Score added to leaderboard"
                log_message(saved_message)
                print(saved_message)
        else:
            log_message(f"[READING] LLM output from: {args.input}")
            print(f"[READING] LLM output from: {args.input}")
            llm_output = read_llm_output(args.input)
            
            if args.benchmark == "maze":
                log_message("[RUNNING] Strategic Maze benchmark...")
                print("[RUNNING] Strategic Maze benchmark...")
                result = grade_strategic_maze(llm_output)
            else:
                raise ValueError(f"Unknown benchmark: {args.benchmark}")
        
        if args.json:
            output_result = {k: v for k, v in result.items() if k != "llm_response"}
            json_output = json.dumps(output_result, indent=2)
            print(json_output)
            log_message(json_output)
        else:
            score_report = format_score_report(result)
            print(score_report)
            log_message(score_report)
            
            if args.input:
                timestamp = args.input.replace('.txt', '_score.json')
                with open(timestamp, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                saved_message = f"\n[SAVED] Detailed results saved to: {timestamp}"
                print(saved_message)
                log_message(saved_message)
        
        if args.add_to_leaderboard:
            print("")
            log_message("")
            show_leaderboard(args.benchmark)
        
        sys.exit(0 if "error" not in result else 1)
            
    except FileNotFoundError as e:
        error_message = f"[ERROR] {e}"
        log_message(error_message)
        print(error_message)
        sys.exit(1)
    except ValueError as e:
        error_message = f"[ERROR] {e}"
        log_message(error_message)
        print(error_message)
        sys.exit(1)
    except RuntimeError as e:
        error_message = f"[ERROR] {e}"
        log_message(error_message)
        print(error_message)
        sys.exit(1)
    except Exception as e:
        error_message = f"[ERROR] Unexpected error: {e}"
        log_message(error_message)
        print(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()
