# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.5.1] - 2025-12-05

### Changed
- **Leaderboard Display**: Removed prompt, completion, and total columns from leaderboard table
  - Simplified table to show only Rank, Model, Score, and Time (s) columns
  - Token usage information still stored in JSON but no longer displayed in markdown table

## [0.5.0] - 2025-12-05

### Added
- **Strategic Maze Elements**: Complete overhaul adding 5 new strategic maze mechanics
  - **Teleporters** ('O'/'Q'): Single-use quick travel for strategic routing (+15 pts each, max 60)
  - **Switches** ('s'): Toggle gates ('S') for dynamic path changes (+20 pts each, max 80)
  - **Movable Blocks** ('B'): Push to create bridges/barriers (innovation bonus)
  - **Bonus Exits** ('F','G','H'): Optional objectives (+75 points each)
  - **Conditional Doors** ('X','Y','Z'): Complex unlock requirements (+30 pts each)
- **Enhanced Scoring System**: Expanded from 5 to 8 scoring components
  - **Strategic Innovation**: Rewards creative use of strategic elements (0-100 pts)
  - **Route Complexity**: Multiple solution paths analysis (0-150 pts)
  - **Bonus Objectives**: Optional challenge completion (0-75 pts)
  - **Reduced trap importance**: Max 30 points vs unlimited before
- **Strategic Pathfinder**: Advanced pathfinding algorithm handling stateful elements
  - Multi-dimensional state tracking (keys, switches, teleport usage)
  - Innovation analysis detecting creative strategic element usage
  - Timeout protection for complex maze solving
- **Enhanced Documentation**: Updated prompt.md to guide models toward strategic thinking

### Changed
- **Scoring Focus**: Shifted from trap-spamming to strategic puzzle-solving
  - Typical scores increased from 200-400 to 800+ for quality strategic mazes
  - Quality over quantity approach for all maze elements
- **Maze Evaluation**: Complete rewrite of `strategic_evaluator.py`
  - StrategicMaze class for intelligent element analysis
  - Enhanced pathfinding with stateful movement logic
  - Innovation detection and creative usage scoring
- **CLI Output**: Updated to reflect new scoring components and strategic analysis
  - Strategic elements breakdown in results
  - Innovation details and unique strategies
  - Enhanced maze analysis with complexity metrics

### Fixed
- **Route Complexity Analysis**: Resolved unpacking error in strategic element counting
- **Pathfinding State Management**: Fixed teleporter and switch state tracking
- **Innovation Scoring**: Corrected strategic element usage detection
- **Performance Issues**: Optimized complex maze solving with proper timeout handling

### Improved
- **AI Model Challenge**: Higher intelligence ceiling for advanced models
- **Maze Variety**: Eliminates repetitive trap-filling strategies
- **Strategic Depth**: Multiple solution paths rewarded over single approaches
- **Benchmark Quality**: True spatial reasoning assessment vs basic maze completion

### Tested
- **Performance Validation**: Sample strategic maze scored 871.69 points
  - Strategic Innovation: 70 points (teleporter + switch usage)
  - Route Complexity: 76 points (strategic element integration)
  - Quality Focus: Strategic placement prioritized over trap quantity
- **System Reliability**: Robust handling of complex strategic element interactions
- **Backward Compatibility**: Legacy maze evaluation maintained through grade_maze() wrapper

## [0.4.1]

### Added
- **Default Input File**: `run_benchmark.py` now defaults to `input.txt` when no `--input` parameter is specified
- **Enhanced Error Handling**: Improved user experience with clear error messages when the default input file doesn't exist
- **Backward Compatibility**: Users can still specify alternative input files using `--input` flag

### Changed
- **CLI Interface**: Simplified usage - system automatically uses `input.txt` by default without requiring explicit specification

## [0.4.0]

### Removed
- **OpenRouter Integration**: Removed all OpenRouter API integration and live model benchmarking
- **Live API Calls**: Eliminated `--model` and `--run-all` flags that required API access
- **External Dependencies**: Removed dependency on OpenRouter API for benchmarking

### Changed
- **CLI Interface**: Simplified to use only file-based input with `--input` flag
- **Documentation**: Updated README and examples to reflect file-based workflow
- **Focus**: Repository now exclusively processes pre-generated LLM output files

### Added
- **Manual Ingestion**: Enhanced `--ingest` feature for processing multiple model outputs from single file
- **File Processing**: Streamlined workflow for benchmark evaluation from saved outputs

## [0.3.0]

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

## [0.2.3]

### Added
- **Retry Logic**: Added `--retries` flag to `run_benchmark.py` (default: 1).
- Automatic retry for blank LLM outputs to improve benchmark reliability.

## [0.2.2]

### Added
- **Multi-Key Maze Logic**: Support for alphabet-based keys (`a`-`z`) and doors (`A`-`Z`).
  - New scoring component: **Complexity (Chain Length)** based on sequential key/door pairs solved.
  - New scoring component: **Path Efficiency** (Length / Grid Size).
  - Updated `prompt.md` to instruct LLMs on the new multi-key rules.
- **Rescore Feature**: Added `--rescore` flag to `run_benchmark.py` to re-evaluate all existing outputs in `output/` directory without re-running models.
- `test_multikey.py`: Test suite for validating the new multi-key maze logic and scoring.

### Changed
- **API Integration**: Improved response parsing to robustly handle usage statistics (prompt/completion/total tokens).
- **Maze Evaluator**: 
  - Overhauled scoring formula to prioritize logical chain completion.
  - Adjusted **Danger** score to use diminishing returns (sqrt) for adjacent traps.
  - Fixed `ZeroDivisionError` in complexity ratio calculation.

## [0.2.1]

### Added
- **Progress bars**: `tqdm` integration for visual progress during sequential benchmarking
- **20 new models** added to `models.txt` (Gemini, Llama, Qwen, Mistral, and more)

### Changed
- `run_benchmark.py` now defaults to `--run-all --sequential` when no arguments provided
- Added `tqdm>=4.65.0` to `requirements.txt`

---

## [0.2.0]

### Added
- **Live benchmarking**: Direct API calls for model benchmarking (removed in later version)
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
- `run_benchmark.py` now supports file-based benchmarking with enhanced parsing
- Token usage tracking (prompt, completion, total) in leaderboard results
- Updated `requirements.txt` with `requests` dependency

---

## [0.1.1]

### Added
- **Maze size limit**: Mazes are now limited to 32x32. Mazes exceeding this limit will receive a score of 0 with an error message.
- Updated `benchmarks/maze/prompt.md` with new size constraint for LLM guidance.

### Changed
- `grade_maze()` in `benchmarks/maze/evaluator.py` now validates maze dimensions before scoring.

---

## [0.1.0]

### Added
- Initial maze benchmark implementation
- Maze Gauntlet Evaluator with gradient scoring system
- Support for ASCII maze parsing from LLM output
- Scoring components: Ambition, Progress, Objectives, Proximity, Danger
- CLI runner (`run_benchmark.py`)

### Removed
- Leaderboard feature
