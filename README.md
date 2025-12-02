# AI Benchmark Repository

A specialized testing suite for evaluating Large Language Models (LLMs) on spatial reasoning tasks through gradient scoring systems.

## 🧪 Current Benchmarks

### The "Maze Gauntlet" - LLM Spatial Reasoning Challenge

Unlike traditional maze benchmarks that use binary pass/fail scoring, the Maze Gauntlet implements a **Gradient Scoring** system that evaluates how well LLMs can generate complex, solvable mazes with specific state-dependency rules.

#### Philosophy
Most maze benchmarks are binary (Pass/Fail). This is a **Gradient Benchmark** that rewards:
- **Ambition**: Grid size and complexity
- **Logic**: Proper S → K → D → E path progression  
- **Danger**: Strategic trap placement adjacent to valid paths

## 🏆 Leaderboard

| Rank | Model | Score | Date | Notes |
|------|-------|-------|------|-------|
| 1 | - | - | - | Waiting for submissions |
| 2 | - | - | - | |
| 3 | - | - | - | |

*Submit your results by running the benchmark and sharing your score!*

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run benchmark on LLM output
python run_benchmark.py --input path_to_llm_output.txt
```

## 📊 Scoring System

### The Maze Gauntlet Scoring Components:

1. **Ambition** (Grid Size)
   - Points: Rows × Columns
   - Rewards larger, more ambitious mazes

2. **Progress** (Path Logic)
   - 2 points per reachable tile
   - +50 bonus for Key ('K') 
   - +50 bonus for Door ('D')
   - +50 bonus for End ('E')

3. **Danger** (Strategic Placement)
   - +20 points per trap adjacent to valid path
   - Only traps near the solution path count
   - Traps in sealed rooms = 0 points

4. **Logic Penalties**
   - If Traps > Walls: -50% score penalty
   - Path must follow S → K → D → E sequence

5. **Proximity Bonuses**
   - Partial credit for unreachable objectives based on distance to reachable areas

## 🔧 Architecture

```
ai-benchmark/
├── README.md               # This file
├── requirements.txt        # Dependencies
├── run_benchmark.py        # CLI Entry point
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
3. Update the CLI in `run_benchmark.py` to include your new benchmark

## 📝 Example Usage

```bash
# Run the Maze Gauntlet benchmark
python run_benchmark.py --input sample_llm_output.txt
```

The output will be a detailed JSON report showing your score breakdown.