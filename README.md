# AI Benchmark Repository

A specialized testing suite for evaluating Large Language Models (LLMs) on spatial reasoning tasks through gradient scoring systems.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run benchmark on LLM output file
python run_benchmark.py --input path_to_llm_output.txt

# Run and save to leaderboard
python run_benchmark.py --input llm_output.txt --add-to-leaderboard

# View the leaderboard
python run_benchmark.py --leaderboard
```

## 🏆 Leaderboard System

The benchmark includes a leaderboard to track and compare model performance:

- **Add results**: Use `--add-to-leaderboard` when running benchmarks
- **View rankings**: Use `--leaderboard` to display current standings
- **Persistent storage**: Results saved to `leaderboard.json`

## 🧪 Current Benchmarks

### The "Maze Gauntlet" - LLM Spatial Reasoning Challenge

Unlike traditional maze benchmarks that use binary pass/fail scoring, the Maze Gauntlet implements a **Gradient Scoring** system that evaluates how well LLMs can generate complex, solvable mazes with specific state-dependency rules.

#### Philosophy
Most maze benchmarks are binary (Pass/Fail). This is a **Gradient Benchmark** that rewards:
- **Ambition**: Grid size and complexity
- **Logic**: Proper S → K → D → E path progression  
- **Danger**: Strategic trap placement adjacent to valid paths

## 📊 Scoring System

### The Maze Gauntlet Scoring Components:

1. **Ambition** (Grid Size)
   - Points: 100 × log₂(Rows × Cols)
   - Rewards larger mazes but with logarithmic scaling to prevent exponential runaway

2. **Progress** (Path Logic)
   - 2 points per reachable tile
   - +50 bonus for Key ('K') 
   - +50 bonus for Door ('D')
   - +50 bonus for End ('E')

3. **Path Efficiency** (New)
   - Points: (Shortest Valid Path Length / Grid Size) × 100
   - Rewards mazes that use the available space efficiently for the solution

4. **Danger** (Strategic Placement)
   - Points: 20 × sqrt(Adjacent Traps)
   - Diminishing returns preventing "trap spamming"
   - Only traps near the valid solution path count

5. **Logic Penalties**
   - If Traps > Walls: -50% score penalty
   - Path must follow S → K → D → E sequence

6. **Proximity Bonuses**
   - Partial credit for **unreachable** objectives based on distance to reachable areas
   - No double-counting for reached objectives

7. **Constraints**
   - Maximum maze size: **64×64** (mazes exceeding this limit score 0)

## 🔧 Architecture

```
ai-benchmark/
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── requirements.txt        # Dependencies
├── run_benchmark.py        # CLI Entry point
├── leaderboard.py          # Leaderboard management
├── leaderboard.json        # Stored benchmark results
└── benchmarks/
    ├── __init__.py
    └── maze/
        ├── __init__.py
        ├── prompt.md       # The "Anti-Cheese" Prompt
        └── evaluator.py    # Gradient Scoring Logic
```

## 🎯 Adding New Benchmarks

This repository is designed to be modular. To add new benchmarks:

1. Create a new directory under `benchmarks/`
2. Implement an evaluator function
3. Add a `prompt.md` file with the benchmark prompt
4. Update the CLI in `run_benchmark.py` to include your new benchmark

## 📝 Example Usage

```bash
# Run the Maze Gauntlet benchmark on a file
python run_benchmark.py --input sample_llm_output.txt

# Add benchmark results to leaderboard
python run_benchmark.py --input sample_llm_output.txt --add-to-leaderboard

# Get JSON output
python run_benchmark.py --input sample_llm_output.txt --json
```

The output will be a detailed JSON report showing your score breakdown.