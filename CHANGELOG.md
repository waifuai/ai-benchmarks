# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
