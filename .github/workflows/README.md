# Workflows

One workflow builds the profile and approach cards; the rest keep the repo
healthy. The generators live in [`../../profile/profile.py`](../../profile/profile.py) and
[`../../approach/approach.py`](../../approach/approach.py),
and the build workflow is a thin wrapper that hands them the credentials.

## The build

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| [build](build.yml) | four times a day (00:17, 06:17, 12:17, 18:17 UTC), push to main (excluding generated files), manual `workflow_dispatch` | Runs `profile/profile.py` to regenerate the profile cards (`profile/profile.svg`, `profile/profile-dark.svg`, `profile/profile-light.svg`) from live GitHub stats and record them in `profile/last-good.json`, then `approach/approach.py` to split the hand-edited `approach/approach.svg` into `approach/approach-dark.svg` and `approach/approach-light.svg`, then commits only if something changed. A stat the API will not give after three retries is carried over from `last-good.json`; a stat with no stored value fails the generate step, so nothing is committed. Pushes over SSH with a write deploy key that bypasses the branch ruleset |

## Repo automation

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| [ci](ci.yml) | PR | Compile-checks and imports both generators and runs `tests/test_profile.py` against a stubbed API so a broken change cannot land |
| [gitleaks-scan](gitleaks-scan.yml) | push, PR | Scans for hard-coded secrets with a pinned gitleaks binary |
| [markdownlint](markdownlint.yml) | push, PR | Lints every markdown file against [`.markdownlint.json`](../../.markdownlint.json) |

Dependency update PRs and stale branch cleanup are handled centrally by repo-ops, so
this repo carries no `dependabot.yml` or branch maintenance workflow.

## Conventions

- One workflow per job, named for what it does; the build workflow is a thin wrapper
  and the logic lives in the script.
- All runtime settings come from GitHub Actions secrets injected as environment
  variables; nothing configurable is committed.
- Third-party actions are pinned to a full commit SHA so a mutable tag cannot be
  silently updated.
