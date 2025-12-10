#!/usr/bin/env python3
"""
AI Benchmark CLI
Main entry point for running LLM spatial reasoning benchmarks.
"""

import argparse
import json
import sys
from benchmark_utils import setup_logging, format_score_report, save_llm_output, save_score_file
from benchmark_runner import run_benchmark_on_model, run_benchmark_on_file, show_leaderboard
from batch_processor import run_all_models
from manual_ingestion import ingest_manual_output, rescore_all_outputs


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
    parser.add_argument("--run-all", action="store_true", help="Run all models from models_todo.txt")
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
        run_all_models(args.benchmark, sequential=True if not args.run_all else args.sequential)
        return
    
    try:
        if args.model:
            from benchmark_utils import log_message
            from leaderboard import Leaderboard
            
            log_message(f"[BENCHMARK] Running {args.benchmark} benchmark on {args.model}")
            print(f"[BENCHMARK] Running {args.benchmark} benchmark on {args.model}")
            result = run_benchmark_on_model(args.model, args.benchmark)
            
            # Save output and score files
            save_llm_output(args.model, args.benchmark, result["llm_response"])
            score_file = save_score_file(args.model, args.benchmark, result)
            
            received_message = f"[RECEIVED] Response ({result['token_usage']['completion_tokens']} tokens) in {result['elapsed_seconds']}s"
            log_message(received_message)
            print(received_message)
            
            if args.add_to_leaderboard:
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
            from benchmark_utils import log_message
            
            log_message(f"[READING] LLM output from: {args.input}")
            print(f"[READING] LLM output from: {args.input}")
            result = run_benchmark_on_file(args.input, args.benchmark)
        
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
