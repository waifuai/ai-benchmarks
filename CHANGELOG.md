# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.3] - 2025-12-05

### Added
- **Retry Logic**: Added `--retries` flag to `run_benchmark.py` (default: 1).
- Automatic retry for blank LLM outputs to improve benchmark reliability.

## [0.2.2] - 2025-12-05

### Added
- **Multi-Key Maze Logic**: Support for alphabet-based keys (`a`-`z`) and doors (`A`-`Z`).
  - New scoring component: **Complexity (Chain Length)** based on sequential key/door pairs solved.
  - New scoring component: **Path Efficiency** (Length / Grid Size).
  - Updated `prompt.md` to instruct LLMs on the new multi-key rules.
- **Rescore Feature**: Added `--rescore` flag to `run_benchmark.py` to re-evaluate all existing outputs in `output/` directory without re-running models.
- `test_multikey.py`: Test suite for validating the new multi-key maze logic and scoring.

### Changed
- **OpenRouter Integration**: Improved response parsing to robustly handle usage statistics (prompt/completion/total tokens).
- **Maze Evaluator**: 
  - Overhauled scoring formula to prioritize logical chain completion.
  - Adjusted **Danger** score to use diminishing returns (sqrt) for adjacent traps.
  - Fixed `ZeroDivisionError` in complexity ratio calculation.

## [0.2.1] - 2025-12-05

### Added
- **Progress bars**: `tqdm` integration for visual progress during sequential benchmarking
- **20 new models** added to `models.txt` (Gemini, Llama, Qwen, Mistral, and more)

### Changed
- `run_benchmark.py` now defaults to `--run-all --sequential` when no arguments provided
- Added `tqdm>=4.65.0` to `requirements.txt`

---

## [0.2.0] - 2025-12-05

### Added
- **OpenRouter integration** (`openrouter.py`): Direct API calls to OpenRouter for live model benchmarking
- **Leaderboard system** (`leaderboard.py`): Track and compare model scores across benchmarks
  - JSON-based persistent storage (`leaderboard.json`)
  - Markdown table generation (`LEADERBOARD.md`)
- **Batch benchmarking**: `--run-all` flag to test all models from `models.txt`
  - Parallel execution by default for faster testing
  - `--sequential` flag for one-at-a-time testing
- **Timing metrics**: Track and display elapsed time (seconds) for each model response
- New CLI options: `--model`, `--leaderboard`, `--add-to-leaderboard`, `--run-all`, `--sequential`
- `.gitignore` for excluding generated files
- `models.txt` for configuring which models to benchmark

### Changed
- `run_benchmark.py` now supports live API benchmarking in addition to file input
- Token usage tracking (prompt, completion, total) in leaderboard results
- Updated `requirements.txt` with `requests` dependency

---

## [0.1.1] - 2025-12-05

### Added
- **Maze size limit**: Mazes are now limited to 32x32. Mazes exceeding this limit will receive a score of 0 with an error message.
- Updated `benchmarks/maze/prompt.md` with new size constraint for LLM guidance.

### Changed
- `grade_maze()` in `benchmarks/maze/evaluator.py` now validates maze dimensions before scoring.

---

## [0.1.0] - 2025-12-02

### Added
- Initial maze benchmark implementation (`c3002ed`)
- Maze Gauntlet Evaluator with gradient scoring system
- Support for ASCII maze parsing from LLM output
- Scoring components: Ambition, Progress, Objectives, Proximity, Danger
- CLI runner (`run_benchmark.py`)

### Removed
- Leaderboard feature (`555d259`)
