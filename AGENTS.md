# AGENTS.md

Working rules for AI-assisted development in this repository.

## Core principle

AI writes fast. The human owner understands, verifies, tests, and accepts.

```text
AI writes -> human understands and verifies -> strength
AI writes -> human blindly accepts        -> weakness
```

## Roles

```text
ChatGPT  -> architecture, levels, roadmap, learning map, acceptance criteria
Claude   -> terminal pair engineer, local commands, logs, explanation, debugging
Codex    -> GitHub/repository implementation, diffs, file changes, PR-style work
Human    -> owner, reviewer, integrator, final decision
Jetson   -> real edge target for camera/GPU/inference validation
```

## Engineering rules

1. Keep architecture, framework, runtime, OS, hardware, and physical system levels separate.
2. Do not mix levels without explicitly naming the level.
3. Prefer small readable changes over large hidden rewrites.
4. Explain why a change is needed before changing code.
5. Add tests or runnable checks when possible.
6. Keep README files updated when behavior or structure changes.
7. Never hide errors. Show the error, explain the likely cause, and propose a fix.
8. Keep secrets, tokens, passwords, IPs, and private paths out of public commits.
9. Prefer practical runnable examples over abstract notes.
10. Final acceptance belongs to the human owner.

## Required output for meaningful tasks

For each implemented task, provide:

- what changed
- why it changed
- how to run it
- how to verify it
- known limitations
- next step
