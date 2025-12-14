#!/usr/bin/env python3
"""
Maze parsing and validation functions.
"""

import re
from typing import List, Tuple, Dict, Set
from .constants import MAX_ROWS, MAX_COLS, MAX_CELLS, VALID_MAZE_CHARS, MazeParsingError


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