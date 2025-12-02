You are an Architect AI in the "Gauntlet Maze Benchmark."
Your task is to generate a SINGLE ASCII maze that maximizes a continuous score based on structure, logic, and danger.

**The Scoring Rules:**
1.  **Ambition:** Points for Grid Size (Rows × Cols).
2.  **Complexity:** Points for the length of the valid path.
3.  **Danger:** +20 points for every Trap ('T') that is **immediately adjacent** to the valid path. (Traps not near the path are worth 0).
4.  **Objectives:** +50 each for reaching Key ('K'), Door ('D'), and End ('E').

**Strict Constraints (Violating these reduces score significantly):**
-   **Structure:** Walls ('#') must outnumber Traps ('T'). You cannot build walls out of traps.
-   **Logic:** The path must go S -> K -> D -> E.
-   **Solvability:** The maze *should* be solvable. (Partial credit is given for partial paths).

**Output Format:**
-   ONLY the maze grid in a markdown code block.
-   Use standard chars: '#', ' ', 'S', 'E', 'K', 'D', 'T'.