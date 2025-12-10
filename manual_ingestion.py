#!/usr/bin/env python3
"""
Manual Ingestion
Manual output ingestion functionality.
"""

import re
import time
from pathlib import Path
from benchmark_utils import log_message, save_llm_output, save_score_file
from benchmark_runner import run_benchmark_on_file


def ingest_manual_output(file_path: str, benchmark: str):
    """Ingest a manual output file and update the system."""
    from leaderboard import Leaderboard
    
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
            output_file = save_llm_output(model_name, benchmark, llm_output)
                
            log_message(f"  > Processing '{model_name}'...")
                
            # Grade
            if benchmark == "maze":
                result = run_benchmark_on_file(str(output_file), benchmark)
            else:
                raise ValueError(f"Unknown benchmark: {benchmark}")
                
            result["model"] = model_name
            result["elapsed_seconds"] = elapsed_seconds
            result["token_usage"] = {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}
            
            # Save score
            score_file = save_score_file(model_name, benchmark, result)
                
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
        from benchmark_runner import show_leaderboard
        show_leaderboard(benchmark)
        
    except Exception as e:
        log_message(f"[ERROR] Failed to ingest: {e}")


def rescore_all_outputs(benchmark: str):
    """Re-score all existing outputs and update leaderboard."""
    from leaderboard import Leaderboard
    
    lb = Leaderboard()
    root_dir = Path(__file__).parent
    output_dir = root_dir / "output"
    
    if not output_dir.exists():
        log_message("[ERROR] No output directory found")
        return
        
    # Gather all potential models from leaderboard and output directories
    all_models = set()
    
    # 1. From leaderboard
    if "models" in lb.data:
        all_models.update(lb.data["models"].keys())
        
    # 2. From output directories
    for model_dir in output_dir.iterdir():
        if model_dir.is_dir():
            # Try to reverse engineer model name from directory name
            # Directory names use format: provider_model_name_free
            dir_name = model_dir.name
            # Remove _free suffix if present
            if dir_name.endswith("_free"):
                model_id = dir_name[:-5]
            else:
                model_id = dir_name
            
            # Convert back to model format (provider/model:free)
            if "_" in model_id:
                parts = model_id.split("_", 1)
                if len(parts) == 2:
                    provider = parts[0]
                    model_name = parts[1]
                    # Add :free suffix to make it a valid model ID
                    full_model = f"{provider}/{model_name}:free"
                    all_models.add(full_model)
    
    log_message(f"[RESCORE] Re-evaluating {len(all_models)} potential models for {benchmark}...")
    
    updated = 0
    errors = 0
    skipped = 0
    
    from tqdm import tqdm
    for model in tqdm(sorted(all_models), desc="Rescoring"):
        safe_model_name = model.replace("/", "_").replace(":", "_")
        model_dir = output_dir / safe_model_name
        
        # Search for all benchmark output files
        output_files = list(model_dir.glob(f"{benchmark}*.txt"))
        
        if not output_files:
            continue
            
        for output_file in output_files:
            try:
                # Grade
                if benchmark == "maze":
                    result = run_benchmark_on_file(str(output_file), benchmark)
                else:
                    continue
                    
                # Add model info
                result["model"] = model
                
                # Save new score details
                score_file = output_file.with_name(output_file.stem + "_score.json")
                
                # Try to preserve existing details (time, tokens)
                existing_details = {}
                if score_file.exists():
                    try:
                        import json
                        with open(score_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            existing_details = {
                                "elapsed_seconds": existing_data.get("elapsed_seconds", 0),
                                "token_usage": existing_data.get("token_usage", {})
                            }
                    except:
                        pass
                
                # Save updated score
                save_score_file(model, benchmark, result)
                
                # Update leaderboard
                lb.add_result(model, benchmark, result["score"], existing_details)
                updated += 1
                
            except Exception as e:
                errors += 1 

    log_message(f"\n[COMPLETE] Updated: {updated}, Errors: {errors}")
    from benchmark_runner import show_leaderboard
    show_leaderboard(benchmark)
