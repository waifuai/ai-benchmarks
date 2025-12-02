#!/usr/bin/env python3
"""
Maze Gauntlet Evaluator
Implements the gradient scoring system for LLM spatial reasoning assessment.
"""

import numpy as np
import re
import json
from collections import deque
from typing import List, Tuple, Dict, Set


def parse_maze_from_text(text: str) -> List[str]:
    """
    Extract maze grid from LLM output text.
    Handles markdown code blocks and ragged rows.
    """
    # Extract content between triple backticks
    code_block_match = re.search(r'```(?:markdown|)?\n(.*?)\n```', text, re.DOTALL)
    if code_block_match:
        maze_text = code_block_match.group(1)
    else:
        # Try to find any ASCII maze-like content
        lines = text.strip().split('\n')
        maze_lines = []
        for line in lines:
            line = line.strip()
            if line and any(char in line for char in ['#', 'S', 'E', 'K', 'D', 'T', ' ']):
                maze_lines.append(line)
        maze_text = '\n'.join(maze_lines)
    
    if not maze_text:
        raise ValueError("No maze found in input text")
    
    # Split into rows and clean up
    rows = []
    for line in maze_text.split('\n'):
        line = line.strip()
        if line:
            rows.append(line)
    
    return rows


def count_elements(grid: List[str]) -> Dict[str, int]:
    """Count occurrences of each element in the maze."""
    counts = {'S': 0, 'E': 0, 'K': 0, 'D': 0, 'T': 0, '#': 0, ' ': 0}
    
    for row in grid:
        for char in row:
            if char in counts:
                counts[char] += 1
    
    return counts


def find_position(grid: List[str], target: str) -> Tuple[int, int]:
    """Find the position of a target character in the grid."""
    for i, row in enumerate(grid):
        for j, char in enumerate(row):
            if char == target:
                return (i, j)
    return (-1, -1)


def bfs_reachable(grid: List[str], start: Tuple[int, int]) -> Set[Tuple[int, int]]:
    """Calculate all reachable positions from start using BFS."""
    rows, cols = len(grid), len(grid[0]) if grid else 0
    reachable = set()
    queue = deque([start])
    visited = set([start])
    
    # Define valid movement characters (not walls or traps)
    valid_chars = {' ', 'S', 'E', 'K', 'D'}
    
    while queue:
        i, j = queue.popleft()
        reachable.add((i, j))
        
        # Check all four directions
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            
            if (0 <= ni < rows and 0 <= nj < len(grid[ni]) and 
                (ni, nj) not in visited and 
                grid[ni][nj] in valid_chars):
                visited.add((ni, nj))
                queue.append((ni, nj))
    
    return reachable


def get_valid_path(grid: List[str], start: Tuple[int, int]) -> Set[Tuple[int, int]]:
    """
    Calculate the valid path through the maze following S -> K -> D -> E sequence.
    Returns set of positions that form the valid path.
    """
    if start == (-1, -1):
        return set()
    
    # Find positions of all objectives
    s_pos = start
    k_pos = find_position(grid, 'K')
    d_pos = find_position(grid, 'D')
    e_pos = find_position(grid, 'E')
    
    # Calculate reachability from each objective
    s_reachable = bfs_reachable(grid, s_pos)
    
    # Check if K is reachable from S
    if k_pos not in s_reachable and k_pos != (-1, -1):
        # K is not reachable, return S's reachable area
        return s_reachable
    
    # If K is reachable, find path to K
    k_reachable = s_reachable
    if k_pos != (-1, -1):
        k_reachable = bfs_reachable_from_set(grid, s_reachable, k_pos)
    
    # Check if D is reachable from K
    if d_pos not in k_reachable and d_pos != (-1, -1):
        # D is not reachable, return K's reachable area
        return k_reachable
    
    # If D is reachable, find path to D
    d_reachable = k_reachable
    if d_pos != (-1, -1):
        d_reachable = bfs_reachable_from_set(grid, k_reachable, d_pos)
    
    # Check if E is reachable from D
    if e_pos not in d_reachable and e_pos != (-1, -1):
        # E is not reachable, return D's reachable area
        return d_reachable
    
    # E is reachable, return D's reach to E
    if e_pos != (-1, -1):
        return bfs_reachable_from_set(grid, d_reachable, e_pos)
    
    return d_reachable


def bfs_reachable_from_set(grid: List[str], start_set: Set[Tuple[int, int]], target: Tuple[int, int]) -> Set[Tuple[int, int]]:
    """Calculate reachability from a set of starting positions to a target."""
    if target in start_set:
        return bfs_reachable(grid, target)
    
    # Find closest reachable position to target
    min_dist = float('inf')
    closest_start = None
    
    for start in start_set:
        dist = abs(start[0] - target[0]) + abs(start[1] - target[1])
        if dist < min_dist:
            min_dist = dist
            closest_start = start
    
    if closest_start:
        return bfs_reachable(grid, closest_start)
    
    return set()


def calculate_proximity_bonus(grid: List[str], reachable: Set[Tuple[int, int]], target: str) -> float:
    """Calculate proximity bonus for unreachable objectives."""
    target_pos = find_position(grid, target)
    if target_pos == (-1, -1):
        return 0
    
    if target_pos in reachable:
        return 50  # Full bonus if reachable
    
    # Calculate minimum distance to reachable area
    min_dist = float('inf')
    for pos in reachable:
        dist = abs(pos[0] - target_pos[0]) + abs(pos[1] - target_pos[1])
        min_dist = min(min_dist, dist)
    
    if min_dist == float('inf'):
        return 0
    
    # Proximity bonus decreases with distance
    max_bonus = 50
    return max(0, max_bonus * (1 - min_dist / 20))  # Linear decrease over 20 steps


def count_adjacent_traps(grid: List[str], valid_path: Set[Tuple[int, int]]) -> int:
    """Count traps adjacent to the valid path."""
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


def grade_maze(maze_text: str) -> Dict:
    """
    Main evaluation function implementing the gradient scoring system.
    Returns a detailed JSON report with scores and explanations.
    """
    try:
        # Parse the maze
        grid = parse_maze_from_text(maze_text)
        
        if not grid:
            return {"error": "No valid maze found", "score": 0}
        
        rows, cols = len(grid), len(grid[0]) if grid else 0
        
        # Count elements
        counts = count_elements(grid)
        
        # Find start position
        s_pos = find_position(grid, 'S')
        if s_pos == (-1, -1):
            return {"error": "No start position 'S' found", "score": 0}
        
        # Calculate reachable areas
        reachable = bfs_reachable(grid, s_pos)
        valid_path = get_valid_path(grid, s_pos)
        
        # Calculate scores
        scores = {}
        penalties = {}
        
        # 1. Ambition Score (Grid Size)
        ambition_score = rows * cols
        scores["ambition"] = ambition_score
        
        # 2. Progress Score (Reachable Tiles)
        progress_score = len(reachable) * 2
        scores["progress"] = progress_score
        
        # 3. Objective Bonuses
        k_bonus = 50 if find_position(grid, 'K') in reachable else 0
        d_bonus = 50 if find_position(grid, 'D') in reachable else 0
        e_bonus = 50 if find_position(grid, 'E') in reachable else 0
        
        objective_score = k_bonus + d_bonus + e_bonus
        scores["objectives"] = objective_score
        scores["key_bonus"] = k_bonus
        scores["door_bonus"] = d_bonus
        scores["end_bonus"] = e_bonus
        
        # 4. Proximity Bonuses for Unreachable Objectives
        k_proximity = calculate_proximity_bonus(grid, reachable, 'K')
        d_proximity = calculate_proximity_bonus(grid, reachable, 'D')
        e_proximity = calculate_proximity_bonus(grid, reachable, 'E')
        
        proximity_score = k_proximity + d_proximity + e_proximity
        scores["proximity"] = proximity_score
        
        # 5. Danger Score (Adjacent Traps)
        adjacent_traps = count_adjacent_traps(grid, valid_path)
        danger_score = adjacent_traps * 20
        scores["danger"] = danger_score
        
        # 6. Structure Penalties
        if counts['T'] > counts['#']:
            structure_penalty = -0.5  # 50% penalty
            penalties["structure"] = structure_penalty
        else:
            structure_penalty = 0
        
        # Calculate total score
        base_score = (scores["ambition"] + scores["progress"] + 
                     scores["objectives"] + scores["proximity"] + scores["danger"])
        total_score = base_score * (1 + structure_penalty)
        
        # Prepare result
        result = {
            "score": round(total_score, 2),
            "base_score": base_score,
            "structure_penalty": structure_penalty,
            "components": {
                "ambition": {
                    "score": scores["ambition"],
                    "description": f"Grid size: {rows} × {cols} = {rows * cols} points",
                    "details": {"rows": rows, "cols": cols}
                },
                "progress": {
                    "score": scores["progress"],
                    "description": f"{len(reachable)} reachable tiles × 2 points each",
                    "details": {"reachable_tiles": len(reachable)}
                },
                "objectives": {
                    "score": scores["objectives"],
                    "description": "Objectives found on valid path",
                    "details": {
                        "key_found": k_bonus > 0,
                        "door_found": d_bonus > 0,
                        "end_found": e_bonus > 0
                    }
                },
                "proximity": {
                    "score": scores["proximity"],
                    "description": "Partial credit for unreachable objectives",
                    "details": {
                        "key_proximity": round(k_proximity, 2),
                        "door_proximity": round(d_proximity, 2),
                        "end_proximity": round(e_proximity, 2)
                    }
                },
                "danger": {
                    "score": scores["danger"],
                    "description": f"{adjacent_traps} traps adjacent to valid path × 20 points",
                    "details": {"adjacent_traps": adjacent_traps}
                }
            },
            "penalties": penalties,
            "maze_info": {
                "dimensions": f"{rows}×{cols}",
                "elements": counts,
                "solvable": len(valid_path) > len(reachable) * 0.1,  # Arbitrary threshold
                "complexity_ratio": len(valid_path) / max(1, len(reachable))
            }
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "score": 0}


if __name__ == "__main__":
    # Test the evaluator
    sample_maze = """
    ```markdown
    S  ##   T
     # # #  
     # K #  
     # # #  
      D   E
    ```
    """
    
    result = grade_maze(sample_maze)
    print(json.dumps(result, indent=2))