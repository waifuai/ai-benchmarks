#!/usr/bin/env python3
"""
Maze Gauntlet Evaluator
Implements the gradient scoring system for LLM spatial reasoning assessment.
"""

import numpy as np
import re
import json
import math
import time
from collections import deque
from typing import List, Tuple, Dict, Set, Optional


# Validation constants
MAX_ROWS = 32
MAX_COLS = 32
MAX_CELLS = MAX_ROWS * MAX_COLS
VALID_MAZE_CHARS = {'#', 'S', 'E', 'K', 'D', 'T'} | set(chr(i) for i in range(ord('a'), ord('z') + 1)) | set(chr(i) for i in range(ord('A'), ord('Z') + 1))


class MazeParsingError(Exception):
    """Custom exception for maze parsing failures."""
    pass


def validate_maze_characters(grid: List[str]) -> None:
    """Validate that all characters in the grid are valid maze characters."""
    invalid_chars = set()
    
    for row_idx, row in enumerate(grid):
        for col_idx, char in enumerate(row):
            if char not in VALID_MAZE_CHARS and char != ' ':
                invalid_chars.add(f"'{char}' at ({row_idx}, {col_idx})")
    
    if invalid_chars:
        raise MazeParsingError(f"Invalid characters found in maze: {', '.join(sorted(invalid_chars))}")


def normalize_maze_grid(grid: List[str]) -> List[str]:
    """
    Normalize the maze grid by:
    1. Removing empty rows
    2. Trimming whitespace
    3. Padding short rows to match the longest row
    """
    # Remove completely empty rows
    cleaned_rows = [row.strip() for row in grid if row.strip()]
    
    if not cleaned_rows:
        raise MazeParsingError("No valid maze rows found after cleaning")
    
    # Find the maximum width
    max_width = max(len(row) for row in cleaned_rows)
    
    # Pad rows to match maximum width
    normalized_rows = []
    for row in cleaned_rows:
        if len(row) < max_width:
            # Pad with spaces to the right
            normalized_rows.append(row + ' ' * (max_width - len(row)))
        else:
            normalized_rows.append(row)
    
    return normalized_rows


def parse_maze_from_text(text: str) -> List[str]:
    """
    Extract and normalize maze grid from LLM output text.
    Handles various markdown formats, code blocks, and ragged rows.
    """
    if not text or not text.strip():
        raise MazeParsingError("Empty or whitespace-only input provided")
    
    # Strategy 1: Extract content between triple backticks (allow leading whitespace)
    code_block_pattern = r'\s*```(?:markdown|)?\n(.*?)\n```'
    code_block_match = re.search(code_block_pattern, text, re.DOTALL)
    if code_block_match:
        maze_text = code_block_match.group(1).strip()
    else:
        # Strategy 2: Extract maze-like content from the text
        lines = text.strip().split('\n')
        maze_lines = []
        
        for line in lines:
            line = line.strip()
            if line and any(char in line for char in ['#', 'S', 'E', 'K', 'D', 'T', ' '] + [chr(i) for i in range(ord('a'), ord('z') + 1)] + [chr(i) for i in range(ord('A'), ord('Z') + 1)]):
                # Additional filtering: skip lines that are clearly not maze content
                if len(line) >= 3 and not line.startswith('##') and not line.upper().startswith('TIME:'):  # Skip markdown headers and metadata
                    maze_lines.append(line)
        
        if not maze_lines:
            raise MazeParsingError("No maze-like content found in input text. Expected maze with characters like #, S, E, K, D, T")
        
        maze_text = '\n'.join(maze_lines)
    
    if not maze_text:
        raise MazeParsingError("No maze content extracted from text")
    
    # Split into rows and clean up
    raw_rows = [line.strip() for line in maze_text.split('\n') if line.strip()]
    
    if len(raw_rows) == 0:
        raise MazeParsingError("No maze rows found after splitting text")
    
    # Validate maze dimensions
    if len(raw_rows) > MAX_ROWS:
        raise MazeParsingError(f"Maze too tall: {len(raw_rows)} rows (maximum: {MAX_ROWS})")
    
    max_width = max(len(row) for row in raw_rows)
    if max_width > MAX_COLS:
        raise MazeParsingError(f"Maze too wide: {max_width} columns (maximum: {MAX_COLS})")
    
    if len(raw_rows) * max_width > MAX_CELLS:
        raise MazeParsingError(f"Maze too large: {len(raw_rows)}x{max_width} = {len(raw_rows) * max_width} cells (maximum: {MAX_CELLS})")
    
    # Normalize the grid (pad short rows, clean up)
    normalized_grid = normalize_maze_grid(raw_rows)
    
    # Validate characters
    validate_maze_characters(normalized_grid)
    
    return normalized_grid


def count_elements(grid: List[str]) -> Dict[str, int]:
    """Count occurrences of each element in the maze."""
    counts = {'S': 0, 'E': 0, 'K': 0, 'D': 0, 'T': 0, '#': 0, ' ': 0}
    
    # Add lowercase and uppercase letter counts
    for i in range(ord('a'), ord('z') + 1):
        counts[chr(i)] = 0
    for i in range(ord('A'), ord('Z') + 1):
        counts[chr(i)] = 0
    
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


def find_all_positions(grid: List[str], targets: Set[str]) -> Dict[str, List[Tuple[int, int]]]:
    """Find all positions of target characters in the grid."""
    positions = {}
    for target in targets:
        positions[target] = []
    
    for i, row in enumerate(grid):
        for j, char in enumerate(row):
            if char in targets:
                positions[char].append((i, j))
    
    return positions


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


def get_stateful_path_with_timeout(
    grid: List[str], 
    start: Tuple[int, int], 
    end: Tuple[int, int],
    timeout_seconds: float = 5.0
) -> Dict:
    """
    Find shortest path between two points considering keys/doors with timeout protection.
    Returns detailed solution information or timeout indication.
    """
    start_time = time.time()
    
    rows, cols = len(grid), len(grid[0]) if grid else 0
    
    # State: (pos_r, pos_c, frozenset(keys))
    start_keys = frozenset()
    queue = deque([(start[0], start[1], start_keys, [start])])
    visited = set([(start[0], start[1], start_keys)])
    
    # Track keys and doors for the maze
    keys_map = {}
    doors_map = {}
    for r in range(rows):
        for c in range(cols):
            char = grid[r][c]
            if 'a' <= char <= 'z':
                keys_map[char] = (r, c)
            elif 'A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D']:
                doors_map[char] = (r, c)
    
    final_path = []
    final_keys = set()
    solved = False
    used_pairs = 0
    used_doors = set()
    
    # Limit iterations to prevent hanging
    max_iter = rows * cols * 10  # Reasonable limit based on maze size
    iter_count = 0
    
    while queue and iter_count < max_iter:
        # Check timeout
        if time.time() - start_time > timeout_seconds:
            return {
                "solvable": False,
                "path": [],
                "path_length": 0,
                "keys_collected": [],
                "chain_length": 0,
                "timeout": True
            }
        
        iter_count += 1
        r, c, keys, path = queue.popleft()
        
        # Check if we reached the target
        if (r, c) == end:
            final_path = path
            final_keys = set(keys)
            solved = True
            break
        
        # Update keys if on a key tile
        curr_char = grid[r][c]
        new_keys = set(keys)
        if 'a' <= curr_char <= 'z':
            new_keys.add(curr_char)
        
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
    
    # Calculate complexity chain if solved
    if solved:
        for r, c in final_path:
            char = grid[r][c]
            if 'A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D']:
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
        "chain_length": used_pairs,
        "timeout": False
    }


def solve_maze_graph(grid: List[str], s_pos: Tuple[int, int], e_pos: Tuple[int, int]) -> Dict:
    """
    Solve the maze by finding the optimal sequence of key collections.
    Returns details about the solution path, collected keys, and complexity.
    """
    if s_pos == (-1, -1) or e_pos == (-1, -1):
        return {
            "solvable": False,
            "path": [],
            "path_length": 0,
            "keys_collected": [],
            "chain_length": 0,
            "timeout": False
        }
    
    return get_stateful_path_with_timeout(grid, s_pos, e_pos)


def grade_maze(maze_text: str) -> Dict:
    """
    Main evaluation function implementing the improved scoring system with robust parsing.
    """
    try:
        # Parse the maze with enhanced error handling
        grid = parse_maze_from_text(maze_text)
        
        if not grid:
            return {"error": "No valid maze found", "score": -100}
        
        rows, cols = len(grid), len(grid[0]) if grid else 0
        
        # Validate maze structure
        counts = count_elements(grid)
        
        # Check for required elements
        s_pos = find_position(grid, 'S')
        e_pos = find_position(grid, 'E')
        
        if s_pos == (-1, -1):
            return {"error": "No start position 'S' found", "score": -100}
        
        if e_pos == (-1, -1):
            return {"error": "No end position 'E' found", "score": -100}
        
        # Check for multiple starts or ends
        starts = count_elements(grid).get('S', 0)
        ends = count_elements(grid).get('E', 0)
        
        if starts != 1:
            return {"error": f"Must have exactly one start 'S' position (found: {starts})", "score": -100}
        
        if ends != 1:
            return {"error": f"Must have exactly one end 'E' position (found: {ends})", "score": -100}
        
        # Analyze solution with timeout protection
        solution = solve_maze_graph(grid, s_pos, e_pos)
        
        if solution.get("timeout", False):
            return {"error": "Maze solving timeout - maze may be too complex", "score": -100}
        
        valid_path = set(solution["path"])
        
        # --- SCORING COMPONENTS ---
        scores = {}
        
        # 1. Ambition (Logarithmic) - size-based scoring
        grid_size = rows * cols
        ambition_score = 100 * math.log2(grid_size) if grid_size > 0 else 0
        scores["ambition"] = round(ambition_score, 2)
        
        # 2. Complexity (Chain Length) - key/door pairs solved
        chain_score = solution["chain_length"] * 50
        scores["complexity"] = chain_score
        
        # 3. Path Efficiency - optimized path length relative to grid size
        path_eff_score = 0
        if grid_size > 0 and solution["solvable"]:
            path_eff_score = (solution["path_length"] / grid_size) * 100
        scores["path_efficiency"] = round(path_eff_score, 2)
        
        # 4. Completion Bonus - reaching the end
        completion_score = 50 if solution["solvable"] else 0
        scores["completion"] = completion_score
        
        # 5. Danger (Diminishing) - traps adjacent to valid path
        adjacent_traps = count_adjacent_traps(grid, valid_path)
        danger_score = 20 * math.sqrt(adjacent_traps) if adjacent_traps > 0 else 0
        scores["danger"] = round(danger_score, 2)
        
        # Structure Penalty (Traps > Walls)
        structure_penalty = 0
        if counts['T'] > counts['#']:
            structure_penalty = -0.5
        
        # Calculate total with proper penalty application
        base_score = (ambition_score + chain_score + path_eff_score + completion_score + danger_score)
        total_score = base_score * (1 + structure_penalty)
        
        # Result with detailed breakdown
        result = {
            "score": round(total_score, 2),
            "base_score": round(base_score, 2),
            "structure_penalty": structure_penalty,
            "components": {
                "ambition": {
                    "score": round(ambition_score, 2),
                    "description": f"Grid {rows}x{cols} (size: {grid_size}) -> 100*log2",
                    "details": {"rows": rows, "cols": cols, "grid_size": grid_size}
                },
                "complexity": {
                    "score": chain_score,
                    "description": f"{solution['chain_length']} Key/Door pairs solved x 50",
                    "details": {
                        "keys_collected": solution["keys_collected"],
                        "path_length": solution["path_length"]
                    }
                },
                "path_efficiency": {
                    "score": round(path_eff_score, 2),
                    "description": f"Optimal path uses {solution['path_length']}/{grid_size} cells ({round((solution['path_length']/grid_size)*100, 1)}%)",
                    "details": {
                        "path_length": solution["path_length"],
                        "grid_size": grid_size,
                        "efficiency_ratio": round(solution["path_length"]/grid_size, 4) if grid_size > 0 else 0
                    }
                },
                "completion": {
                    "score": completion_score,
                    "description": "Successfully reached End 'E'" if solution["solvable"] else "Failed to reach End 'E'",
                    "details": {"solvable": solution["solvable"]}
                },
                "danger": {
                    "score": round(danger_score, 2),
                    "description": f"{adjacent_traps} strategic traps on solution path (sqrt scaled)",
                    "details": {"adjacent_traps": adjacent_traps, "scaling": "sqrt"}
                }
            },
            "maze_info": {
                "dimensions": f"{rows}x{cols}",
                "solvable": solution["solvable"],
                "keys_collected": solution["keys_collected"],
                "chain_length": solution["chain_length"],
                "path_length": solution["path_length"],
                "elements": {
                    "S": counts.get('S', 0),
                    "E": counts.get('E', 0),
                    "K": counts.get('K', 0),
                    "D": counts.get('D', 0),
                    "T": counts.get('T', 0),
                    "#": counts.get('#', 0)
                },
                "complexity_ratio": round((counts['T'] + counts['#']) / grid_size, 3) if grid_size > 0 else 0,
                "timeout": solution.get("timeout", False)
            }
        }
        
        return result
        
    except MazeParsingError as e:
        return {
            "error": f"Maze parsing failed: {str(e)}", 
            "score": -100,
            "error_type": "parsing"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Unexpected error during evaluation: {str(e)}", 
            "score": -100,
            "error_type": "evaluation"
        }


if __name__ == "__main__":
    # Test the improved evaluator with properly sized mazes
    sample_maze = """```markdown
S  T   ##
 #  # #   
 #  K # # D  
 #  # # # #  
     T   E
```"""
    
    print("Testing improved maze evaluator...")
    try:
        result = grade_maze(sample_maze)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
        
    # Test edge case
    print("\n" + "="*50)
    print("Testing edge case with irregular rows...")
    edge_case = """```markdown
S  T   ##
 #  # #   
 #  K # # D  
 #  # # # 
     T   E
```"""
    
    try:
        result2 = grade_maze(edge_case)
        print(json.dumps(result2, indent=2))
    except Exception as e:
        print(f"Edge case test failed: {e}")