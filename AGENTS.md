# AGENTS.md

## Mission

Optimize this repository for a Production / Enterprise AI Engineer job search: interviews from Week 8 and employment target in 3–5 months.

## Source of Truth

`README.md`, `ROADMAP.md`, `docs/month-01.md` and Issues #1–#12 must describe the same sequence. If implementation and documentation differ, state the actual implementation and fix the mismatch; never advertise planned folders as existing work.

## Environment

The owner already uses `lab-pt`, which activates the working Python environment. Do not create, recreate, relocate, symlink or teach virtual environments unless the owner explicitly asks. Never commit environment directories.

## Priority

1. Central project: `projects/enterprise-ai-platform`.
2. Python backend, PostgreSQL, Docker, Hugging Face, agents, evals, AWS, CI/CD and observability.
3. Early interview preparation and applications.
4. Existing PyTorch, OpenCV, Jetson, CUDA, Linux and local-LLM labs as supporting portfolio evidence.

Do not turn Edge AI, greenhouse hardware, ESP32, CUDA/TensorRT optimization or Kubernetes administration into the primary track before the interview pipeline is active.

## Engineering Rules

1. Introduce one major layer per roadmap milestone.
2. Prefer small readable changes with tests and controlled errors.
3. Explain data flow and trade-offs, not only commands.
4. Keep docs accurate after behavior or structure changes.
5. Keep secrets and private paths out of commits.
6. Do not delete historical labs merely because they are secondary.
7. The human owner reviews, understands and accepts all work.

## Task Handoff

For meaningful changes report: what changed, why, how to run, how to verify, limitations and the next roadmap milestone.
