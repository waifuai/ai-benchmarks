# Strategic Maze Elements Design

## Current Problems
- Excessive repetitive traps that look silly and unstrategic
- Limited tactical depth - only basic key/door mechanics
- Scoring encourages trap-spamming over intelligent design
- No dynamic or interactive elements
- Aesthetically poor repetitive patterns

## New Strategic Elements

### 1. Teleporters
- **Symbol**: 'O' (origin) and 'Q' (destination)
- **Mechanics**: Single-use teleporters that transport player to matching destination
- **Strategic Use**: Quick traversal, bypassing obstacles, creating multi-path strategies
- **Scoring**: Bonus for creative teleportation routes

### 2. Switches and Gates  
- **Switch Symbol**: 's' (toggle switch)
- **Gate Symbol**: 'S' (initially closed, opens when switch activated)
- **Mechanics**: Stepping on switch toggles all gates of that type
- **Strategic Use**: Complex route planning, temporary access, timing puzzles
- **Scoring**: Complexity bonus for multi-switch gate puzzles

### 3. Movable Blocks
- **Symbol**: 'B' (movable block)
- **Mechanics**: Can be pushed into adjacent empty spaces to create bridges or barriers
- **Strategic Use**: Bridge gaps, block paths, create temporary platforms
- **Scoring**: Innovation bonus for creative block usage

### 4. Multiple Exit Conditions
- **Primary Exit**: 'E' (standard end point)
- **Bonus Exits**: 'F', 'G', 'H' (require specific collections: flowers, gems, etc.)
- **Mechanics**: Reaching different exits provides different scoring bonuses
- **Strategic Use**: Multiple path strategies, collection puzzles
- **Scoring**: Bonus for completing bonus objectives

### 5. Conditional Paths
- **Special Doors**: 'X', 'Y', 'Z' (require multiple keys or specific conditions)
- **Mechanics**: Complex unlock conditions (e.g., need 2 of 3 keys, or key + switch activation)
- **Strategic Use**: Advanced planning, resource management, conditional logic
- **Scoring**: High complexity bonuses for multi-condition puzzles

## Enhanced Scoring System

### New Scoring Components
1. **Strategic Innovation** (0-100 pts): Creative use of new elements
2. **Route Complexity** (0-150 pts): Multiple viable solution paths
3. **Resource Management** (0-100 pts): Efficient use of keys, switches, blocks
4. **Bonus Objectives** (0-75 pts): Completing optional challenges
5. **Puzzle Sophistication** (0-125 pts): Advanced conditional logic

### Reduced Traps Importance
- Lower maximum trap scoring (max 30 pts instead of unlimited)
- Remove trap density penalties (focus on placement quality)
- Score traps based on strategic placement, not quantity

## Implementation Phases
1. Update evaluator to parse new elements
2. Implement pathfinding for new mechanics
3. Create enhanced scoring algorithm
4. Update prompt to guide strategic maze creation
5. Test with complex maze examples