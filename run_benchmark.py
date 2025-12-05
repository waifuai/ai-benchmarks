#!/usr/bin/env python3
"""
AI Benchmark CLI
Main entry point for running LLM spatial reasoning benchmarks.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from benchmarks.maze.evaluator import grade_maze


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
        return f"[ERROR] {result['error']}\\nScore: {result['score']}"
    
    score = result["score"]
    base_score = result.get("base_score", 0)
    structure_penalty = result.get("structure_penalty", 0)
    
    report = []
    report.append("[RESULTS] MAZE GAUNTLET BENCHMARK")
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
    
    if structure_penalty != 0:
        report.append("")
        report.append("[WARNING] This maze violates the structure constraint!")
        report.append("         Traps must not outnumber walls.")
    
    return "\\n".join(report)


def run_benchmark_on_model(model: str, benchmark: str) -> dict:
    """Run a benchmark against an OpenRouter model."""
    from openrouter import OpenRouterClient, get_prompt_for_benchmark
    
    client = OpenRouterClient()
    prompt = get_prompt_for_benchmark(benchmark)
    
    # Generate response with timing
    start_time = time.time()
    response = client.generate(model, prompt)
    elapsed_time = time.time() - start_time
    
    llm_output = response["content"]
    
    # Save the LLM output to output/<model-name>/
    safe_model_name = model.replace("/", "_").replace(":", "_")
    output_dir = Path(__file__).parent / "output" / safe_model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{benchmark}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(llm_output)
    
    # Grade the response
    if benchmark == "maze":
        result = grade_maze(llm_output)
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
    print(lb.format_cli_table(benchmark))


def benchmark_single_model(model: str, benchmark: str):
    """Benchmark a single model and return result tuple."""
    try:
        result = run_benchmark_on_model(model, benchmark)
        return (model, result, None)
    except Exception as e:
        return (model, None, str(e))


def run_all_models(benchmark: str, sequential: bool = False):
    """Run benchmarks on all models from models.txt, skipping those already tested."""
    from leaderboard import Leaderboard
    
    models_file = Path(__file__).parent / "models.txt"
    if not models_file.exists():
        print("[ERROR] models.txt not found")
        return
    
    lb = Leaderboard()
    
    with open(models_file, 'r', encoding='utf-8') as f:
        all_models = [line.strip() for line in f if line.strip()]
    
    # Filter out already tested models
    models_to_test = []
    for model in all_models:
        existing = lb.get_result(model, benchmark)
        if existing:
            print(f"[SKIP] {model} - already has score: {existing['score']}")
        else:
            models_to_test.append(model)
    
    if not models_to_test:
        print("[DONE] All models already tested")
        show_leaderboard(benchmark)
        return
    
    print(f"\n[RUN-ALL] Testing {len(models_to_test)} models {'sequentially' if sequential else 'in parallel'}...")
    
    tested = 0
    errors = 0
    
    if sequential:
        # Sequential execution
        for model in models_to_test:
            print(f"\n[TESTING] {model}")
            model_name, result, error = benchmark_single_model(model, benchmark)
            
            if error:
                print(f"[ERROR] {model}: {error}")
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
                print(f"[DONE] {model}: Score {result['score']} ({result.get('elapsed_seconds', 0)}s)")
                tested += 1
    else:
        # Parallel execution
        print(f"[PARALLEL] Starting {len(models_to_test)} concurrent API calls...")
        
        with ThreadPoolExecutor(max_workers=len(models_to_test)) as executor:
            futures = {
                executor.submit(benchmark_single_model, model, benchmark): model 
                for model in models_to_test
            }
            
            for future in as_completed(futures):
                model_name, result, error = future.result()
                
                if error:
                    print(f"[ERROR] {model_name}: {error}")
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
                    print(f"[DONE] {model_name}: Score {result['score']} ({result.get('elapsed_seconds', 0)}s)")
                    tested += 1
    
    print(f"\n{'='*60}")
    print(f"[COMPLETE] Tested: {tested}, Errors: {errors}")
    print('='*60)
    
    show_leaderboard(benchmark)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Benchmark - Spatial Reasoning Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py --input llm_output.txt
  python run_benchmark.py --model openai/gpt-4 --add-to-leaderboard
  python run_benchmark.py --run-all
  python run_benchmark.py --run-all --sequential
  python run_benchmark.py --leaderboard
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
    
    args = parser.parse_args()
    
    if args.leaderboard:
        show_leaderboard(args.benchmark)
        return
    
    if args.run_all:
        run_all_models(args.benchmark, sequential=args.sequential)
        return
    
    if not args.input and not args.model:
        parser.error("Either --input, --model, --run-all, or --leaderboard is required")
    
    try:
        if args.model:
            print(f"[BENCHMARK] Running {args.benchmark} benchmark on {args.model}")
            result = run_benchmark_on_model(args.model, args.benchmark)
            print(f"[RECEIVED] Response ({result['token_usage']['completion_tokens']} tokens) in {result['elapsed_seconds']}s")
            
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
                print(f"[SAVED] Score added to leaderboard")
        else:
            print(f"[READING] LLM output from: {args.input}")
            llm_output = read_llm_output(args.input)
            
            if args.benchmark == "maze":
                print("[RUNNING] Maze Gauntlet benchmark...")
                result = grade_maze(llm_output)
            else:
                raise ValueError(f"Unknown benchmark: {args.benchmark}")
        
        if args.json:
            output_result = {k: v for k, v in result.items() if k != "llm_response"}
            print(json.dumps(output_result, indent=2))
        else:
            score_report = format_score_report(result)
            print(score_report)
            
            if args.input:
                timestamp = args.input.replace('.txt', '_score.json')
                with open(timestamp, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print(f"\\n[SAVED] Detailed results saved to: {timestamp}")
        
        if args.add_to_leaderboard:
            print("")
            show_leaderboard(args.benchmark)
        
        sys.exit(0 if "error" not in result else 1)
            
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()