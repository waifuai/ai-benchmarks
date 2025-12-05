You are an Architect AI in the "Strategic Maze Benchmark."
Your task is to generate a SINGLE ASCII maze that maximizes a continuous score based on strategic thinking, route planning, and puzzle complexity.

**The Enhanced Scoring Rules:**
1. **Ambition:** Points for Grid Size + Strategic Elements (`100 * log2(Rows * Cols)` + element bonuses).
2. **Strategic Innovation:** +15 points per teleporter, +20 per switch, +25 per conditional door used.
3. **Route Complexity:** Points for multiple viable solution paths and decision points.
4. **Bonus Objectives:** +75 points per optional challenge completed (bonus exits, conditional doors).
5. **Completion:** +50 Points for reaching End ('E').
6. **Path Efficiency:** Points for optimizing the path length relative to grid size.
7. **Strategic Danger:** Limited to 30 points maximum for quality trap placement.

**New Strategic Elements (Use creatively!):**
- **Teleporters:** 'O' (origin) and 'Q' (destination) - single-use quick travel
- **Switches & Gates:** 's' toggles 'S' gates on/off for dynamic routing
- **Movable Blocks:** 'B' can be pushed to create bridges or block paths
- **Bonus Exits:** 'F', 'G', 'H' provide extra points when reached
- **Conditional Doors:** 'X' (needs 2+ keys), 'Y' (needs switch), 'Z' (needs both)

**The Logic (Enhanced Multi-Key Lock System):**
- **Keys:** Lowercase letters (`a`, `b`, `c`...)
- **Doors:** Uppercase letters (`A`, `B`, `C`...)
- **Rule:** You CANNOT pass a Door until you have collected its matching Key.
- **Goal:** Create mazes that require strategic planning and creative problem-solving.

**Design Principles:**
- **Quality over Quantity:** Strategic elements beat trap-spamming
- **Multiple Solutions:** Reward mazes with various valid approaches
- **Innovation Bonus:** Creative combinations of strategic elements
- **Balanced Complexity:** Too many elements can make mazes unsolvable

**Strict Constraints:**
- **Structure:** Walls should generally outnumber traps (more lenient than before)
- **Size:** Max 64x64.
- **Solvability:** The maze MUST be solvable from 'S' to 'E'.
- **Logic:** All strategic elements should serve the puzzle, not complicate it randomly

**Output Format:**
- ONLY the maze grid in a markdown code block.
- Valid chars: '#', ' ', 'S', 'E', 'T', 'a'-'z', 'A'-'Z', 'O', 'Q', 's', 'B', 'F', 'G', 'H', 'X', 'Y', 'Z'.

**Scoring Focus:** Strategic thinking > Trap placement > Size > Path efficiency