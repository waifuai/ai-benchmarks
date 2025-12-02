#!/usr/bin/env python3
"""
AI Benchmark CLI
Main entry point for running LLM spatial reasoning benchmarks.
"""

import argparse
import json
import sys
from pathlib import Path
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
    
    # Create a nice formatted report
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


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Benchmark - Spatial Reasoning Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py --input llm_output.txt
  python run_benchmark.py -i sample_maze.txt --json
  
The input file should contain the LLM's maze output in markdown code blocks.
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to file containing LLM output"
    )
    
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format instead of pretty print"
    )
    
    parser.add_argument(
        "--benchmark", "-b",
        default="maze",
        choices=["maze"],
        help="Which benchmark to run (default: maze)"
    )
    
    args = parser.parse_args()
    
    try:
        # Read the LLM output
        print(f"[READING] LLM output from: {args.input}")
        llm_output = read_llm_output(args.input)
        
        # Run the appropriate benchmark
        if args.benchmark == "maze":
            print("[RUNNING] Maze Gauntlet benchmark...")
            result = grade_maze(llm_output)
        else:
            raise ValueError(f"Unknown benchmark: {args.benchmark}")
        
        # Output results
        if args.json:
            # Raw JSON output
            print(json.dumps(result, indent=2))
        else:
            # Pretty formatted output
            score_report = format_score_report(result)
            print(score_report)
            
            # Also save a JSON file with timestamp
            timestamp = args.input.replace('.txt', '_score.json')
            with open(timestamp, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"\\n[SAVED] Detailed results saved to: {timestamp}")
        
        # Exit with appropriate code
        if "error" in result:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()