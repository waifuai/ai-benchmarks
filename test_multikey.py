from benchmarks.maze.evaluator import grade_maze, solve_maze_graph
import json

def test_multikey_logic():
    # Test 1: Simple Chain (Valid) - Strict Corridor
    print("\n--- Test 1: Simple Chain (Valid) ---")
    maze_valid = """
    ```
    #######
    #S a A#
    ##### #
    #  E  #
    #######
    ```
    """
    # Now row 2 is ##### #. 
    # S(1,1) a(1,3) A(1,5). 
    # Path MUST go through A to get to (1,6) aka space, then down to (2,6) space, then to E?
    # Wait, let's make it simpler.
    maze_valid = """
    ```
    #######
    #S a A#
    #####E#
    #######
    ```
    """
    # S -> a -> A -> E. No other way.
    
    result = grade_maze(maze_valid)
    print(f"Score: {result['score']}")
    print(f"Components: {json.dumps(result['components'], indent=2)}")
    
    if result['components']['complexity']['score'] >= 50 and result['components']['completion']['score'] == 50:
        print("PASS: Correctly awarded points for chain and completion.")
    else:
        print("FAIL: Did not award correct points.")
        print(f"Collected Keys: {result['maze_info']['keys_collected']}")

    # Test 2: Door before Key (Invalid)
    print("\n--- Test 2: Door Before Key (Invalid) ---")
    maze_invalid = """
    ```
    #######
    #S A a#
    #####E#
    #######
    ```
    """
    # S -> A (blocked) -> a -> E.
    result = grade_maze(maze_invalid)
    print(f"Score: {result['score']}")
    print(f"Solvable: {result['maze_info']['solvable']}")
    
    if not result['maze_info']['solvable']:
        print("PASS: Correctly identified as unsolvable.")
    else:
        print("FAIL: Incorrectly marked as solvable.")

    # Test 3: Multi-Key Chain (Valid)
    print("\n--- Test 3: Multi-Key Chain (Valid) ---")
    maze_chain = """
    ```
    ###########
    #S a A b B#
    #########E#
    ###########
    ```
    """
    result = grade_maze(maze_chain)
    print(f"Score: {result['score']}")
    print(f"Chain Description: {result['components']['complexity']['description']}")
    
    # Needs to find 2 pairs
    if "2 Key/Door pairs" in result['components']['complexity']['description']:
        print("PASS: Identified 2 key/door pairs.")
    else:
        print(f"FAIL: Expected 2 pairs, got: {result['components']['complexity']['description']}")

if __name__ == "__main__":
    test_multikey_logic()
