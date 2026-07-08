# AGENTS.md — Example Service

## Overview

This service has a small instruction file for agents and contributors. Keep
the guidance focused on repository-specific details.

## Environment

- Use Python 3.11 or newer.
- Create a virtual environment with `python -m venv .venv`.
- Install the project with `pip install -e .[dev]`.

## Development Workflow

- Run `pytest` before opening a pull request.
- Keep changes small and easy to review.
- Prefer typed functions and clear names.
- Add tests for new behavior and bug fixes.

## Agent Notes

- Read nearby files before editing.
- Prefer nested AGENTS.md files when a subdirectory needs special guidance.
- Move long background material into reference documentation.
