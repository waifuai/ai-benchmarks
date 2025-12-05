#!/usr/bin/env python3
"""
Enhanced Strategic Maze Evaluator (Fixed Version)
Implements intelligent maze generation assessment with strategic elements.
"""

import numpy as np
import re
import json
import math
import time
from collections import deque
from typing import List, Tuple, Dict, Set, Optional, FrozenSet


# Validation constants
MAX_ROWS = 32
MAX_COLS = 32
MAX_CELLS = MAX_ROWS * MAX_COLS

# Core maze characters
VALID_MAZE_CHARS = {
    '#', 'S', 'E', 'K', 'D', 'T',  # Original elements
    'O', 'Q',  # Teleporters (origin, destination)
    's', 'B',  # Switch, Movable block
    'F', 'G', 'H',  # Bonus exits
    'X', 'Y', 'Z'  # Conditional doors
} | set(chr(i) for i in range(ord('a'), ord('z') + 1)) | set(chr(i) for i in range(ord('A'), ord('Z') + 1))


class MazeParsingError(Exception):
    """Custom exception for maze parsing failures."""
    pass


class StrategicMaze:
    """Enhanced maze with strategic elements."""
    
    def __init__(self, grid: List[str]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        
        # Strategic element maps
        self.teleporters_o = {}  # 'O' -> position
        self.teleporters_q = {}  # 'Q' -> position
        self.switches = {}  # 's' -> position
        self.movable_blocks = []  # List of 'B' positions
        self.bonus_exits = {}  # 'F', 'G', 'H' -> position
        self.conditional_doors = {}  # 'X', 'Y', 'Z' -> position
        
        self._analyze_elements()
    
    def _analyze_elements(self):
        """Analyze all strategic elements in the maze."""
        for r in range(self.rows):
            for c in range(self.cols):
                if c >= len(self.grid[r]):
                    continue
                    
                char = self.grid[r][c]
                pos = (r, c)
                
                # Teleporters
                if char == 'O':
                    self.teleporters_o[pos] = len(self.teleporters_o)
                elif char == 'Q':
                    self.teleporters_q[pos] = len(self.teleporters_q)
                
                # Switches
                elif char == 's':
                    self.switches[pos] = True
                
                # Movable blocks
                elif char == 'B':
                    self.movable_blocks.append(pos)
                
                # Bonus exits
                elif char in 'FGH':
                    self.bonus_exits[char] = pos
                
                # Conditional doors
                elif char in 'XYZ':
                    self.conditional_doors[char] = pos
    
    def is_wall(self, pos: Tuple[int, int]) -> bool:
        """Check if position is a wall."""
        r, c = pos
        return c >= len(self.grid[r]) or self.grid[r][c] == '#'
    
    def is_traversable(self, pos: Tuple[int, int]) -> bool:
        """Check if position is traversable (not a wall or out of bounds)."""
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < len(self.grid[r]) and self.grid[r][c] != '#'
    
    def get_cell(self, pos: Tuple[int, int]) -> str:
        """Get character at position."""
        r, c = pos
        if r >= self.rows or c >= len(self.grid[r]):
            return ' '
        return self.grid[r][c]
    
    def teleport_destinations(self, teleporter_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get all destinations for a teleporter."""
        teleporter_num = self.teleporters_o.get(teleporter_pos)
        if teleporter_num is None:
            return []
        
        return [pos for pos, num in self.teleporters_q.items() if num == teleporter_num]


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
            if line and any(char in line for char in ['#', 'S', 'E', 'K', 'D', 'T', 'O', 'Q', 's', 'B', 'F', 'G', 'H', 'X', 'Y', 'Z', ' '] + 
                          [chr(i) for i in range(ord('a'), ord('z') + 1)] + [chr(i) for i in range(ord('A'), ord('Z') + 1)]):
                # Additional filtering: skip lines that are clearly not maze content
                if len(line) >= 3 and not line.startswith('##') and not line.upper().startswith('TIME:'):
                    maze_lines.append(line)
        
        if not maze_lines:
            raise MazeParsingError("No maze-like content found in input text. Expected maze with strategic elements")
        
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


def count_elements(grid: List[str]) -> Dict[str, int]:
    """Count occurrences of each element in the maze."""
    counts = {
        'S': 0, 'E': 0, 'K': 0, 'D': 0, 'T': 0, '#': 0, ' ': 0,
        'O': 0, 'Q': 0, 's': 0, 'B': 0, 'F': 0, 'G': 0, 'H': 0,
        'X': 0, 'Y': 0, 'Z': 0
    }
    
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


class StrategicPathfinder:
    """Enhanced pathfinding with strategic elements."""
    
    def __init__(self, maze: StrategicMaze):
        self.maze = maze
        self.rows = maze.rows
        self.cols = maze.cols
    
    def solve_with_strategic_elements(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        timeout_seconds: float = 5.0
    ) -> Dict:
        """Solve maze considering all strategic elements."""
        start_time = time.time()
        
        # Enhanced state: (pos_r, pos_c, frozenset(keys), frozenset(activated_switches), frozenset(used_teleporters))
        start_keys = frozenset()
        start_switches = frozenset()
        start_teleporters = frozenset()
        
        initial_state = (start[0], start[1], start_keys, start_switches, start_teleporters)
        queue = deque([(initial_state, [start])])
        visited = set([initial_state])
        
        # Track maze elements
        keys_map = {}
        doors_map = {}
        
        for r in range(self.rows):
            for c in range(self.cols):
                if c >= len(self.maze.grid[r]):
                    continue
                    
                char = self.maze.grid[r][c]
                if 'a' <= char <= 'z':
                    keys_map[char] = (r, c)
                elif 'A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D', 'O', 'Q', 'F', 'G', 'H', 'X', 'Y', 'Z']:
                    doors_map[char] = (r, c)
        
        final_path = []
        final_keys = set()
        final_switches = set()
        final_teleporters_used = set()
        solved = False
        used_pairs = 0
        used_doors = set()
        strategic_moves = {'teleports': 0, 'switches_activated': 0, 'blocks_moved': 0}
        
        # Limit iterations
        max_iter = self.rows * self.cols * 20  # Higher limit for complex mazes
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
                    "timeout": True,
                    "strategic_usage": strategic_moves
                }
            
            iter_count += 1
            (r, c, keys, switches, used_teles), path = queue.popleft()
            
            # Check if we reached the target
            if (r, c) == end:
                final_path = path
                final_keys = set(keys)
                final_switches = set(switches)
                final_teleporters_used = set(used_teles)
                solved = True
                break
            
            # Update keys if on a key tile
            curr_char = self.maze.get_cell((r, c))
            new_keys = set(keys)
            if 'a' <= curr_char <= 'z':
                new_keys.add(curr_char)
            
            # Handle switches
            new_switches = set(switches)
            if curr_char == 's':
                new_switches.add((r, c))
                strategic_moves['switches_activated'] += 1
            
            # Explore neighbors and special movements
            self._explore_possible_moves(
                r, c, new_keys, new_switches, set(used_teles), path,
                queue, visited, strategic_moves
            )
        
        # Calculate complexity if solved
        if solved:
            for r, c in final_path:
                char = self.maze.get_cell((r, c))
                
                # Count key/door pairs
                if 'A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D', 'O', 'Q', 'F', 'G', 'H', 'X', 'Y', 'Z']:
                    if char not in used_doors:
                        used_doors.add(char)
                        if char.lower() in final_keys:
                            used_pairs += 1
                
                # Count teleport usage
                elif char == 'O' and (r, c) in final_teleporters_used:
                    strategic_moves['teleports'] += 1
        
        return {
            "solvable": solved,
            "path": final_path,
            "path_length": len(final_path),
            "keys_collected": list(final_keys),
            "chain_length": used_pairs,
            "switches_activated": list(final_switches),
            "teleporters_used": list(final_teleporters_used),
            "strategic_usage": strategic_moves,
            "timeout": False
        }
    
    def _explore_possible_moves(self, r, c, keys, switches, used_teles, path, queue, visited, strategic_moves):
        """Explore all possible moves including strategic elements."""
        current_pos = (r, c)
        curr_char = self.maze.get_cell(current_pos)
        
        # 1. Regular movement (4 directions)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            next_pos = (nr, nc)
            
            if self._is_valid_move(next_pos, keys, switches):
                self._queue_state(nr, nc, keys, switches, used_teles, path, queue, visited)
        
        # 2. Teleportation
        if curr_char == 'O' and current_pos not in used_teles:
            destinations = self.maze.teleport_destinations(current_pos)
            for dest in destinations:
                if self.maze.is_traversable(dest):
                    new_used_teles = set(used_teles)
                    new_used_teles.add(current_pos)
                    new_path = path + [dest]
                    new_state = (dest[0], dest[1], frozenset(keys), frozenset(switches), frozenset(new_used_teles))
                    
                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, new_path))
                        strategic_moves['teleports'] += 1
        
        # 3. Movable block pushing (simplified)
        if curr_char == 'B':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                push_pos = (r + dr, c + dc)
                land_pos = (r + 2*dr, c + 2*dc)
                
                # Can push into empty space
                if (self.maze.get_cell(push_pos) == ' ' and 
                    self.maze.is_traversable(land_pos) and
                    self.maze.get_cell(land_pos) != '#'):
                    
                    strategic_moves['blocks_moved'] += 1
                    new_path = path + [push_pos, land_pos]
                    new_state = (land_pos[0], land_pos[1], frozenset(keys), frozenset(switches), frozenset(used_teles))
                    
                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, new_path))
    
    def _is_valid_move(self, pos: Tuple[int, int], keys: Set[str], switches: Set[Tuple[int, int]]) -> bool:
        """Check if a position is a valid move."""
        if not self.maze.is_traversable(pos):
            return False
        
        char = self.maze.get_cell(pos)
        
        # Walls
        if char == '#':
            return False
        
        # Doors requiring keys
        if 'A' <= char <= 'Z' and char not in ['S', 'E', 'T', 'K', 'D', 'O', 'Q', 'F', 'G', 'H', 'X', 'Y', 'Z']:
            required_key = char.lower()
            if required_key not in keys:
                return False
        
        # Special doors that may require switches
        elif char in 'XYZ':
            # Conditional doors could require switches, keys, or both
            if char == 'X' and len(keys) < 2:  # Requires 2+ keys
                return False
            elif char == 'Y' and not switches:  # Requires switch activation
                return False
            elif char == 'Z' and (len(keys) < 1 or not switches):  # Requires both
                return False
        
        return True
    
    def _queue_state(self, r, c, keys, switches, used_teles, path, queue, visited):
        """Queue a new state for exploration."""
        new_state = (r, c, frozenset(keys), frozenset(switches), frozenset(used_teles))
        if new_state not in visited:
            visited.add(new_state)
            queue.append((new_state, path + [(r, c)]))


def count_adjacent_traps(grid: List[str], valid_path: Set[Tuple[int, int]]) -> int:
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


def grade_strategic_maze(maze_text: str) -> Dict:
    """
    Enhanced evaluation function with strategic scoring system.
    """
    try:
        # Parse the maze
        grid = parse_maze_from_text(maze_text)
        
        if not grid:
            return {"error": "No valid maze found", "score": -100}
        
        # Create strategic maze object
        maze = StrategicMaze(grid)
        
        rows, cols = maze.rows, maze.cols
        
        # Validate required elements
        s_pos = find_position(grid, 'S')
        e_pos = find_position(grid, 'E')
        
        if s_pos == (-1, -1):
            return {"error": "No start position 'S' found", "score": -100}
        
        if e_pos == (-1, -1):
            return {"error": "No end position 'E' found", "score": -100}
        
        # Check for multiple starts or ends
        counts = count_elements(grid)
        
        if counts['S'] != 1:
            return {"error": f"Must have exactly one start 'S' position (found: {counts['S']})", "score": -100}
        
        if counts['E'] != 1:
            return {"error": f"Must have exactly one end 'E' position (found: {counts['E']})", "score": -100}
        
        # Solve maze with strategic elements
        pathfinder = StrategicPathfinder(maze)
        solution = pathfinder.solve_with_strategic_elements(s_pos, e_pos)
        
        if solution.get("timeout", False):
            return {"error": "Maze solving timeout - maze may be too complex", "score": -100}
        
        valid_path = set(solution["path"]) if solution["path"] else set()
        
        # --- ENHANCED SCORING SYSTEM ---
        scores = {}
        grid_size = rows * cols
        
        # 1. Ambition (Enhanced) - size and strategic element bonuses
        ambition_score = 100 * math.log2(grid_size) if grid_size > 0 else 0
        strategic_bonus = (
            len(maze.teleporters_o) * 10 + 
            len(maze.switches) * 15 + 
            len(maze.bonus_exits) * 20 + 
            len(maze.conditional_doors) * 25
        )
        ambition_score += strategic_bonus
        scores["ambition"] = round(ambition_score, 2)
        
        # 2. Strategic Innovation (NEW) - creative use of strategic elements
        innovation_analysis = analyze_strategic_innovation(maze, solution)
        scores["strategic_innovation"] = innovation_analysis['score']
        
        # 3. Route Complexity (Enhanced) - multiple solution paths
        complexity_analysis = analyze_route_complexity(maze, solution)
        scores["route_complexity"] = complexity_analysis['score']
        
        # 4. Traditional Complexity - key/door pairs
        chain_score = solution["chain_length"] * 50
        scores["complexity"] = chain_score
        
        # 5. Path Efficiency - optimized path length
        path_eff_score = 0
        if grid_size > 0 and solution["solvable"]:
            path_eff_score = (solution["path_length"] / grid_size) * 100
        scores["path_efficiency"] = round(path_eff_score, 2)
        
        # 6. Completion Bonus - reaching the end
        completion_score = 50 if solution["solvable"] else 0
        scores["completion"] = completion_score
        
        # 7. Strategic Danger (Reduced importance) - quality over quantity
        adjacent_traps = count_adjacent_traps(grid, valid_path)
        danger_score = min(adjacent_traps * 5, 30)  # Much lower max score
        scores["danger"] = round(danger_score, 2)
        
        # 8. Bonus Objectives (NEW) - optional challenges
        bonus_score = 0
        if solution["solvable"]:
            # Award points for reaching bonus exits
            path_set = set(solution['path'])
            for exit_char in maze.bonus_exits:
                if maze.bonus_exits[exit_char] in path_set:
                    bonus_score += 75
        scores["bonus_objectives"] = bonus_score
        
        # Structure Penalty (Relaxed)
        structure_penalty = 0
        if counts['T'] > counts['#'] * 2:  # More lenient threshold
            structure_penalty = -0.25  # Reduced penalty
        
        # Calculate total score
        base_score = (ambition_score + scores["strategic_innovation"] + 
                     scores["route_complexity"] + chain_score + path_eff_score + 
                     completion_score + danger_score + bonus_score)
        total_score = base_score * (1 + structure_penalty)
        
        # Result with enhanced breakdown
        result = {
            "score": round(total_score, 2),
            "base_score": round(base_score, 2),
            "structure_penalty": structure_penalty,
            "components": {
                "ambition": {
                    "score": round(ambition_score, 2),
                    "description": f"Grid {rows}x{cols} + strategic elements",
                    "details": {
                        "rows": rows, "cols": cols, "grid_size": grid_size,
                        "strategic_bonus": strategic_bonus
                    }
                },
                "strategic_innovation": {
                    "score": scores["strategic_innovation"],
                    "description": "Creative use of strategic maze elements",
                    "details": innovation_analysis['details']
                },
                "route_complexity": {
                    "score": scores["route_complexity"],
                    "description": "Multiple solution paths and strategic complexity",
                    "details": complexity_analysis['details']
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
                    "description": f"Strategic trap placement (quality over quantity)",
                    "details": {"adjacent_traps": adjacent_traps}
                },
                "bonus_objectives": {
                    "score": bonus_score,
                    "description": "Completed optional strategic challenges",
                    "details": {"bonus_exits_reached": innovation_analysis['details']['bonus_exits_reached']}
                }
            },
            "maze_info": {
                "dimensions": f"{rows}x{cols}",
                "solvable": solution["solvable"],
                "keys_collected": solution["keys_collected"],
                "chain_length": solution["chain_length"],
                "path_length": solution["path_length"],
                "strategic_elements": {
                    "teleporters": len(maze.teleporters_o),
                    "switches": len(maze.switches),
                    "movable_blocks": len(maze.movable_blocks),
                    "bonus_exits": len(maze.bonus_exits),
                    "conditional_doors": len(maze.conditional_doors)
                },
                "elements": {
                    "S": counts.get('S', 0),
                    "E": counts.get('E', 0),
                    "K": counts.get('K', 0),
                    "D": counts.get('D', 0),
                    "T": counts.get('T', 0),
                    "#": counts.get('#', 0),
                    "O": counts.get('O', 0),
                    "Q": counts.get('Q', 0),
                    "s": counts.get('s', 0),
                    "B": counts.get('B', 0),
                    "F": counts.get('F', 0),
                    "G": counts.get('G', 0),
                    "H": counts.get('H', 0),
                    "X": counts.get('X', 0),
                    "Y": counts.get('Y', 0),
                    "Z": counts.get('Z', 0)
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


# Backwards compatibility function
def grade_maze(maze_text: str) -> Dict:
    """Legacy function that calls the enhanced evaluator."""
    return grade_strategic_maze(maze_text)


if __name__ == "__main__":
    # Test the enhanced evaluator with strategic maze
    strategic_maze = """```markdown
S  O   ##
 #  s #   
 #  K # # X  
 #  # # # #  
     B   E
Q     F
```"""
    
    print("Testing enhanced strategic maze evaluator...")
    try:
        result = grade_strategic_maze(strategic_maze)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()