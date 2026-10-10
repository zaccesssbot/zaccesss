# Changelog

All notable changes to this project are recorded here. The format follows Keep a
Changelog and this project uses date based entries rather than semantic versions,
because it is a living profile rather than a released library.

## Unreleased

## 2026-10-11

### Fixed

- Lines of code leave out two generated repos: isaacadjei.me (the public copy of my portfolio's source) and meta-mirror (automated backups). Each portfolio release copied the whole site into isaacadjei.me, so the same lines were counted twice.
- The card images carry a new cache number (16) so GitHub shows the corrected figures straight away instead of a stale copy.

## 2026-10-09

### Fixed

- The card build no longer reverts other changes on main when it retries a rejected push. It sets its generated SVGs aside, resets to the new tip and puts only those back.

### Changed

- The Contact block runs Discord, LinkedIn, Portfolio, Email.Main then Email.Work, so the keys step up in length and the two emails sit together. LinkedIn shows as in/isaacadjei.
- Hobbies.Hardware reads PCBs, plural like MCUs beside it.
- The links above the card follow the site header: Portfolio, About, Experience, Projects, Blog, TIL, Notes, Newsletter, Contact, Links and More, with Bot last.
- The card image links move to ?v=15, so cached copies refresh with the new rows.
- Region shows LHR <-> BHX, the CDN edge codes for London and Birmingham, in place of eu-west-2. Plain ASCII keeps the right edge aligned in the card font.
- The card now reads Host then Mode then Region. Mode shortens to EECS. Region shows eu-west-2 in place of the full location, which the profile sidebar already gives.

### Added

- CODEOWNERS and SUPPORT.md.
- Markdown lint CI workflow with its own `.markdownlint.json`, added to the workflows README.
- YAML issue forms for bug reports and feature requests plus a pull request template.
- `.github/ISSUE_TEMPLATE/config.yml` disabling blank issues.

### Changed

- Tidied code comments and the repository docs.
- The build workflow now commits generated SVGs as the real zaccesssbot account instead of a placeholder identity with no GitHub account behind it. Its signing key now matches what is actually registered there, so these commits show as Verified.
- The repo count stat now includes repos I belong to as an org member, not just ones I personally own, matching the affiliation list the lines-of-code stat already used.
- Rewrote CODE_OF_CONDUCT.md from a closed-to-external-input notice to the standard interaction guidelines used across my other repositories.
- Moved the profile and approach generators and their SVGs into their own `profile/` and `approach/`
  folders, so each card's script and output sit together instead of all eight files loose at the repo
  root. Updated the README image paths, the build and CI workflows and the docs that reference them
  to match; bumped the profile SVGs' cache-busting query string to `v=14` since their served path changed.
- Upgraded the profile SVG generation to output three variants: `profile.svg` (adaptive, default dark),
  `profile-dark.svg` and `profile-light.svg`. The README uses an HTML `<picture>` tag with `prefers-color-scheme`
  media queries to serve `profile-dark.svg` and `profile-light.svg` directly (resolving SVG @media sandboxing
  on forges and devices that strip it), while keeping `profile.svg` as the standalone adaptive fallback image.
- Added `approach.py`, which derives `approach-dark.svg` and `approach-light.svg` from the
  hand-edited `approach.svg`, the same fixed-palette-per-theme treatment as the profile card, for when the
  `approach` card in the README is un-muted. approach.svg itself stays hand-authored since it's an illustrative
  diagram, not live data.
- Replaced the Git Stats `Account` creation-year row with `Uptime` (account age as `Xy Yd`, computed live from
  the account's creation timestamp rather than frozen at a static year), paired with `Streak` on the right,
  formatting the longest streak in key-coloured curly braces (`Uptime: 3y 145d | Streak: Xd {Best: Yd}`) to
  match the `Repos` and `Lines of Code` headline-left, detail-right pattern. Abbreviated the "days" unit on
  `Streak`/`Best` to a single `d` after finding the full word could overflow the 66-char row budget once both
  values reached a full year (366/366) - verified every Git Stats row against generous worst-case values and
  this was the only one that broke the budget; the abbreviated form fits exactly at 66 chars even at 366d/366d.
- Reordered the Git Stats rows so the three curly-brace detail rows (`Repos {Contrib}`, `Streak {Best}`,
  `Lines of Code {++/--}`) sit together at the bottom of the block instead of being split up by `Commits`/`PRs`
  and `Issues`/`Reviews`.
- Aligned both the opening `{` and closing `}` of the `Repos {Contrib}` and `Streak {Best}` rows to the same
  columns, by padding whichever row's inner brace text is shorter with a leader-dot (`{Best: .42d}`) up to a
  shared target length, matching the `. Label: .... value` dot-leader style used everywhere else on the card
  instead of leaving an invisible gap. Went through two unsafe designs before this one and caught both by
  testing worst-case values rather than just the current live numbers: pinning a fixed column let the row with
  the longer detail text overflow past 66 chars; the first version of the inner-padding fix could still
  overflow because padding one row out to match the other's length didn't check whether that row had any
  budget left before its own dot-leader hit its 1-dot floor. Swept 480 `(repos, contributed, current streak,
  longest streak)` combinations after the fix - zero overflow, braces aligned in every case.
- Proved by exhaustive sweep that the dot-leader fix above was already the best a 66-char row could do -
  `Repos {Contrib}` and `Streak {Best}` have fixed label-length differences (`Repos` vs `Streak`, `Contrib`
  vs `Best`) that a dot-leader cannot always cancel out within a fixed budget without either overflowing
  or shrinking a real digit.
- Found that `get_streak()` was silently capped at one year of history: GitHub's `contributionsCollection`
  defaults to the trailing 365 days when no `from`/`to` range is given, so any real streak longer than a
  year would have been truncated to whatever the trailing year covered, with nothing to say it had been
  cut short. Added `get_contribution_days_for_year()` and walked every calendar year from account creation
  to today, the same pattern `get_all_contributions()` already used, then ran the streak count over the
  full stitched-together history instead of a single window. A streak can now genuinely run past a year.
- Widened `LINE_WIDTH` from 66 to 70 chars and `SVG_WIDTH` from 1080 to 1120 to match, the smallest
  increase that guarantees the `Repos`/`Streak` braces always land on the same column, checked against
  every digit-length combination up to 999 repos/contributed and 9999 streak days now that a streak isn't
  bounded to one year. The extra characters come out of the right margin evenly instead of crowding the
  card edge.
- Made `fmt_uptime()` calendar-exact instead of dividing `delta_days` by a flat 365: that divisor doesn't
  know about leap years, so the day count drifted by roughly a day for every leap year the account had
  lived through. Switched to `dateutil.relativedelta`, which walks real calendar years, so the split is
  exact regardless of how many leap years fall inside the span.
- Fixed the `isaac@adjei` header divider landing one hyphen short of every other row's width, unlike the
  `- Contact` and `- Git Stats` section dividers, which already filled to `LINE_WIDTH` exactly.
- Reduced the ASCII portrait from 14px to 13px so the 44-char-wide art leaves a visible gap before the
  stats column instead of almost touching it.
- Bumped the README's SVG cache-busting query param from `?v=12` to `?v=13` across all three `<picture>`
  references, so the changes above are visible immediately rather than waiting out GitHub's cache.
- Bumped the README's SVG cache-busting query param from `?v=11` to `?v=12` across all three `<picture>`
  references, so the dot-leader change above is visible immediately rather than waiting out GitHub's cache.
- Bumped the README's SVG cache-busting query param from `?v=10` to `?v=11` across all three `<picture>`
  references, so the brace-alignment change above is visible immediately rather than waiting out GitHub's cache.
- Bumped the README's SVG cache-busting query param from `?v=9` to `?v=10` across all three `<picture>`
  references, so GitHub serves the freshly regenerated cards instead of a cached copy of the old layout.
- Updated `.github/workflows/build.yml` and `.github/workflows/ci.yml` to generate, ignore and stage all
  generated SVG variants (`profile*.svg`, `approach-dark.svg`, `approach-light.svg`) and to compile-check
  `approach.py` alongside `profile.py`.
- Bumped the build schedule back to four runs a day (00:17, 06:17, 12:17 and 18:17 UTC) from three, and
  brought `.github/WORKFLOW.md` and `.github/workflows/README.md` back in sync with the schedule and with
  `approach.py`'s existence (both had drifted out of date).
- Fixed a stale reference in `.gitattributes` to the generator's old filename (`isaacadjei.py`), clarified
  that `approach.svg` is the one hand-authored exception among the generated SVGs and generalised "GitHub's
  language bar" to "each forge's language bar" since the file applies to every mirror, not just GitHub.
- Generalised "iOS Safari and GitHub Mobile" to forge/device-neutral wording in `README.md`, `profile.py`
  and `approach.py`, since the underlying reason (some hosts strip `@media` queries from inline SVG) isn't
  specific to those two.
- Renamed the profile generator from `isaacadjei.py` to `profile.py` and the ASCII
  portrait asset from `ascii_final.txt` to `ascii_profile.txt`.
- Added a `More` link to the README's top link row, pointing at
  `https://isaacadjei.me/all-pages` and dropped the direct `Now` link because
  that page is already discoverable from `More`.
- Expanded the Git Stats section to six rows: followers/stars, lifetime contributions/
  repos, commits/PRs, issues/PR reviews, streaks and lines of code. Contributed repos
  now includes my own repos, commits count commit contributions only and lifetime
  Contribs sums the contribution calendar total across every year since account
  creation. The Repos row keeps the Contributed count in key-coloured curly braces on
  the right, mirroring the Lines of Code row's headline-left, detail-right shape. Forks
  and gists are still fetched every run but that row is commented out for now since both
  are 0; I'll bring it back once there is real data. The portrait is shifted down to
  stay centred beside the taller stats block.
- The profile card is now a single theme-adaptive `profile.svg` instead of a `dark_mode.svg`
  and `light_mode.svg` pair swapped by a `<picture>` element. The theme switch lives inside the
  SVG as a `prefers-color-scheme` media query on colour classes, so the browser renders the right
  theme on every forge (GitHub, GitLab, Codeberg and gitea.com), not just GitHub. GitHub strips
  `<picture>` on the other forges and falls back to a single fixed image, which is why the mirrors
  always showed the dark card before. The `approach` diagram gets the same treatment as a single
  adaptive `approach.svg`, so it is ready to render everywhere when I un-mute it. The generator
  (`profile.py`) now emits the one adaptive file and the README references it directly. The
  build workflow now regenerates, ignores on push and commits `profile.svg` rather than the old
  paired filenames, which were left stale in the first pass and broke the daily auto-update.
- The build pushes the SVGs over SSH with a write deploy key rather than the built in
  token. The push trigger ignores the generated SVGs so the deploy-key push cannot
  re-trigger the build and loop.
- CI and gitleaks now run on pull requests only. They no longer re-run on `main` after a
  merge, since the same commit was already checked on the PR.
- Moved the build schedule off the top of the hour, to the `:17` minute past each
  scheduled run. The explicit times spell out each daily run and the off-peak minute
  dodges GitHub's congested on-the-hour scheduling. (Since trimmed from four runs a day
  to three, see above.)
- Relicensed the repository. The visual and written content (the SVGs, the README,
  the ASCII portrait and everything under `assets/`) is now Creative Commons
  Attribution-NonCommercial-NoDerivatives 4.0 and the generator source
  (`profile.py`) is PolyForm Noncommercial 1.0.0, so the profile can be shared
  with credit but not reused commercially or remixed. This replaces the previous
  MIT licence.

### Added

- A TIL link in the README nav, between Blog and Newsletter, pointing at
  `https://isaacadjei.me/til`.
- Enforced CI on `main` with a branch ruleset, so a pull request cannot merge until the
  check passes and `gh pr merge --auto` waits for it. The build's write deploy key is the
  ruleset's bypass actor so the automated SVG commit still lands.
- Repository scaffolding to match my other repos: a CI workflow that compile and
  import checks the generator, a gitleaks secret scan, Dependabot auto-merge, a
  `.gitattributes` that marks the generated SVGs and `CODE_OF_CONDUCT.md`,
  `SECURITY.md` and this changelog. Dependency update PRs and stale branch cleanup
  are handled centrally by repo-ops, so this repo carries no `dependabot.yml` or
  branch maintenance workflow.

### Fixed

- Commits, PR reviews and lifetime Contribs were silently undercounting every private
  repo. GitHub's `contributionsCollection` withholds private-repo detail from every API
  caller, even the account owner, unless the token carries the classic `read:user`
  scope; no fine-grained permission grants this, confirmed empirically by testing
  the same query with and without that scope on an otherwise identical token. Added
  `CONTRIB_TOKEN`, a classic PAT scoped to `read:user` alone with no `repo` access at
  all, used only for the contribution and streak queries, so `ACCESS_TOKEN`'s own
  repo-content permissions stay exactly as narrow as before.

## 2026-07-06

### Fixed

- Stopped meta-mirror's weekly JSON backup commits inflating my profile Lines of
  Code. The generator now reads each commit's headline and skips commits titled
  `chore: update metadata backup`, so roughly 400k lines of backup data no longer
  count. Because it recomputes from full history every run the number self
  corrected on the next build, from about 801,927 to about 399,182 (#10, #12).
- Forced GitHub to refetch the stats image after the LOC fix. GitHub caches the SVG
  by URL, so with an unchanged filename it kept serving the stale numbers. Bumped
  the cache version query on all three README references from `?v=4` to `?v=5`
  (#11, #13).

## 2026-07-05

### Changed

- Dropped the in-workflow forge mirroring. mirror-ops now carries this repo to
  GitLab, Codeberg, Bitbucket and Gitea server side, so the build only pushes to
  GitHub (#8).
- Counted organisation member repos in the Lines of Code total, crediting only my
  own commits in shared repos (#7).
- Bumped the checkout, setup-python and cache actions to their Node 24 majors.

### Fixed

- Made the SVG push conflict proof. Builds are serialised and the push rebases and
  retries onto the latest `main`, so concurrent runs no longer clash (#9).

## 2026-07-04

### Changed

- Switched the build commit to my GitHub noreply email so the automated refresh
  attributes to me cleanly.

## 2026-06-20

### Changed

- Added Newsletter and Now links to the README nav and moved Contact to the end.

## 2026-06-15

### Added

- `.github/FUNDING.yml` with GitHub Sponsors, Buy Me a Coffee and Patreon links
  (#6, closes #5).

## 2026-06-13

### Changed

- Switched the build commit identity from my personal address to my main email and
  refreshed the SVGs.

## 2026-06-07

### Changed

- Reordered the languages section, bumped the SVG cache version and cleaned up the
  `.gitignore`.

## 2026-06-05

### Changed

- Overhauled the profile SVG layout and content, refined the hobbies section and
  status line and finalised the layout tweaks.
- Added my website URL to the LICENSE copyright line.

### Fixed

- Fixed forge mirroring: mirror to Gitea over SSH, creating the `.ssh` directory
  before the keyscan and force-pushing while temporarily unprotecting GitLab `main`
  so the mirror push is accepted (#4).

## 2026-06-04

### Added

- Streak stats, new languages and hobbies and portrait tweaks, plus pushing SVG
  updates to Gitea.com on every build.

### Fixed

- Restored the `ascii_final.txt` portrait asset.
- Pushed SVGs to GitHub before mirroring to the other forges.
- Widened the SVG canvas to 1080px to stop the Languages.Hardware row overflowing,
  and set `LINE_WIDTH` to 66 so every row right-aligns to one vertical edge.
- Used a full clone so Gitea accepts the first push to a new repo.

## 2026-05-20

### Changed

- Workflow maintenance.

## 2026-05-15

### Added

- A looping typing animation for the README, `approach_dark.svg` and
  `approach_light.svg`, that types each line, holds and resets (#2).

### Changed

- Renamed `today.py` to `isaacadjei.py` and updated the workflow to match (#1).
- Section headers now use the main text colour, the schedule moved from daily to
  every six hours so stats stay fresh, trimmed the approach SVG top padding and set
  the workflow to commit under my own name and email (#3).
- Added a newsletter link to the nav.

## 2026-05-14

### Changed

- Restructured the profile card with Mode, Kernel and Status rows, moved the nav
  links above the card for visibility and added website and links to the nav.

### Fixed

- Busted the GitHub README cache to force the SVG to re-render.

## 2026-05-13

### Added

- The first version of my GitHub profile README: an animated SVG portrait with live
  GitHub stats, generated by `isaacadjei.py` into `dark_mode.svg` and
  `light_mode.svg` and committed back by GitHub Actions.

---

The generator also commits an automated `chore: update profile SVG` refresh on its
schedule. Those routine regenerations are omitted here.
