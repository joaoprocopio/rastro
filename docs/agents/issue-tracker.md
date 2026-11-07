# Issue tracker: GitHub Issues

Specs and tickets are issues of this repo, and `gh` runs every operation. The repo is public, so every issue and comment is public.

- **Spec**: an issue.
- **Ticket**: a sub-issue of its spec (`gh issue create --parent <spec>`), or an issue without a parent when the work has no spec.
- **Label**: one triage label, plus `type:feature` or `type:spike` on a ticket.
- **Blocking**: GitHub's issue dependencies (`gh issue create --blocked-by <n>`), so a ticket is ready when every blocker is closed.
- **Comment**: `gh issue comment <n>`.
- **Acceptance criterion**: the agent that verifies a criterion ticks its checkbox in the issue body, so an empty checkbox marks a criterion that nobody verified.
- **Close**: work ends when its PR to `main` is open, as `docs/agents/github.md` describes. The PR body has one `Closes #<n>` per issue, and GitHub closes those issues when the PR merges into `main`.
- **Integration branch**: a merge into another branch closes nothing, so the PR of the integration branch lists the spec and every ticket.
- **Review**: the maintainer reviews on the PR.
- **External PR**: it is a plain PR, and triage covers issues only.

## Wayfinding operations

- **Map**: an issue with the `wayfinder:map` label.
- **Child ticket**: a sub-issue of the map, with a `wayfinder:<type>` label.
- **Blocking**: GitHub's issue dependencies, as above.
- **Frontier**: the open sub-issues of the map, without an open blocker or an assignee, in map order.
- **Claim**: `gh issue edit <n> --add-assignee @me`.
- **Resolve**: comment the answer, run `gh issue close <n>`, and add its link and gist to the Decisions-so-far of the map.
