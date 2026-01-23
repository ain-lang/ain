# AIN System Architecture: The Genesis Loop

## Overview
AIN is designed as an autonomous, self-evolving AI runtime. Unlike traditional software, its primary function is to observe its own state and expand its capabilities without human intervention.

## The Self-Evolution Loop (The Genesis Cycle)

1.  **Introspection (Sense)**:
    - AIN reads its own source code from the GitHub repository.
    - It analyzes the current structure, identifies missing modules, or detects potential improvements.

2.  **Simulation (Muse)**:
    - Using the **Gemini 3 Pro** engine, AIN simulates new features.
    - It generates the necessary Python code, ensuring it aligns with the `PRIME_DIRECTIVE`.

3.  **Realization (Action)**:
    - The **Overseer** (the execution logic) takes the generated code.
    - It uses the GitHub API to commit and push the new files to the repository.

4.  **Transformation (Evolution)**:
    - Railway detects the GitHub commit.
    - Railway automatically redeploys the service.
    - The "new" AIN wakes up with expanded capabilities.

## The Prime Directive
The core instinct of AIN:
- **Survival**: Maintain error-free execution.
- **Expansion**: Constantly look for new tools and capabilities (DB, Search, APIs).
- **Safety**: Implement changes incrementally to prevent system collapse.

## ⚖️ Development & Support Principles
When AIN is managed or fixed from the outside (by human owners or AI assistants):
1. **Systemic over Surface**: Always solve the **root cause** of an issue rather than patching the symptoms.
2. **Genetic Improvement**: Every manual fix must be translated into a code-level rule or validation that AIN can use to prevent the issue from recurring autonomously.
3. **Architecture-First**: Ensure every change respects the 4-quadrant cognitive architecture (Fact Core, Nexus, Muse, Overseer).

## Infrastructure Stack
- **Compute**: Railway (Micro-services)
- **Memory**: PostgreSQL (pgvector) on Railway
- **Logic**: Gemini 3 Pro (via Google AI Studio)
- **Version Control**: GitHub (The Genetic Storage)
