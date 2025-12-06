#!/usr/bin/env python3
"""
Strategic Maze Evaluator v2.0
Handles Advanced Logic: Switches, Teleporters, and Conditional Doors.
"""

import math
import time
import re
import json
from collections import deque
from typing import List, Tuple, Dict, Set, Optional

# --- Configuration ---
MAX_ROWS = 64
MAX_COLS = 64
# Valid chars: #, space, S, E, T, a-z, A-Z, O, Q, s, B, F, G, H, X, Y, Z
VALID_MAZE_CHARS = {
    '#', ' ', 'S', 'E', 'T', 'O', 'Q', 's', 'B', 'F', 'G', 'H', 'X', 'Y', 'Z'
} | set(chr(i) for i in range(ord('a'), ord('z') + 1)) | \
   set(chr(i) for i in range(ord('A'), ord('Z') + 1))

class MazeParsingError(Exception):
    pass

def parse_maze(text: str) -> List[str]:
    """Extracts maze from markdown or raw text."""
    if "```" in text:
        match = re.search(r'```(?:markdown|)?\n(.*?)\n```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    lines = [line for line in text.split('\n') if line.strip()]
    
    # Basic validation
    if not lines:
        raise MazeParsingError("No maze lines found.")
    
    # Normalize width
    max_width = max(len(line) for line in lines)
    grid = [line.ljust(max_width) for line in lines]
    
    # Character validation
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if char not in VALID_MAZE_CHARS:
                # Treat unknown chars as walls for safety, but warn
                # For strict mode, raise error. We'll replace with '#' to allow partial grading
                grid[r] = grid[r][:c] + '#' + grid[r][c+1:]
                
    return grid

def find_locations(grid: List[str]) -> Dict:
    """Locates all static elements."""
    locs = {
        'S': None, 'E': None, 'O': [], 'Q': [], 's': [], 
        'keys': {}, 'doors': {}, 'traps': [], 'bonus': []
    }
    
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if char == 'S': locs['S'] = (r, c)
            elif char == 'E': locs['E'] = (r, c)
            elif char == 'O': locs['O'].append((r, c))
            elif char == 'Q': locs['Q'].append((r, c))
            elif char == 's': locs['s'].append((r, c))
            elif char == 'T': locs['traps'].append((r, c))
            elif char in ['F', 'G', 'H']: locs['bonus'].append((r, c))
            elif 'a' <= char <= 'z': locs['keys'][char] = (r, c)
            elif 'A' <= char <= 'Z': locs['doors'][(r, c)] = char
            
    return locs

def solve_maze_strategic(grid: List[str], locs: Dict) -> Dict:
    """
    BFS with State: (row, col, frozenset(keys), switch_active)
    Handles:
    - O -> Q Teleportation
    - s -> switch_active = True
    - Doors A-Z (Keys)
    - Door X (2+ Keys)
    - Door Y (Switch)
    - Door Z (Switch + 1 Key)
    """
    start_pos = locs['S']
    end_pos = locs['E']
    
    if not start_pos or not end_pos:
        return {'solvable': False, 'reason': 'Missing S or E'}

    rows, cols = len(grid), len(grid[0])
    
    # State: (r, c, keys_held, switch_state)
    initial_state = (start_pos[0], start_pos[1], frozenset(), False)
    
    queue = deque([(initial_state, [])]) # state, path
    visited = set([initial_state])
    
    final_path = []
    keys_collected_final = set()
    bonuses_reached = set()
    
    # For O->Q logic: find nearest Q? Or any Q? 
    # Usually maze teleporters are 1:1 or 1:Many. 
    # Logic: If multiple O and Q, O maps to first available Q or treated as hub.
    # To simplify: Entering any 'O' teleports to the first 'Q' found (or stays if no Q).
    dest_q = locs['Q'][0] if locs['Q'] else None

    start_time = time.time()

    while queue:
        if time.time() - start_time > 5.0: # Timeout
            return {'solvable': False, 'reason': 'Timeout (Complexity too high)'}

        (r, c, keys, switch_on), path = queue.popleft()
        
        current_path = path + [(r, c)]
        
        # Check Bonus
        if grid[r][c] in ['F', 'G', 'H']:
            bonuses_reached.add(grid[r][c])

        # Check End
        if (r, c) == end_pos:
            return {
                'solvable': True,
                'path': current_path,
                'path_length': len(current_path),
                'keys': list(keys),
                'switch_used': switch_on,
                'bonuses': list(bonuses_reached)
            }

        # Determine possible next moves
        # Teleport logic: If we stepped on O, we INSTANTLY move to Q in next step logic?
        # Or we treat O as a tile that moves us.
        # Let's handle neighbours normally.
        
        shifts = [(-1,0), (1,0), (0,-1), (0,1)]
        
        for dr, dc in shifts:
            nr, nc = r + dr, c + dc
            
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
                
            char = grid[nr][nc]
            
            if char == '#': continue
            
            # Logic for next state variables
            n_keys = set(keys)
            n_switch = switch_on
            
            # 1. Update State based on cell content
            if 'a' <= char <= 'z':
                n_keys.add(char)
            elif char == 's':
                n_switch = True
            
            # 2. Check Passability (Doors)
            can_pass = True
            
            if 'A' <= char <= 'Z':
                # Standard Doors
                if len(char) == 1 and char not in ['S', 'E', 'O', 'Q', 'T', 'B', 'F', 'G', 'H', 'X', 'Y', 'Z']:
                    req_key = char.lower()
                    if req_key not in keys:
                        can_pass = False
                
                # Special Doors
                elif char == 'X': # Needs 2 keys
                    if len(keys) < 2: can_pass = False
                elif char == 'Y': # Needs Switch
                    if not switch_on: can_pass = False
                elif char == 'Z': # Needs Switch AND 1 Key
                    if not (switch_on and len(keys) >= 1): can_pass = False
            
            # Movable Block 'B' - Treat as passable for solving, 
            # assuming the user pushes it. (Simplified physics)
            if char == 'B':
                pass 

            if can_pass:
                # 3. Handle Teleporter Logic
                # If moving ONTO 'O', actual position becomes 'Q'
                final_nr, final_nc = nr, nc
                if char == 'O' and dest_q:
                    final_nr, final_nc = dest_q
                
                frozen_keys = frozenset(n_keys)
                state = (final_nr, final_nc, frozen_keys, n_switch)
                
                if state not in visited:
                    visited.add(state)
                    queue.append((state, current_path))

    return {'solvable': False, 'reason': 'No path found'}

def grade_maze(prompt_response: str) -> Dict:
    try:
        grid = parse_maze(prompt_response)
        rows = len(grid)
        cols = len(grid[0])
        grid_size = rows * cols
        
        locs = find_locations(grid)
        solution = solve_maze_strategic(grid, locs)
        
        score_breakdown = {}
        total_score = 0
        
        # 1. Ambition: 100 * log2(size)
        if grid_size > 0:
            ambition = 100 * math.log2(grid_size)
        else:
            ambition = 0
        score_breakdown['ambition'] = round(ambition, 2)
        total_score += ambition

        # 2. Strategic Innovation
        # +15 per Teleporter O (assuming pairs), +20 switch, +25 special door
        count_o = len(locs['O'])
        count_s = len(locs['s'])
        
        # Count X, Y, Z actually used in grid
        special_doors = 0
        for row in grid:
            for char in row:
                if char in ['X', 'Y', 'Z']:
                    special_doors += 1
                    
        innovation = (count_o * 15) + (count_s * 20) + (special_doors * 25)
        score_breakdown['innovation'] = innovation
        total_score += innovation

        # 3. Route Complexity (Base + Solved Keys)
        complexity = 0
        if solution['solvable']:
            # Points for keys collected
            complexity += len(solution['keys']) * 15
            # Points for using switch
            if solution['switch_used']:
                complexity += 30
        score_breakdown['complexity'] = complexity
        total_score += complexity

        # 4. Bonus Objectives
        bonus_pts = 0
        if solution['solvable']:
            bonus_pts = len(solution['bonuses']) * 75
        score_breakdown['bonus_objectives'] = bonus_pts
        total_score += bonus_pts

        # 5. Completion
        completion = 50 if solution['solvable'] else 0
        score_breakdown['completion'] = completion
        total_score += completion

        # 6. Path Efficiency
        efficiency = 0
        if solution['solvable'] and grid_size > 0:
            # Higher ratio of Path/Grid is usually bad, but we want "Optimized" path.
            # However, usually longer solution paths in Mazes = better puzzles.
            # Let's reward path length as a percentage of grid, capped.
            path_len = solution['path_length']
            # Reward utilization of space
            efficiency = (path_len / grid_size) * 100
        score_breakdown['path_utilization'] = round(efficiency, 2)
        total_score += efficiency

        # 7. Strategic Danger (Traps)
        # 5 points per trap, max 30
        trap_score = min(len(locs['traps']) * 5, 30)
        score_breakdown['danger'] = trap_score
        total_score += trap_score

        # Penalty for unsolvable
        if not solution['solvable']:
            total_score = 0
            score_breakdown['NOTE'] = f"Maze Unsolvable: {solution.get('reason')}"

        return {
            "total_score": round(total_score, 2),
            "breakdown": score_breakdown,
            "dimensions": f"{rows}x{cols}",
            "elements": {
                "keys": len(locs['keys']),
                "switches": count_s,
                "teleporters": count_o,
                "special_doors": special_doors
            },
            "path_found": solution['solvable']
        }

    except Exception as e:
        return {"error": str(e), "score": 0}

# --- Test Block ---
if __name__ == "__main__":
    # Example logic test
    sample_maze = """
    #######
    #S a O#
    ##### #
    #E Y s#
    #Q ####
    #######
    """
    print(json.dumps(grade_maze(sample_maze), indent=2))