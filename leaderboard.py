#!/usr/bin/env python3
"""
Leaderboard Management System
Manages benchmark scores and rankings for multiple LLM models.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


class Leaderboard:
    """Manages benchmark scores and rankings."""
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the leaderboard.
        
        Args:
            data_file: Path to JSON file for persistence. 
                      Defaults to leaderboard.json in project root.
        """
        if data_file is None:
            data_file = Path(__file__).parent / "leaderboard.json"
        
        self.data_file = Path(data_file)
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load leaderboard data from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"models": {}, "meta": {"version": "1.0"}}
        return {"models": {}, "meta": {"version": "1.0"}}
    
    def _save(self):
        """Save leaderboard data to file."""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
    
    def save_to_markdown_file(self, filename: str = "LEADERBOARD.md"):
        """
        Save the leaderboard to a markdown file.
        
        Args:
            filename: The filename to save to. Defaults to LEADERBOARD.md in project root.
        """
        content = self.export_markdown()
        root_path = Path(__file__).parent
        file_path = root_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[LEADERBOARD] Updated {filename}")

    def add_result(
        self, 
        model_name: str, 
        benchmark: str, 
        score: float,
        details: Optional[Dict] = None
    ):
        """
        Add or update a benchmark result for a model.
        Supports multiple runs by appending to a list.
        
        Args:
            model_name: The model identifier (e.g., "openai/gpt-4")
            benchmark: The benchmark name (e.g., "maze")
            score: The numeric score
            details: Optional additional details about the run
        """
        if "models" not in self.data:
            self.data["models"] = {}
        
        if model_name not in self.data["models"]:
            self.data["models"][model_name] = {}
        
        # Initialize as list if not present
        if benchmark not in self.data["models"][model_name]:
            self.data["models"][model_name][benchmark] = []
            
        # Migrate old dict format to list if necessary
        current_data = self.data["models"][model_name][benchmark]
        if isinstance(current_data, dict):
            self.data["models"][model_name][benchmark] = [current_data]
        
        # Store the result
        self.data["models"][model_name][benchmark].append({
            "score": score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        })
        
        self._save()
        self.save_to_markdown_file()
    
    def get_result(self, model_name: str, benchmark: str) -> Optional[Dict]:
        """
        Get the most recent result for a model and benchmark.
        
        Args:
            model_name: The model identifier
            benchmark: The benchmark name
            
        Returns:
            Result dict or None if not found
        """
        data = self.data.get("models", {}).get(model_name, {}).get(benchmark)
        if not data:
            return None
        
        # Handle list format (return last item)
        if isinstance(data, list):
            return data[-1] if data else None
            
        # Handle legacy dict format
        return data
    
    def get_rankings(self, benchmark: str) -> List[Dict]:
        """
        Get ranked list of models for a specific benchmark.
        Includes all runs for each model.
        
        Args:
            benchmark: The benchmark name
            
        Returns:
            List of dicts with model info, sorted by score descending
        """
        rankings = []
        
        for model_name, benchmarks in self.data.get("models", {}).items():
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
    
    def get_all_benchmarks(self) -> List[str]:
        """Get list of all benchmarks that have results."""
        benchmarks = set()
        for model_benchmarks in self.data.get("models", {}).values():
            benchmarks.update(model_benchmarks.keys())
        return sorted(benchmarks)
    
    def remove_model(self, model_name: str) -> bool:
        """
        Remove a model from the leaderboard.
        
        Args:
            model_name: The model identifier
            
        Returns:
            True if removed, False if not found
        """
        if model_name in self.data.get("models", {}):
            del self.data["models"][model_name]
            self._save()
            self.save_to_markdown_file()
            return True
        return False
    
    def export_markdown(self, benchmark: Optional[str] = None) -> str:
        """
        Export leaderboard as markdown table.
        
        Args:
            benchmark: Specific benchmark to export, or None for all
            
        Returns:
            Markdown formatted string
        """
        lines = ["# 🏆 Benchmark Leaderboard\n"]
        
        benchmarks = [benchmark] if benchmark else self.get_all_benchmarks()
        
        if not benchmarks:
            lines.append("*No benchmark results yet.*\n")
            return "\n".join(lines)
        
        for bench in benchmarks:
            rankings = self.get_rankings(bench)
            
            if not rankings:
                continue
            
            lines.append(f"## {bench.title()} Benchmark\n")
            lines.append("| Rank | Model | Score | Time (s) |")
            lines.append("|------|-------|-------|----------|")
            
            for entry in rankings:
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
        
        return "\n".join(lines)
    
    def format_cli_table(self, benchmark: Optional[str] = None) -> str:
        """
        Format leaderboard for CLI display.
        
        Args:
            benchmark: Specific benchmark to display, or None for all
            
        Returns:
            Formatted string for terminal output
        """
        benchmarks = [benchmark] if benchmark else self.get_all_benchmarks()
        
        if not benchmarks:
            return "[LEADERBOARD] No benchmark results yet.\n"
        
        lines = []
        lines.append("=" * 60)
        lines.append("                    LEADERBOARD")
        lines.append("=" * 60)
        
        for bench in benchmarks:
            rankings = self.get_rankings(bench)
            
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Leaderboard Manager")
    parser.add_argument("--update", action="store_true", help="Regenerate LEADERBOARD.md from json")
    parser.add_argument("--benchmark", "-b", help="Filter by benchmark")
    
    args = parser.parse_args()
    
    lb = Leaderboard()
    
    if args.update:
        lb.save_to_markdown_file()
    else:
        print(lb.format_cli_table(args.benchmark))
