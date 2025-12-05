# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.3.0] - 2025-12-05

### Added
- **Enhanced Maze Parsing & Validation**: Fixed regex extraction to handle various LLM output formats including metadata like "TIME: 275s"
- **Comprehensive Error Handling**: Intelligent error messages with context-aware suggestions for parsing failures, size violations, missing elements, and timeouts
- **Performance Optimization**: 5-second timeout protection for complex maze solving with iteration limits to prevent hanging
- **Detailed Scoring Breakdowns**: Enhanced component breakdowns with comprehensive explanations for ambition, complexity, path efficiency, completion, and danger

### Changed
- **Scoring Calculations**: Verified all scoring components match documented behavior with maintained leaderboard integration
- **CLI Output**: Rich output with component analysis, performance ratings, and actionable feedback
- **Character Validation**: Resolved bugs and improved edge case handling for irregular row lengths and malformed maze detection
- **System Safety**: Implemented comprehensive error tracking and debugging information while maintaining existing progress indicators

### Fixed
- **Regex Extraction**: Fixed handling of various LLM output formats and metadata
- **Size Validation**: Enhanced 32x32 constraint validation with clear error messages
- **BFS Algorithms**: Optimized algorithms with iteration limits to prevent hanging
- **Error Handling**: Fixed missing element detection and timeout handling

### Improved
- **User Experience**: Clear error messages with specific improvement suggestions
- **Parsing Reliability**: Handles diverse LLM output formats without failure
- **Scoring Accuracy**: Calculations verified against benchmark specifications
- **System Reliability**: Robust handling of metadata, edge cases, and malformed inputs

### Verified
- **Sample Processing**: Successfully scores complex mazes (e.g., 675.69 points with full breakdown)
- **Error Handling**: Properly rejects violations (e.g., 34x32 maze > 32x32 limit) with helpful suggestions
- **CLI Enhancement**: Rich output with component analysis, performance ratings, and actionable feedback
- **System Compatibility**: Re-scored existing mazes ensuring calculation consistency
- **Real-world Testing**: Parsing tested with real-world LLM output variations

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
