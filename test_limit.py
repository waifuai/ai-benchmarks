from benchmarks.maze.evaluator import grade_maze
import json

def test_size_limit():
    # Create a 33x33 maze
    large_maze_rows = []
    for _ in range(33):
        large_maze_rows.append("#" * 33)
    large_maze = "\n".join(large_maze_rows)
    
    print("Testing 33x33 maze...")
    result = grade_maze(large_maze)
    print(json.dumps(result, indent=2))
    
    if "error" in result and "exceeds limit" in result["error"]:
        print("PASS: Large maze rejected correctly.")
    else:
        print("FAIL: Large maze was not rejected.")

    # Create a 10x10 maze
    small_maze = """
    ```
    S  #######
    #        #
    # K      #
    #      D #
    #        #
    #######  E
    ```
    """
    print("\nTesting small maze...")
    result = grade_maze(small_maze)
    # print(json.dumps(result, indent=2))
    
    if "error" not in result:
        print("PASS: Small maze accepted.")
    else:
        print(f"FAIL: Small maze rejected with error: {result.get('error')}")

if __name__ == "__main__":
    test_size_limit()
