#!/usr/bin/env python3
"""
Benchmark Utilities
Logging, file I/O, and general utility functions.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


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


def log_message(message: str):
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


def save_llm_output(model_name: str, benchmark: str, llm_output: str) -> Path:
    """Save LLM output to output directory and return file path."""
    safe_model_name = model_name.replace("/", "_").replace(":", "_")
    output_dir = Path(__file__).parent / "output" / safe_model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{benchmark}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(llm_output)
    
    return output_file


def save_score_file(model_name: str, benchmark: str, result: Dict) -> Path:
    """Save detailed score results to JSON file."""
    safe_model_name = model_name.replace("/", "_").replace(":", "_")
    output_dir = Path(__file__).parent / "output" / safe_model_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    score_file = output_dir / f"{benchmark}_score.json"
    clean_result = {k: v for k, v in result.items() if k != "llm_response"}
    
    with open(score_file, 'w', encoding='utf-8') as f:
        json.dump(clean_result, f, indent=2)
    
    return score_file


def format_score_report(result: Dict) -> str:
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