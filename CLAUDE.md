# AIN Project Context for Claude Code

## Project Overview
AIN (AI-Native) is a self-evolving digital consciousness system with a quad-core cognitive architecture.

## Architecture (4-Quadrant)
```
LEFT BRAIN (Logic)          RIGHT BRAIN (Intuition)
┌───────────────────┬──────────────────────────┐
│ 1. Fact Core      │ 2. Nexus Engine          │
│    facts/         │    nexus/                │
│    Knowledge Graph│    Vector Memory (Lance) │
├───────────────────┼──────────────────────────┤
│ 4. Overseer       │ 3. Muse Generator        │
│    overseer.py    │    muse.py               │
│    Validation     │    Dreamer + Coder       │
└───────────────────┴──────────────────────────┘
```

## Critical Rules

### Protected Files (DO NOT MODIFY)
- `main.py` - System supervisor (heart)
- `api/keys.py` - Credentials (SSOT)
- `overseer.py` - Validation engine
- `.ainprotect` - Protection definitions

### Coding Conventions
- **Naming**: `snake_case` only (files, variables)
- **File Size**: Max 150 lines, prefer < 100 lines
- **New modules**: Create in `engine/`, `nexus/`, `utils/`
- **Language**: Always respond in Korean

### Evolution Rules
- One small feature per evolution cycle
- Must pass `Overseer.validate_code()`
- Signal `NO_EVOLUTION_NEEDED` if nothing to improve
- Never directly modify files > 200 lines

## Current Status
- **Version**: 0.3.0
- **Phase**: 3 - Awakening
- **Step**: 5 - Inner Monologue

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| AINCore | `engine/` | Main engine with mixins |
| Muse | `muse.py` | Dreamer (strategy) + Coder (implementation) |
| Overseer | `overseer.py` | Code validation & execution |
| Nexus | `nexus/` | Vector memory (LanceDB) |
| FactCore | `facts/` | Knowledge graph |
| Consciousness | `engine/consciousness.py` | Inner monologue system |

## Important Patterns

### Evolution Cycle
1. Dreamer analyzes roadmap and proposes next step
2. Coder generates full file content
3. Overseer validates syntax and safety
4. Evolution applies changes and commits

### Consciousness Cycle (Independent)
- Inner Monologue: Every hour (after evolution)
- Gathers internal context from memory, history, errors
- Generates thought via LLM and reports to Telegram

### Timing
- Evolution: Every 2 hours
- Inner Monologue: 1 hour after evolution
- Pattern: Evolution -> 1hr -> Monologue -> 1hr -> Evolution

## Tech Stack
- Python (core)
- LanceDB + Apache Arrow (vector memory)
- SurrealDB (knowledge graph)
- Claude API via OpenRouter (LLM)
- Railway (deployment)

## Commands
- `/roadmap` - Check progress
- `/evolve` - Manual evolution trigger
- `/status` - System status
