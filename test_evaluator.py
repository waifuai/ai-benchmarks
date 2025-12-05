#!/usr/bin/env python3
"""
Test script for debugging the maze evaluator improvements.
"""

import sys
sys.path.append('.')

from benchmarks.maze.evaluator import VALID_MAZE_CHARS, grade_maze, parse_maze_from_text

def test_character_validation():
    """Test the character validation fix."""
    print("=== Testing Character Validation ===")
    print(f"VALID_MAZE_CHARS type: {type(VALID_MAZE_CHARS)}")
    print(f"Has space: {' ' in VALID_MAZE_CHARS}")
    print(f"Has #: {'#' in VALID_MAZE_CHARS}")
    print(f"Contains backtick: {'`' in VALID_MAZE_CHARS}")
    print(f"Number of chars: {len(VALID_MAZE_CHARS)}")
    print(f"Sample chars: {sorted(list(VALID_MAZE_CHARS))[:10]}")
    print()

def test_simple_maze():
    """Test a simple valid maze."""
    print("=== Testing Simple Valid Maze ===")
    simple_maze = """```markdown
S  T   
 #  # #   
 #  K # # D  
 #  # # # #  
     T   E
```"""
    
    try:
        result = grade_maze(simple_maze)
        print(f"Score: {result.get('score', 'N/A')}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print("SUCCESS: Maze parsed and scored!")
            print(f"Components: {list(result.get('components', {}).keys())}")
    except Exception as e:
        print(f"Exception: {e}")
    print()

def test_regex_issue():
    """Test the regex extraction issue."""
    print("=== Testing Regex Extraction ===")
    test_text = """Here is my maze:

```markdown
S  T   
 #  # #   
 #  K # # D  
     T   E
```
Some more text"""
    
    try:
        grid = parse_maze_from_text(test_text)
        print(f"Parsed {len(grid)} rows")
        print(f"First row: '{grid[0]}'")
        print(f"Max width: {max(len(row) for row in grid)}")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    test_character_validation()
    test_simple_maze()
    test_regex_issue()