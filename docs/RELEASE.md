# Release Guide

This document describes the release workflow for AgriAutoLab.

## Prerequisites

Before tagging a release, ensure:

1. All linting and tests pass on Python 3.10 and 3.12:
   ```bash
   ruff check .
   pytest
   ```
2. Dependency sanity check passes:
   ```bash
   pip check
   python3 -m compileall src tests scripts
   ```
3. Version in `pyproject.toml` matches the planned release tag.
4. `CHANGELOG.md` reflects all changes for the release version.

## Versioning Policy

AgriAutoLab follows [Semantic Versioning (SemVer 2.0.0)](https://semver.org/):
- **MAJOR** version for incompatible API or protocol changes.
- **MINOR** version for backward-compatible functional additions.
- **PATCH** version for backward-compatible bug fixes.

Development branches use PEP 440 dev versions (e.g., `0.6.0.dev0`).
