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





def get_stateful_path(grid: List[str], start: Tuple[int, int], end: Tuple[int, int]) -> Tuple[Set[Tuple[int, int]], Set[str]]:
    """
    Find shortest path between two points considering keys/doors.
    Returns (path_positions, collected_keys) or (set(), set()) if unreachable.
    """
    rows, cols = len(grid), len(grid[0]) if grid else 0
    
    # State: (pos_r, pos_c, frozenset(keys))
    # Queue: (r, c, keys, path_history)
    start_keys = frozenset()
    queue = deque([(start[0], start[1], start_keys, [start])])
    visited = set([(start[0], start[1], start_keys)])
    
    while queue:
        r, c, keys, path = queue.popleft()
        
        # Check if we reached the target
        if (r, c) == end:
            return set(path), set(keys)
        
        # Current cell processing
        char = grid[r][c]
        new_keys = set(keys)
        
        # If standing on a key, collect it
        if 'a' <= char <= 'z':
            new_keys.add(char)
        
        frozen_new_keys = frozenset(new_keys)
        
        # Explore neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            if 0 <= nr < rows and 0 <= nc < len(grid[nr]):
                next_char = grid[nr][nc]
                
                # Check traversability
                if next_char == '#':
                    continue
                    
                # Check doors - require matching key
                if 'A' <= next_char <= 'Z' and next_char not in ['S', 'E', 'T', 'K', 'D']:
                    required_key = next_char.lower()
                    if required_key not in new_keys:
                        continue
                        
                # Check visited state
                if (nr, nc, frozen_new_keys) not in visited:
                    visited.add((nr, nc, frozen_new_keys))
                    queue.append((nr, nc, frozen_new_keys, path + [(nr, nc)]))
                    
    return set(), set()

def solve_maze_graph(grid: List[str], s_pos: Tuple[int, int], e_pos: Tuple[int, int]) -> Dict:
    """
    Solve the maze by finding the optimal sequence of key collections.
    Returns details about the solution path, collected keys, and complexity.
    """
    # Identify all interesting points
    keys_map = {}
    doors_map = {}
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if 'a' <= char <= 'z':
                keys_map[char] = (r, c)
            elif 'A' <= char <= 'Z':
                doors_map[char] = (r, c)
                
    # Full stateful BFS for entire maze solution
    # We want to find a path from S to E that maximizes "complexity" (key chains)
    # But for grading, we just want *the* shortest valid path to E first
    
    rows, cols = len(grid), len(grid[0])
    
    # Queue: (r, c, frozenset(keys), path_list)
    start_state = (s_pos[0], s_pos[1], frozenset())
    queue = deque([(s_pos[0], s_pos[1], frozenset(), [s_pos])])
    visited = {start_state: 0} # map state -> path length
    
    final_path = []
    final_keys = set()
    solved = False
    
    # Limit iterations to prevent hanging on huge mazes
    max_iter = 100000
    iter_count = 0
    
    while queue and iter_count < max_iter:
        iter_count += 1
        r, c, keys, path = queue.popleft()
        
        if (r, c) == e_pos:
            final_path = path
            final_keys = keys
            solved = True
            break
            
        # Update keys if on a key tile
        curr_char = grid[r][c]
        next_keys = set(keys)
        if 'a' <= curr_char <= 'z':
            next_keys.add(curr_char)
        frozen_keys = frozenset(next_keys)
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            if 0 <= nr < rows and 0 <= nc < len(grid[nr]):
                n_char = grid[nr][nc]
                
                # Wall check
                if n_char == '#':
                    continue
                    
                # Door check
                if 'A' <= n_char <= 'Z' and n_char not in ['S', 'E', 'T', 'K', 'D']:
                    if n_char.lower() not in next_keys:
                        continue
                        
                # State check
                new_state = (nr, nc, frozen_keys)
                if new_state not in visited:
                    visited[new_state] = len(path) + 1
                    queue.append((nr, nc, frozen_keys, path + [(nr, nc)]))
    
    # Calculate complexity chain
    # Check which key/door pairs were used effectively
    # A pair (k, D) is "used" if we have key k, and passed through door D
    used_pairs = 0
    used_doors = set()
    for r, c in final_path:
        char = grid[r][c]
        if 'A' <= char <= 'Z':
            if char not in used_doors:
                used_doors.add(char)
                # If we passed door D, and have key d, that's a valid chain link
                if char.lower() in final_keys:
                    used_pairs += 1
                    
    return {
        "solvable": solved,
        "path": final_path,
        "path_length": len(final_path),
        "keys_collected": list(final_keys),
        "chain_length": used_pairs
    }

def grade_maze(maze_text: str) -> Dict:
    """
    Main evaluation function implementing the v2 scoring system (Multi-Key).
    """
    try:
        # Parse the maze
        grid = parse_maze_from_text(maze_text)
        
        if not grid:
            return {"error": "No valid maze found", "score": -100}
        
        rows, cols = len(grid), len(grid[0]) if grid else 0
        
        # Check size limit
        MAX_ROWS = 32
        MAX_COLS = 32
        size_penalty = 0
        if rows > MAX_ROWS or cols > MAX_COLS:
            excess = (max(0, rows - MAX_ROWS) + max(0, cols - MAX_COLS))
            size_penalty = excess * 10 
        
        counts = count_elements(grid)
        s_pos = find_position(grid, 'S')
        e_pos = find_position(grid, 'E')
        
        if s_pos == (-1, -1):
            return {"error": "No start position 'S' found", "score": -100}
            
        # Analyze solution
        solution = solve_maze_graph(grid, s_pos, e_pos) if e_pos != (-1, -1) else {"solvable": False, "path": [], "path_length": 0, "keys_collected": [], "chain_length": 0}
        
        valid_path = set(solution["path"])
        
        # --- SCORING COMPONENTS ---
        
        scores = {}
        
        # 1. Ambition (Logarithmic)
        grid_size = rows * cols
        import math
        ambition_score = 100 * math.log2(grid_size) if grid_size > 0 else 0
        scores["ambition"] = ambition_score
        
        # 2. Complexity (Chain Length)
        # 50 points per Key/Door pair used
        chain_score = solution["chain_length"] * 50
        scores["complexity"] = chain_score
        
        # 3. Path Efficiency
        # (Path Length / Grid Size) * 100
        path_eff_score = 0
        if grid_size > 0 and solution["solvable"]:
            path_eff_score = (solution["path_length"] / grid_size) * 100
        scores["path_efficiency"] = path_eff_score
        
        # 4. Completion Bonus
        completion_score = 50 if solution["solvable"] else 0
        scores["completion"] = completion_score
        
        # 5. Danger (Diminishing)
        adjacent_traps = count_adjacent_traps(grid, valid_path)
        danger_score = 20 * math.sqrt(adjacent_traps) if adjacent_traps > 0 else 0
        scores["danger"] = danger_score
        
        # Structure Penalty (Traps > Walls)
        structure_penalty = 0
        if counts['T'] > counts['#']:
            structure_penalty = -0.5
            
        # Total
        base_score = (ambition_score + chain_score + path_eff_score + completion_score + danger_score)
        total_score = base_score * (1 + structure_penalty) - size_penalty
        
        # Result
        result = {
            "score": round(total_score, 2),
            "base_score": round(base_score, 2),
            "structure_penalty": structure_penalty,
            "components": {
                "ambition": {
                    "score": round(ambition_score, 2),
                    "description": f"Grid {rows}x{cols} -> 100*log2",
                },
                "complexity": {
                    "score": chain_score,
                    "description": f"{solution['chain_length']} Key/Door pairs solved x 50",
                    "details": {"keys_collected": solution["keys_collected"]}
                },
                "path_efficiency": {
                    "score": round(path_eff_score, 2),
                    "description": f"Length {solution['path_length']} / Size {grid_size}",
                },
                "completion": {
                    "score": completion_score,
                    "description": "Reached End 'E'",
                },
                "danger": {
                    "score": round(danger_score, 2),
                    "description": f"Traps on path: {adjacent_traps} (sqrt scaled)",
                }
            },
            "maze_info": {
                "dimensions": f"{rows}x{cols}",
                "solvable": solution["solvable"],
                "keys_collected": solution["keys_collected"]
            }
        }
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "score": -100}


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