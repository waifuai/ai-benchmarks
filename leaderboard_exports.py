#!/usr/bin/env python3
"""
Leaderboard Exports
Export and display functionality for leaderboard data.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def export_markdown(lb_data: Dict, benchmark: Optional[str] = None) -> str:
    """
    Export leaderboard as markdown table.
    
    Args:
        lb_data: Leaderboard data dictionary
        benchmark: Specific benchmark to export, or None for all
        
    Returns:
        Markdown formatted string
    """
    lines = ["# 🏆 Benchmark Leaderboard\n"]
    
    # Get all benchmarks
    all_benchmarks = set()
    for model_benchmarks in lb_data.get("models", {}).values():
        all_benchmarks.update(model_benchmarks.keys())
    
    benchmarks = [benchmark] if benchmark else sorted(all_benchmarks)
    
    if not benchmarks:
        lines.append("*No benchmark results yet.*\n")
        return "\n".join(lines)
    
    for bench in benchmarks:
        rankings = get_rankings(lb_data, bench)
        
        if not rankings:
            continue
        
        # Separate successful runs (score > -100) from failed runs (score = -100)
        successful_models = [entry for entry in rankings if entry["score"] > -100]
        failed_models = [entry for entry in rankings if entry["score"] == -100]
        
        lines.append(f"## {bench.title()} Benchmark\n")
        
        # Successful models section
        if successful_models:
            lines.append("### 🏆 Successful Runs")
            lines.append("| Rank | Model | Score | Time (s) |")
            lines.append("|------|-------|-------|----------|")
            
            for entry in successful_models:
                # Medal for top 3
                rank_display = entry["rank"]
                if rank_display == 1:
                    rank_display = "🥇"
                elif rank_display == 2:
                    rank_display = "🥈"
                elif rank_display == 3:
                    rank_display = "🥉"
                
                # Get details
                details = entry.get("details", {})
                elapsed = details.get("elapsed_seconds", 0)
                
                lines.append(
                    f"| {rank_display} | {entry['model']} | "
                    f"{entry['score']:.2f} | {elapsed:.1f} |"
                )
            lines.append("")
        
        # Failed models section
        if failed_models:
            lines.append("### ❌ Failed Runs (Score: -100)")
            lines.append("| Rank | Model | Time (s) |")
            lines.append("|------|-------|----------|")
            
            for i, entry in enumerate(failed_models, 1):
                # Get details
                details = entry.get("details", {})
                elapsed = details.get("elapsed_seconds", 0)
                
                lines.append(
                    f"| {i} | {entry['model']} | {elapsed:.1f} |"
                )
            lines.append("")
    
    return "\n".join(lines)


def format_cli_table(lb_data: Dict, benchmark: Optional[str] = None) -> str:
    """
    Format leaderboard for CLI display.
    
    Args:
        lb_data: Leaderboard data dictionary
        benchmark: Specific benchmark to display, or None for all
        
    Returns:
        Formatted string for terminal output
    """
    # Get all benchmarks
    all_benchmarks = set()
    for model_benchmarks in lb_data.get("models", {}).values():
        all_benchmarks.update(model_benchmarks.keys())
    
    benchmarks = [benchmark] if benchmark else sorted(all_benchmarks)
    
    if not benchmarks:
        return "[LEADERBOARD] No benchmark results yet.\n"
    
    lines = []
    lines.append("=" * 60)
    lines.append("                    LEADERBOARD")
    lines.append("=" * 60)
    
    for bench in benchmarks:
        rankings = get_rankings(lb_data, bench)
        
        if not rankings:
            continue
        
        lines.append(f"\n[{bench.upper()}]")
        lines.append("-" * 50)
        lines.append(f"{'Rank':<6} {'Model':<30} {'Score':>10}")
        lines.append("-" * 50)
        
        for entry in rankings:
            rank = entry["rank"]
            if rank == 1:
                prefix = "[1st]"
            elif rank == 2:
                prefix = "[2nd]"
            elif rank == 3:
                prefix = "[3rd]"
            else:
                prefix = f"#{rank}"
            
            model = entry["model"]
            if len(model) > 28:
                model = model[:25] + "..."
            
            lines.append(f"{prefix:<6} {model:<30} {entry['score']:>10.2f}")
    
    lines.append("\n" + "=" * 60)
    
    return "\n".join(lines)


def get_rankings(lb_data: Dict, benchmark: str) -> List[Dict]:
    """
    Get ranked list of models for a specific benchmark.
    Includes all runs for each model.
    
    Args:
        lb_data: Leaderboard data dictionary
        benchmark: The benchmark name
        
    Returns:
        List of dicts with model info, sorted by score descending
    """
    rankings = []
    
    for model_name, benchmarks in lb_data.get("models", {}).items():
        if benchmark in benchmarks:
            result_data = benchmarks[benchmark]
            
            # Normalize to list
            results = result_data if isinstance(result_data, list) else [result_data]
            
            for result in results:
                rankings.append({
                    "model": model_name,
                    "score": result["score"],
                    "timestamp": result.get("timestamp", ""),
                    "details": result.get("details", {})
                })
    
    # Sort by score descending
    rankings.sort(key=lambda x: x["score"], reverse=True)
    
    # Add rank numbers
    for i, entry in enumerate(rankings, 1):
        entry["rank"] = i
    
    return rankings


def save_to_markdown_file(lb_data: Dict, filename: str = "LEADERBOARD.md"):
    """
    Save the leaderboard to a markdown file.
    
    Args:
        lb_data: Leaderboard data dictionary
        filename: The filename to save to. Defaults to LEADERBOARD.md in project root.
    """
    content = export_markdown(lb_data)
    root_path = Path(__file__).parent
    file_path = root_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[LEADERBOARD] Updated {filename}")