#!/usr/bin/env python3
"""
Debug script to test regex extraction.
"""

import re

def test_regex_extraction():
    """Test the regex extraction logic."""
    test_text = """
    Here is my maze design for the Gauntlet Benchmark:

    ```markdown
    S  T   ##
     #  # #   
     #  K # # D  
     #  # # # #  
         T   E
    ```
    This maze demonstrates strategic trap placement and logical progression.
    """
    
    print("=== Original Text ===")
    print(repr(test_text))
    print()
    
    # Test the current regex
    code_block_pattern = r'```(?:markdown|)?\n(.*?)\n```'
    code_block_match = re.search(code_block_pattern, test_text, re.DOTALL)
    
    if code_block_match:
        maze_text = code_block_match.group(1).strip()
        print("=== Extracted Maze Text ===")
        print(repr(maze_text))
        print()
        
        # Split into rows and check each one
        rows = [line.strip() for line in maze_text.split('\n') if line.strip()]
        print("=== Parsed Rows ===")
        for i, row in enumerate(rows):
            print(f"Row {i}: '{row}' (len={len(row)})")
        print()
        
        max_width = max(len(row) for row in rows) if rows else 0
        print(f"Max width: {max_width}")
        
    else:
        print("No regex match found!")

if __name__ == "__main__":
    test_regex_extraction()