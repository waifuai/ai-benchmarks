#!/usr/bin/env python3
"""
Constants and validation for maze evaluation.
"""

# Validation constants
MAX_ROWS = 64
MAX_COLS = 64
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