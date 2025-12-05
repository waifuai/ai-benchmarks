#!/usr/bin/env python3
"""
AI Benchmark CLI
Main entry point for running LLM spatial reasoning benchmarks.
"""

import argparse
import json
import sys
from pathlib import Path
from tqdm import tqdm
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


def show_leaderboard(benchmark: str = None):
    """Display the current leaderboard."""
    from leaderboard import Leaderboard
    lb = Leaderboard()
    print(lb.format_cli_table(benchmark))


def rescore_all_outputs(benchmark: str):
    """Re-score all existing outputs and update leaderboard."""
    from leaderboard import Leaderboard
    
    lb = Leaderboard()
    root_dir = Path(__file__).parent
    output_dir = root_dir / "output"
    models_file = root_dir / "models.txt"
    
    if not output_dir.exists():
        print("[ERROR] No output directory found")
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
    
    print(f"[RESCORE] Re-evaluating {len(all_models)} potential models for {benchmark}...")
    
    updated = 0
    errors = 0
    skipped = 0
    
    for model in tqdm(sorted(all_models), desc="Rescoring"):
        safe_model_name = model.replace("/", "_").replace(":", "_")
        model_dir = output_dir / safe_model_name
        output_file = model_dir / f"{benchmark}.txt"
        
        if not output_file.exists():
            # Try to see if there is any directory that matches logic?
            # actually if file doesn't exist, we just skip
            # skipped += 1
            continue
            
        try:
            # Read maze
            with open(output_file, 'r', encoding='utf-8') as f:
                llm_output = f.read()
            
            # Grade
            if benchmark == "maze":
                result = grade_maze(llm_output)
            else:
                continue
                
            # Add model info (needed for some logic, though grade_maze doesn't strictly use it)
            result["model"] = model
            
            # Save new score details
            score_file = model_dir / f"{benchmark}_score.json"
            clean_result = {k: v for k, v in result.items() if k != "llm_response"}
            with open(score_file, 'w', encoding='utf-8') as f:
                json.dump(clean_result, f, indent=2)
            
            # Update leaderboard
            # Get existing details to preserve token stats
            old_entry = lb.get_result(model, benchmark)
            details = {}
            if old_entry:
                details = old_entry.get("details", {})
            
            # Update score
            lb.add_result(model, benchmark, result["score"], details)
            updated += 1
            
        except Exception as e:
            # tqdm.write(f"[ERROR] Failed to rescore {model}: {e}")
            errors += 1
            
    print(f"\\n[COMPLETE] Updated: {updated}, Errors: {errors}")
    show_leaderboard(benchmark)


def ingest_manual_output(file_path: str, benchmark: str):
    """Ingest a manual output file and update the system."""
    from leaderboard import Leaderboard
    import re
    
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] Ingest file not found: {file_path}")
        return
        

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content:
            print("[ERROR] Empty ingest file")
            return
            
        # Split content by "model:" (case-insensitive) to find blocks
        # We need to keep the delimiter to know where blocks start
        # Regex lookahead to split but keep delimiter is tricky with split, 
        # easier to finditer.
        
        # Regex to find model headers: start of line, "model:" or "MODEL:", capture rest of line
        model_header_pattern = re.compile(r'(?m)^(?:model|MODEL):\\s*(.+)$')
        
        matches = list(model_header_pattern.finditer(content))
        
        if not matches:
             print("[ERROR] No 'model: <name>' headers found.")
             return
             
        print(f"[INGEST] Found {len(matches)} model entries in {file_path}")
        
        for i, match in enumerate(matches):
            model_name = match.group(1).strip()
            start_pos = match.end()
            
            # End position is the start of the next match, or end of file
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(content)
            
            block_content = content[start_pos:end_pos]
            
            # Extract time if present
            time_match = re.search(r'(?m)^(?:time|TIME):\\s*([\\d\\.]+)', block_content)
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
            
            output_file = output_dir / f"{benchmark}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(llm_output)
                
            print(f"  > Processing '{model_name}'...")
                
            # Grade
            if benchmark == "maze":
                result = grade_maze(llm_output)
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
            
            print(f"    - Score: {result['score']} (Time: {elapsed_seconds}s)")

        print("\\n[SUCCESS] All entries processed and leaderboard updated.")
        show_leaderboard(benchmark)
        
    except Exception as e:
        print(f"[ERROR] Failed to ingest: {e}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="AI Benchmark - Spatial Reasoning Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py --input llm_output.txt
  python run_benchmark.py --leaderboard
  python run_benchmark.py --rescore
  python run_benchmark.py --ingest output.txt
        """
    )
    
    parser.add_argument("--input", "-i", help="Path to file containing LLM output")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--benchmark", "-b", default="maze", choices=["maze"])
    parser.add_argument("--leaderboard", "-l", action="store_true", help="Display leaderboard")
    parser.add_argument("--add-to-leaderboard", "-a", action="store_true", help="Save to leaderboard")
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
    
    # Default behavior: require input file
    if not args.input:
        parser.print_help()
        print("\\n[ERROR] Please provide an input file with --input")
        sys.exit(1)
    
    try:
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