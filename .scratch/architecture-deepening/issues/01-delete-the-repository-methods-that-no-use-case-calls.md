# 01: Delete the repository methods that no use case calls

**What to build:** A developer who adds a repository adapter implements only the methods that a use case calls. `SessionRepository.update`, `SessionRepository.get_by_id`, and `UserRepository.remove` leave the ports, the Sql adapters, the fakes, and their tests. `UserRepository.update`, `UserRepository.get_by_id`, and `SessionRepository.remove` stay, because use cases call them. In `CODING_STANDARDS.md`, the sentence "Its methods use Evans's names: ..." goes away with no replacement, and the introduction of the method rules that follow it reads on its own. Read the spec (`.scratch/architecture-deepening/spec.md`, section "1. Delete the repository methods that no use case calls"), `CODING_STANDARDS.md`, and the ADRs before you start.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] No port, Sql adapter, or fake declares `SessionRepository.update`, `SessionRepository.get_by_id`, or `UserRepository.remove`.
- [x] A repository test that read a Session through `get_by_id` reads it through `get_by_hashed_token`, and every other repository test still passes.
- [x] `CODING_STANDARDS.md` holds no list of Evans's method names, and its rules for `next_id`, `add`, `update`, `remove`, and `get_by_*` stay.
- [x] The checks in `README.md` pass.
