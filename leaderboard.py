#!/usr/bin/env python3
"""
Leaderboard Management System
Manages benchmark scores and rankings for multiple LLM models.
"""

import json
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
        
        # Update markdown file
        from leaderboard_exports import save_to_markdown_file
        save_to_markdown_file(self.data)
    
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
            
            # Update markdown file
            from leaderboard_exports import save_to_markdown_file
            save_to_markdown_file(self.data)
            return True
        return False
    
    def format_cli_table(self, benchmark: Optional[str] = None) -> str:
        """
        Format leaderboard for CLI display.
        
        Args:
            benchmark: Specific benchmark to display, or None for all
            
        Returns:
            Formatted string for terminal output
        """
        from leaderboard_exports import format_cli_table
        return format_cli_table(self.data, benchmark)
    
    def export_markdown(self, benchmark: Optional[str] = None) -> str:
        """
        Export leaderboard as markdown table.
        
        Args:
            benchmark: Specific benchmark to export, or None for all
            
        Returns:
            Markdown formatted string
        """
        from leaderboard_exports import export_markdown
        return export_markdown(self.data, benchmark)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Leaderboard Manager")
    parser.add_argument("--update", action="store_true", help="Regenerate LEADERBOARD.md from json")
    parser.add_argument("--benchmark", "-b", help="Filter by benchmark")
    
    args = parser.parse_args()
    
    lb = Leaderboard()
    
    if args.update:
        from leaderboard_exports import save_to_markdown_file
        save_to_markdown_file(lb.data)
    else:
        print(lb.format_cli_table(args.benchmark))
