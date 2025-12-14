#!/usr/bin/env python3
"""
StrategicMaze class for handling maze with strategic elements.
"""

from typing import List, Tuple, Dict, Set
from .maze_parsing import find_all_positions


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