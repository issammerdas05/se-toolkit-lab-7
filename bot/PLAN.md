# LMS Telegram Bot - Implementation Plan

## Overview

This document outlines the development plan for building a Telegram bot that allows users to interact with the Learning Management System (LMS) backend through chat. The bot will support both slash commands and natural language queries using an LLM for intent routing.

## Architecture

The bot follows a layered architecture:

1. **Entry Point** (`bot.py`): Handles Telegram webhook/polling and CLI test mode
2. **Handlers** (`handlers/`): Pure functions that process commands and return responses
3. **Services** (`services/`): API clients for backend and LLM communication
4. **Configuration** (`config.py`): Environment variable loading

This separation ensures testability - handlers work without Telegram connection via `--test` mode.

## Task 1: Plan and Scaffold (Current)

**Goal**: Create project structure and test mode.

- [x] Create `bot/` directory structure
- [x] Implement `bot.py` with `--test` mode
- [x] Create handler layer (separated from Telegram)
- [x] Create `config.py` for environment loading
- [x] Create `pyproject.toml` with dependencies
- [ ] Create `.env.bot.example` file
- [ ] Test all placeholder commands

**Acceptance**: `uv run bot.py --test "/start"` returns welcome message.

## Task 2: Backend Integration

**Goal**: Connect handlers to real LMS backend API.

- [ ] Create `services/api_client.py` for HTTP requests
- [ ] Implement Bearer token authentication
- [ ] Update `/health` handler to call backend `/docs` endpoint
- [ ] Update `/labs` handler to call backend `/items/` endpoint
- [ ] Update `/scores` handler to call backend analytics endpoints
- [ ] Add error handling for backend failures
- [ ] Test with real backend data

**Acceptance**: Commands return real data from backend, not placeholders.

## Task 3: Intent-Based Natural Language Routing

**Goal**: Enable plain text queries using LLM tool calling.

- [ ] Create `services/llm_client.py` for LLM API calls
- [ ] Define tools for each backend endpoint
- [ ] Implement system prompt with tool descriptions
- [ ] Create intent router that calls LLM for non-command input
- [ ] Handle multi-step reasoning (LLM chaining multiple API calls)
- [ ] Add inline keyboard buttons for common actions

**Acceptance**: User can ask "what labs are available?" and get correct response.

## Task 4: Containerize and Document

**Goal**: Deploy bot alongside backend on VM.

- [ ] Create `bot/Dockerfile`
- [ ] Add bot service to `docker-compose.yml`
- [ ] Configure bot to use Docker networking (service names, not localhost)
- [ ] Update README with deployment instructions
- [ ] Test end-to-end deployment

**Acceptance**: Bot runs in Docker, responds to Telegram messages.

## Testing Strategy

1. **Unit Tests**: Test individual handlers with mock data
2. **Integration Tests**: Test backend API calls with test mode
3. **Manual Tests**: Verify in Telegram after each task

## Deployment Checklist

- [ ] `.env.bot.secret` on VM with `BOT_TOKEN`, `LMS_API_KEY`, `LLM_API_KEY`
- [ ] Backend running and accessible
- [ ] Qwen proxy running on port 42005
- [ ] Bot container built and started
- [ ] Bot responds in Telegram

## Notes

- Use `uv` for dependency management (not pip)
- Never commit secrets (`.env.bot.secret` is gitignored)
- Follow Git workflow: issue → branch → PR → review → merge
# Task 3: Intent Routing with LLM
