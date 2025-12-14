#!/usr/bin/env python3
"""
Enhanced Strategic Maze Evaluator (Refactored)
Implements intelligent maze generation assessment with strategic elements.
Main entry point that orchestrates all maze evaluation functionality.
"""

import json
import math
from typing import Dict

# Import from refactored modules (relative imports for package)
from .maze_parsing import parse_maze_from_text, find_position, count_elements
from .strategic_maze import StrategicMaze
from .pathfinding import StrategicPathfinder
from .scoring_analysis import count_adjacent_traps, analyze_strategic_innovation, analyze_route_complexity
from .constants import MazeParsingError


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