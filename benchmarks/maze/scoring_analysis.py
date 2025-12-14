#!/usr/bin/env python3
"""
Scoring analysis functions for strategic maze evaluation.
"""

from typing import List, Dict, Set
from .strategic_maze import StrategicMaze


def count_adjacent_traps(grid: List[str], valid_path: Set[tuple]) -> int:
    """Count traps adjacent to the valid path (enhanced for strategic placement)."""
    adjacent_traps = 0
    
    for i, j in valid_path:
        # Check all four adjacent positions
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            
            # Check bounds and if it's a trap
            if (0 <= ni < len(grid) and 0 <= nj < len(grid[ni]) and 
                grid[ni][nj] == 'T'):
                adjacent_traps += 1
    
    return adjacent_traps


def analyze_strategic_innovation(maze: StrategicMaze, solution: Dict) -> Dict:
    """Analyze strategic elements usage and innovation."""
    innovation_score = 0
    innovation_details = {
        'teleporters_used': 0,
        'switches_activated': 0,
        'bonus_exits_reached': 0,
        'conditional_doors_used': 0,
        'unique_strategies': []
    }
    
    strategic_usage = solution.get('strategic_usage', {})
    
    # Teleportation innovation
    teleport_count = strategic_usage.get('teleports', 0)
    if teleport_count > 0:
        innovation_score += min(teleport_count * 15, 60)
        innovation_details['teleporters_used'] = teleport_count
        innovation_details['unique_strategies'].append(f"Used {teleport_count} teleporters")
    
    # Switch complexity
    switch_count = strategic_usage.get('switches_activated', 0)
    if switch_count > 0:
        innovation_score += min(switch_count * 20, 80)
        innovation_details['switches_activated'] = switch_count
        innovation_details['unique_strategies'].append(f"Activated {switch_count} switches")
    
    # Bonus objective analysis
    if solution.get('solvable'):
        path_set = set(solution['path'])
        
        # Check bonus exits reached
        for exit_char, exit_pos in maze.bonus_exits.items():
            if exit_pos in path_set:
                innovation_score += 25
                innovation_details['bonus_exits_reached'] += 1
                innovation_details['unique_strategies'].append(f"Reached bonus exit {exit_char}")
        
        # Check conditional doors used
        for door_char, door_pos in maze.conditional_doors.items():
            if door_pos in path_set:
                innovation_score += 30
                innovation_details['conditional_doors_used'] += 1
                innovation_details['unique_strategies'].append(f"Used conditional door {door_char}")
    
    return {
        'score': innovation_score,
        'details': innovation_details
    }


def analyze_route_complexity(maze: StrategicMaze, solution: Dict) -> Dict:
    """Analyze multiple viable solution paths and complexity."""
    complexity_score = 0
    complexity_details = {
        'alternative_paths': 0,
        'branching_factor': 0,
        'strategic_decisions': 0
    }
    
    if not solution.get('solvable'):
        return {'score': 0, 'details': complexity_details}
    
    # Simplified complexity analysis based on maze structure
    strategic_elements_count = (
        len(maze.teleporters_o) + 
        len(maze.switches) + 
        len(maze.movable_blocks) + 
        len(maze.bonus_exits) + 
        len(maze.conditional_doors)
    )
    
    # Higher complexity for more strategic elements
    complexity_score = min(strategic_elements_count * 12, 150)
    
    # Additional bonus for key/door complexity - FIXED VERSION
    keys_and_doors = 0
    for r in range(maze.rows):
        for c in range(maze.cols):
            if c < len(maze.grid[r]):
                char = maze.get_cell((r, c))
                if ('a' <= char <= 'z' or 
                    ('A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D', 'O', 'Q', 'F', 'G', 'H', 'X', 'Y', 'Z'])):
                    keys_and_doors += 1
    
    complexity_score += min(keys_and_doors * 8, 100)
    
    complexity_details['strategic_decisions'] = strategic_elements_count + keys_and_doors
    
    return {
        'score': complexity_score,
        'details': complexity_details
    }