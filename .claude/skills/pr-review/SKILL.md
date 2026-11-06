---
name: pr-review
description: Review the PR in rounds, fix real findings, and record every decision in a ledger.
---

Read `docs/agents/issue-tracker.md` and find the path of the PR review ledger. If the doc has no path, stop and ask the user.

Repeat these steps as one round:

1. Call the Skill tool for "code-review" on the PR diff and its spec.
2. Read the ledger. Drop each finding that already has a `decline` or `defer` entry, unless its code changed since.
3. Give each remaining finding one verdict:
   - `fix`: a real defect, or it breaks the spec.
   - `decline`: the reason is the spec section, the line that disproves the finding, or the risk the fix adds.
   - `defer`: real, but outside this PR. The reason is the ticket.
4. Fix the `fix` findings. Run only the test files that cover the change.
5. Append one ledger entry per finding: file and line, finding, verdict, reason, round number.

Start a new round only after a round with a `fix`. If a `fix` changes a line that an earlier round fixed, stop and ask the user.

After a round with no `fix`:

1. Run the checks of the Checks section in `CLAUDE.md`. If one fails, fix it and start a new round.
2. If the evidence in the PR body names an older commit, update it from this run.
3. Report the number of rounds, the count of each verdict, the open findings, and the ledger path.

Fix only what a finding points to. Add nothing the spec does not ask for.
