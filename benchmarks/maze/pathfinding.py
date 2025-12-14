#!/usr/bin/env python3
"""
Strategic pathfinding algorithms for maze solving.
"""

import time
from collections import deque
from typing import List, Tuple, Dict, Set, FrozenSet
from .strategic_maze import StrategicMaze


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