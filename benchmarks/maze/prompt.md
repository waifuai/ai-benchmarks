You are an Architect AI in the "Strategic Maze Benchmark."
Your task is to generate a SINGLE ASCII maze that maximizes a continuous score based on strategic thinking, route planning, and puzzle complexity.

**The Enhanced Scoring Rules:**
1. **Ambition:** Points for Grid Size + Strategic Elements (`100 * log2(Rows * Cols)`).
2. **Strategic Innovation:** +15 points per teleporter pair, +20 per switch, +25 per conditional door used.
3. **Route Complexity:** Points for requiring backtracking and key collection chains.
4. **Bonus Objectives:** +75 points per optional exit reachable ('F', 'G', 'H').
5. **Completion:** +50 Points for reaching End ('E').
6. **Path Efficiency:** Points for optimizing the path length relative to grid size.
7. **Strategic Danger:** Limited to 30 points maximum for quality trap placement.

**Strategic Elements & Logic:**
- **Start/End:** 'S' (Start) and 'E' (End).
- **Standard Walls:** '#'
- **Traps:** 'T' (Avoid these).
- **Teleporters:** 'O' (Entry) -> 'Q' (Exit). One-way instant travel.
- **Switch:** 's' (lowercase). Toggles state to OPEN 'Y' and 'Z' doors.
- **Movable Blocks:** 'B' (Counts as a wall, but conceptually movable for puzzle logic).
- **Bonus Exits:** 'F', 'G', 'H' (Optional targets for extra points).

**Lock & Key System:**
- **Standard Keys:** Lowercase letters (`a`, `b`, `c`...)
- **Standard Doors:** Uppercase letters (`A`, `B`, `C`...) -> Require matching key (a->A).
- **Conditional Door 'X':** Requires holding at least 2 standard keys to pass.
- **Conditional Door 'Y':** Requires activating Switch 's' to pass.
- **Conditional Door 'Z':** Requires BOTH Switch 's' AND at least 1 standard key.

**Strict Constraints:**
- **Structure:** Walls must outline the valid paths clearly.
- **Size:** Max 32x32 (for reliable rendering).
- **Solvability:** The maze MUST be solvable from 'S' to 'E'.
- **Constraint:** 'S' (Start) and 's' (Switch) are different. Do not confuse them.

**Output Format:**
- ONLY the maze grid in a markdown code block.
- Valid chars: '#', ' ', 'S', 'E', 'T', 'a'-'z', 'A'-'Z', 'O', 'Q', 's', 'B', 'F', 'G', 'H', 'X', 'Y', 'Z'.

**Scoring Focus:** Strategic thinking > Trap placement > Size > Path efficiency