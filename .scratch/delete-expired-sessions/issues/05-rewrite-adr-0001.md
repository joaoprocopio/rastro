# 05: Rewrite ADR 0001 for the current stack

**What to build:** a reader of ADR 0001 learns the stack that rastro runs today. ADR 0001 is rewritten in place: its title names FastAPI, SQLAlchemy 2, and Procrastinate, its considered option about the task queue and its section "Use ZeroMQ as the first taskiq broker" go, and one line points to ADR 0004 for the choice of the task queue. ADR 0004 keeps the reason and the prototype evidence, so ADR 0001 repeats neither. The file name changes with the title, and every link to ADR 0001 follows it. The spec is `.scratch/delete-expired-sessions/spec.md`.

**Blocked by:** 02

**Status:** resolved

- [x] ADR 0001 does not mention taskiq or ZeroMQ.
- [x] ADR 0001 points to ADR 0004 for the task queue.
- [x] Every link to ADR 0001 in the repository resolves to the renamed file.
