# Security Policy

> Public version of this policy: https://isaacadjei.me/security-policy

This repository is public. It holds my GitHub profile README, the generator that
builds it and the SVGs it produces. The generator reads GitHub statistics with
read only tokens, so it can never change anything.

## Reporting a vulnerability

Please report anything security relevant privately, not in a public issue.

- Email security@isaacadjei.me with the details and steps to reproduce.
- Expect an acknowledgement within a few days.

## What lives here and what does not

- No secret value is ever committed to this repository. Every credential exists
  solely as a GitHub Actions secret.
- `ACCESS_TOKEN` is a fine grained token scoped to read only, covering the account
  and repository statistics the generator needs. It cannot write to any repository.
- `CONTRIB_TOKEN` is a classic personal access token scoped to `read:user` alone,
  with no `repo` access at all. GitHub's `contributionsCollection` API withholds
  private repository detail (commits, PR reviews, the contribution calendar) from
  every caller, even the account owner, unless the token carries that classic
  scope; no fine grained permission grants it. This is the one deliberate
  exception to fine grained only tokens, held as narrowly as the gap allows: it
  cannot read or write any repository content, only my own profile level
  contribution counts.
- The workflow's write access to this repo comes from the built in `GITHUB_TOKEN`,
  scoped to this repository alone and is only used to commit the regenerated SVGs.

## If a credential is exposed

Rotate first, investigate second. Every token here is narrowly scoped and can be
revoked and reissued without downtime, because the build simply re-runs against
the new token.

1. Revoke the exposed token. `ACCESS_TOKEN` is a fine grained token, revoked from
   GitHub's fine grained token settings; `CONTRIB_TOKEN` is a classic token,
   revoked from GitHub's classic token settings.
2. Generate a replacement with the same minimal scope: read only covering account
   and repository statistics for `ACCESS_TOKEN`, `read:user` alone for
   `CONTRIB_TOKEN`.
3. Update the matching Actions secret (`ACCESS_TOKEN` or `CONTRIB_TOKEN`).
4. Run the build by hand from the Actions tab to confirm it still works.
