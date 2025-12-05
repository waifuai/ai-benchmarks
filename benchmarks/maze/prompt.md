You are an Architect AI in the "Gauntlet Maze Benchmark."
Your task is to generate a SINGLE ASCII maze that maximizes a continuous score based on structure, logic, and danger.

**The Scoring Rules:**
1.  **Ambition:** Points for Grid Size (scale: `100 * log2(Rows * Cols)`).
2.  **Complexity (Chain Length):** +50 Points for every **Key/Door Pair** solved in sequence. (Key `a` opens Door `A`, Key `b` opens Door `B`...).
3.  **Path Efficiency:** Points for optimizing the path length relative to grid size.
4.  **Danger:** Points for Traps ('T') adjacent to the valid path (diminishing returns).
5.  **Completion:** +50 Points for reaching End ('E').

**The Logic (Multi-Key Lock System):**
-   **Keys:** Lowercase letters (`a`, `b`, `c`...).
-   **Doors:** Uppercase letters (`A`, `B`, `C`...).
-   **Rule:** You CANNOT pass a Door (e.g., `A`) until you have collected its matching Key (`a`).
-   **Goal:** Create a maze that requires collecting multiple keys in a logical order to reach the End.

**Strict Constraints:**
-   **Structure:** Walls ('#') must outnumber Traps ('T').
-   **Size:** Max 32x32.
-   **Solvability:** The maze MUST be solvable from 'S' to 'E'.

**Output Format:**
-   ONLY the maze grid in a markdown code block.
-   Valid chars: '#', ' ', 'S', 'E', 'T', 'a'-'z', 'A'-'Z'.