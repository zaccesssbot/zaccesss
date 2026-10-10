#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
# copyright (c) 2026 Isaac Adjei <https://isaacadjei.me>
#
# this generator script is licensed under the PolyForm Noncommercial License 1.0.0;
# see NOTICE.md. The repository's visual output (the SVGs, the README and the
# assets) is licensed under CC BY-NC-ND 4.0; see LICENSE.
"""
profile.py - my GitHub profile README SVG generator.

I generate three SVG cards (profile.svg, profile-dark.svg and profile-light.svg):
  - profile.svg: theme-adaptive card (dark palette by default, light under prefers-color-scheme)
  - profile-dark.svg: fixed dark-mode card for <picture> source tags, for hosts that don't
    honour @media queries inside an <img>-embedded SVG
  - profile-light.svg: fixed light-mode card for the same <picture> source tags
  - Left column:  my ASCII art portrait (44 cols x 30 rows, loaded from ascii_profile.txt)
  - Right column: neofetch-style info block + live GitHub stats pulled from the API

To run locally I need my ACCESS_TOKEN set as an environment variable:
    export ACCESS_TOKEN=<fine-grained-PAT>
    python profile/profile.py
"""

import os
import sys
import datetime
import requests
from dateutil.relativedelta import relativedelta
from html import escape as esc

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

USERNAME   = 'zaccesss'  # GitHub username to query

ASCII_ART_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'ascii_profile.txt')  # path to ASCII portrait file, one level up in the repo root
GRAPHQL_URL    = 'https://api.github.com/graphql'  # GitHub GraphQL endpoint

# portrait dimensions (rows must match ascii_profile.txt line count)
ASCII_ROWS = 30  # must match the line count of ascii_profile.txt

SVG_WIDTH  = 1120  # total canvas width in pixels; +40 vs the old 1080 to keep pace with LINE_WIDTH
                    # going 66->70, so the right margin past the stats column stays roughly level
                    # with ASCII_X's 35px left margin instead of the widened column eating into it
ROW_STEP   = 20   # vertical gap between rows in pixels
ROW_START  = 30   # y-coordinate of the first row

# right column char width: dots are calculated so every value ends here.
# 70 not 66: the extra 4 chars are the slack the Repos/Streak curly-brace rows need to always
# align, verified by exhaustively checking every digit-length combination up to 999 repos/
# contributed and 9999 streak days (get_streak() is no longer capped at one year of history, so
# a multi-year streak is a real possibility, not just a hypothetical) - see shared_brace_col().
LINE_WIDTH = 70   # character budget for the right column; dots fill to this width exactly

ASCII_X = 35   # left edge of the ASCII portrait column
STATS_X = 410  # left edge of the stats column
ASCII_FONT_SIZE = 13  # px; a size down from the 16px stats font so the 44-char-wide portrait
                       # leaves a real gap before STATS_X instead of almost touching it
ASCII_Y_OFFSET = ROW_STEP  # visually centres the portrait after the taller Git Stats block

# stats rows: content goes to row 33 (y=690); SVG height adds bottom margin.
STATS_ROWS = 34                                                        # total number of rows in the stats block
SVG_HEIGHT = ROW_START + (STATS_ROWS - 1) * ROW_STEP + ROW_STEP + 20  # 730px total canvas height

# ---------------------------------------------------------------------------
# colour schemes
# ---------------------------------------------------------------------------

DARK = {
    'bg':     '#161b22',
    'text':   '#c9d1d9',
    'key':    '#ffa657',
    'value':  '#a5d6ff',
    'add':    '#3fb950',
    'delete': '#f85149',
    'dots':   '#616e7f',
}

LIGHT = {
    'bg':     '#f6f8fa',
    'text':   '#24292f',
    'key':    '#953800',
    'value':  '#0a3069',
    'add':    '#1a7f37',
    'delete': '#cf222e',
    'dots':   '#c2cfde',
}

# ---------------------------------------------------------------------------
# ASCII art loader
# ---------------------------------------------------------------------------

def load_ascii_art(path: str) -> list[str]:
    """Return ASCII_ROWS strings of 44 chars each from ascii_profile.txt."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    result = []
    for i in range(ASCII_ROWS):
        line = lines[i] if i < len(lines) else ''
        result.append(line.ljust(44)[:44])  # pad short lines to exactly 44 chars and clip any that are longer
    return result

# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def graphql(token: str, query: str, variables: dict | None = None) -> dict:
    headers = {'Authorization': f'bearer {token}', 'Content-Type': 'application/json'}  # bearer auth for GitHub API
    resp = requests.post(GRAPHQL_URL,
                         json={'query': query, 'variables': variables or {}},
                         headers=headers, timeout=30)  # 30-second timeout so a slow API cannot hang the workflow
    resp.raise_for_status()
    result = resp.json()
    if 'errors' in result:
        raise RuntimeError(f'GraphQL errors: {result["errors"]}')
    return result.get('data', {})


def get_user_info(token: str, username: str) -> tuple[int, int, int, int, int, int, str]:
    """Return (followers, prs, contributed_repos, issues, gists, creation_year, created_at)."""
    data = graphql(token, """
        query ($login: String!) {
            user(login: $login) {
                followers { totalCount }
                pullRequests { totalCount }
                issues { totalCount }
                gists(first: 1, privacy: PUBLIC) { totalCount }
                repositoriesContributedTo(
                    first: 1
                    contributionTypes: [COMMIT, PULL_REQUEST, PULL_REQUEST_REVIEW, ISSUE, REPOSITORY]
                    includeUserRepositories: true
                ) { totalCount }
                createdAt
            }
        }""", {'login': username})
    u = data.get('user', {})
    created_at = u.get('createdAt', '2022-01-01T00:00:00Z')
    return (
        u.get('followers',                  {}).get('totalCount', 0),
        u.get('pullRequests',               {}).get('totalCount', 0),
        u.get('repositoriesContributedTo',  {}).get('totalCount', 0),
        u.get('issues',                     {}).get('totalCount', 0),
        u.get('gists',                      {}).get('totalCount', 0),
        int(created_at[:4]),  # slice the year from the ISO timestamp, for the contributions-since-creation loop
        created_at,
    )


def get_repos_stars_and_forks(token: str, username: str) -> tuple[int, int, int]:
    """Return (total_repos, total_stars, total_forks) across repos I own or belong to as an org member.

    Matches get_loc's affiliation list below, so joining an org counts its repos here the same
    way it already counts towards lines of code, rather than this stat staying personal-only.
    """
    query = """
        query ($login: String!, $cursor: String) {
            user(login: $login) {
                repositories(first: 100, after: $cursor, ownerAffiliations: [OWNER, ORGANIZATION_MEMBER],
                             orderBy: {field: UPDATED_AT, direction: DESC}) {
                    nodes { stargazerCount forkCount }
                    pageInfo { hasNextPage endCursor }
                    totalCount
                }
            }
        }"""
    stars, forks, total, cursor, first = 0, 0, 0, None, True
    while True:
        r = graphql(token, query, {'login': username, 'cursor': cursor})
        r = r.get('user', {}).get('repositories', {})
        if first:
            total, first = r.get('totalCount', 0), False  # capture total count from the first page only
        stars += sum(n.get('stargazerCount', 0) for n in r.get('nodes', []))
        forks += sum(n.get('forkCount', 0) for n in r.get('nodes', []))
        page = r.get('pageInfo', {})
        if not page.get('hasNextPage'):
            break
        cursor = page.get('endCursor')
    return total, stars, forks


def get_contributions_for_year(token: str, username: str, year: int) -> tuple[int, int, int]:
    """Return (commits, reviews, total_contributions) for one calendar year."""
    data = graphql(token, """
        query ($login: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                    totalCommitContributions
                    totalPullRequestReviewContributions
                    contributionCalendar {
                        totalContributions
                    }
                }
            }
        }""", {'login': username,
               'from': f'{year}-01-01T00:00:00Z',
               'to':   f'{year}-12-31T23:59:59Z'})
    collection = (data.get('user', {})
                      .get('contributionsCollection', {}))
    return (
        collection.get('totalCommitContributions', 0),
        collection.get('totalPullRequestReviewContributions', 0),
        collection.get('contributionCalendar', {}).get('totalContributions', 0),
    )


def get_contribution_days_for_year(token: str, username: str, year: int) -> list[tuple[str, int]]:
    """Return [(date, contributionCount), ...] for one calendar year, sorted by date."""
    data = graphql(token, """
        query ($login: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                    contributionCalendar {
                        weeks {
                            contributionDays {
                                contributionCount
                                date
                            }
                        }
                    }
                }
            }
        }""", {'login': username,
               'from': f'{year}-01-01T00:00:00Z',
               'to':   f'{year}-12-31T23:59:59Z'})
    weeks = (data.get('user', {})
                 .get('contributionsCollection', {})
                 .get('contributionCalendar', {})
                 .get('weeks', []))
    return sorted(
        [(d['date'], d['contributionCount']) for w in weeks for d in w.get('contributionDays', [])],
        key=lambda x: x[0]
    )

def get_streak(token: str, username: str, creation_year: int) -> tuple[int, int]:
    """Return (current_streak_days, longest_streak_days) across the account's full history.

    GitHub's contributionsCollection caps out at one year of days per query (its default, with
    no from/to, is the trailing 365 days), which is not the same thing as the account's real
    streak history once the account is more than a year old. A genuine 400 day streak would get
    silently truncated to whatever the trailing year covers. So instead of one bare query, I walk
    every calendar year from account creation to today, same pattern as get_all_contributions(),
    and run the streak count over the full stitched-together history rather than a single window.
    """
    days = []
    for year in range(creation_year, datetime.datetime.utcnow().year + 1):
        try:
            days.extend(get_contribution_days_for_year(token, username, year))
        except Exception as e:
            print(f'  Warning (streak {year}): {e}', file=sys.stderr)
    days.sort(key=lambda x: x[0])
    longest = current_run = 0
    for _, count in days:
        if count > 0:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 0
    # don't penalise the streak if today has no contributions yet
    today = datetime.date.today().isoformat()
    days_to_check = [(d, c) for d, c in days if d <= today]
    if days_to_check and days_to_check[-1][0] == today and days_to_check[-1][1] == 0:
        days_to_check = days_to_check[:-1]
    current = 0
    for _, count in reversed(days_to_check):
        if count > 0:
            current += 1
        else:
            break
    return current, longest


def get_all_contributions(token: str, username: str, creation_year: int) -> tuple[int, int, int]:
    """Sum commits, reviews and total contributions across every year since account creation."""
    commits = reviews = total_contribs = 0
    for year in range(creation_year, datetime.datetime.utcnow().year + 1):  # walk every year from account creation to today
        try:
            year_commits, year_reviews, year_total = get_contributions_for_year(token, username, year)
            commits += year_commits
            reviews += year_reviews
            total_contribs += year_total
        except Exception as e:
            print(f'  Warning (contributions {year}): {e}', file=sys.stderr)
    return commits, reviews, total_contribs


# repos left out of the lines of code: isaacadjei.me is a generated public copy of the portfolio's
# source, rebuilt on every release, so counting it would count the same lines twice. meta-mirror holds
# automated metadata backups rather than code anyone wrote
LOC_EXCLUDE_REPOS = {'zaccesss/isaacadjei.me', 'zaccesss/meta-mirror'}


def get_loc(token: str, username: str) -> tuple[int, int, int]:
    """
    Total LOC across all owned non-forked repos.
    Counts commits by this user (including unlinked terminal commits).
    Returns (added, deleted, net).
    """
    repos = []
    cursor = None
    while True:
        data = graphql(token, """
            query ($login: String!, $cursor: String) {
                user(login: $login) {
                    repositories(first: 100, after: $cursor,
                                 ownerAffiliations: [OWNER, ORGANIZATION_MEMBER], isFork: false) {
                        nodes { nameWithOwner isEmpty defaultBranchRef { name } }
                        pageInfo { hasNextPage endCursor }
                    }
                }
            }""", {'login': username, 'cursor': cursor})
        rd = data.get('user', {}).get('repositories', {})
        for n in rd.get('nodes', []):
            if not n.get('isEmpty') and n.get('defaultBranchRef'):
                repos.append(n['nameWithOwner'])
        page = rd.get('pageInfo', {})
        if not page.get('hasNextPage'):
            break
        cursor = page.get('endCursor')

    commit_q = """
        query ($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100, after: $cursor) {
                                nodes {
                                    additions deletions messageHeadline
                                    author { user { login } }
                                }
                                pageInfo { hasNextPage endCursor }
                            }
                        }
                    }
                }
            }
        }"""
    add, delete = 0, 0
    for repo in repos:
        if repo.lower() in LOC_EXCLUDE_REPOS:
            continue
        owner, name = repo.split('/', 1)
        # only in the owner's own repos are unlinked terminal commits credited (they're the owner's).
        # in org/shared repos an unlinked commit could be someone else's, so there
        # the commit must be authored by the owner.
        is_own_repo = owner.lower() == username.lower()
        cursor = None
        try:
            while True:
                data = graphql(token, commit_q,
                               {'owner': owner, 'name': name, 'cursor': cursor})
                history = (data.get('repository', {})
                               .get('defaultBranchRef', {})
                               .get('target', {})
                               .get('history', {}))
                for c in history.get('nodes', []):
                    # skip the automated metadata backup commits (from the meta-mirror repo) so their
                    # JSON dumps do not inflate the lines of code with data nobody actually wrote.
                    if c.get('messageHeadline', '') == 'chore: update metadata backup':
                        continue
                    login = ((c.get('author') or {}).get('user') or {}).get('login', '')
                    if login.lower() == username.lower() or (is_own_repo and not login):
                        add    += c.get('additions', 0)
                        delete += c.get('deletions', 0)
                page = history.get('pageInfo', {})
                if not page.get('hasNextPage'):
                    break
                cursor = page.get('endCursor')
        except Exception as e:
            print(f'  Warning (LOC {repo}): {e}', file=sys.stderr)
    return add, delete, add - delete

# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------

def fmt(n: int) -> str:
    return f'{n:,}'  # comma-separated thousands (e.g. 1,234)


def fmt_uptime(created_at: str) -> str:
    """Return account age as 'Xy Yd' (neofetch-style uptime), from an ISO createdAt timestamp.

    Calendar-exact rather than delta_days // 365: a flat 365 divisor doesn't know about leap
    years, so it drifts the day count by roughly a day for every leap year the account has lived
    through; it would eventually misattribute a whole year once that drift piles up. relativedelta
    walks real calendar months and years instead, so the split is exact regardless of how many
    leap years fall inside the span.
    """
    created = datetime.date.fromisoformat(created_at[:10])
    today = datetime.date.today()
    delta = relativedelta(today, created)
    days = (today - (created + relativedelta(years=delta.years))).days
    return f'{delta.years}y {days}d'


def pad_dots(label: str, value: str, width: int = LINE_WIDTH) -> str:
    """
    Return dots so that '. LABEL: DOTS VALUE' = width chars exactly.
    The full value string (including any trailing text like '( add++, del-- )')
    must be passed so dots are calculated correctly.
    """
    n = width - 2 - len(label) - 2 - 1 - len(str(value))  # 2 = '. ', 2 = ': ', 1 = space before value
    return '.' * max(1, n)

# ---------------------------------------------------------------------------
# SVG fragment builders
# ---------------------------------------------------------------------------

def cc(t: str)  -> str: return f'<tspan class="cc">{esc(t)}</tspan>'    # punctuation and dots colour class
def key(t: str) -> str: return f'<tspan class="key">{esc(t)}</tspan>'   # label colour class
def val(t: str) -> str: return f'<tspan class="value">{esc(t)}</tspan>' # value colour class

def trow(y: int, content: str) -> str:
    return f'    <tspan x="{STATS_X}" y="{y}">{content}</tspan>'  # pin each row to the stats column x-offset

def info_row(y: int, label: str, value: str) -> str:
    """Standard right-aligned info row."""
    return trow(y, cc('. ') + key(label) + cc(f': {pad_dots(label, str(value))} ') + val(str(value)))

def section_header(y: int, title: str) -> str:
    # section headers match the weight of the first "isaac@adjei" line,
    # so the whole thing - title and hyphens - uses the main text colour, no grey.
    hyphens = '-' * max(2, LINE_WIDTH - 2 - len(title) - 1)
    return trow(y, f'- {title} {hyphens}')

def blank(y: int) -> str:
    return trow(y, '')

PIPE_LEFT = 36  # chars from line-start to the space before ' | '; pins | column

def dual_row(y: int, lbl1: str, v1: str, lbl2: str, v2: str) -> str:
    """Two key-value pairs with the | separator pinned to column PIPE_LEFT."""
    d1 = max(1, PIPE_LEFT - 5 - len(lbl1) - len(v1))
    d2 = max(1, LINE_WIDTH - PIPE_LEFT - 6 - len(lbl2) - len(v2))
    return trow(y,
        cc('. ') + key(lbl1) + cc(f': {"."*d1} ') + val(v1) +
        cc(' | ') + key(lbl2) + cc(f': {"."*d2} ') + val(v2))

RIGHT_BUDGET = LINE_WIDTH - PIPE_LEFT - 3  # chars available for 'lbl2: .. v2_main {detail_lbl: .. detail_val}'

def brace_inner_len(detail_lbl: str, detail_val: str) -> int:
    """Length of the unpadded 'detail_lbl: detail_val' text a dual_row_detail row puts inside its braces."""
    return len(f'{detail_lbl}: {detail_val}')

def brace_col_range(lbl2: str, v2_main: str, detail_lbl: str, detail_val: str) -> tuple[int, int]:
    """(min, max) column the '{' can land on for this row, as chars from the start of its own
    'lbl2: ...' text up to and including the space right before '{'.

    min is with the dot-leader at its 1-dot floor (as tight as the row can be). max is with the
    inner brace text at its natural, unpadded length (as loose as the row can be before it either
    has to shrink real digits, which we never do or blow past the LINE_WIDTH row budget).
    """
    p_min = len(lbl2) + len(v2_main) + 5
    p_max = RIGHT_BUDGET - 2 - brace_inner_len(detail_lbl, detail_val)
    return p_min, p_max

def shared_brace_col(rows: list[tuple[str, str, str, str]]) -> int:
    """Target '{' column for a group of dual_row_detail rows, chosen so whichever row naturally
    needs the most room sets the target and the others stretch their dot-leader to match.

    dual_row_detail clamps this per-row to its own brace_col_range, so a row that can't afford
    the target (its max < target) still lands as close as it safely can instead of overflowing -
    the only way two rows end up misaligned is when their safe ranges genuinely don't overlap,
    which is now the true minimum misalignment rather than an artifact of an overly strict cap.
    """
    return max(brace_col_range(*row)[0] for row in rows)

def dual_row_detail(y: int, lbl1: str, v1: str, lbl2: str, v2_main: str, detail_lbl: str, detail_val: str,
                     brace_col: int | None = None) -> str:
    """Headline stat on left paired with a right stat containing detailed info in key-coloured curly braces.
    e.g. '. Contribs: 1,234 | Repos: 15 {Contrib: 8}'
         '. Uptime: 3y 145d | Streak: 5d {Best: 42d}'

    Pass brace_col (from shared_brace_col() across a group of rows) to align the opening and
    closing braces with those other rows: both the outer dot-leader (before v2_main) and the
    inner one (inside the braces) stretch to land '{' on that column, so '}' lands in sync too
    since every row is still exactly LINE_WIDTH chars wide. brace_col is clamped to this row's
    own safe range first, so it can only ever pad up to what the LINE_WIDTH budget allows - it can
    never push a row past it.
    """
    p_min, p_max = brace_col_range(lbl2, v2_main, detail_lbl, detail_val)
    p = p_min if brace_col is None else max(p_min, min(brace_col, p_max))
    d2 = p - len(lbl2) - len(v2_main) - 4
    natural_inner = brace_inner_len(detail_lbl, detail_val)
    gap = max(0, (RIGHT_BUDGET - p - 2) - natural_inner)
    dots = '.' * gap
    d1 = max(1, PIPE_LEFT - 5 - len(lbl1) - len(v1))
    v2_svg = (f'<tspan class="value">{esc(v2_main)} {{'
              f'<tspan class="key">{esc(detail_lbl)}</tspan>: ' +
              (f'<tspan class="cc">{dots}</tspan>' if dots else '') +
              f'{esc(detail_val)}}}</tspan>')
    return trow(y,
        cc('. ') + key(lbl1) + cc(f': {"."*d1} ') + val(v1) +
        cc(' | ') + key(lbl2) + cc(f': {"."*d2} ') + v2_svg)

def contribs_repos_row(y: int, lbl1: str, v1: str, repos: int, contributed: int, brace_col: int | None = None) -> str:
    """Any headline stat paired with Repos (Contributed in key-coloured curly braces) on the right."""
    return dual_row_detail(y, lbl1, v1, 'Repos', fmt(repos), 'Contrib', fmt(contributed), brace_col=brace_col)

def loc_dual_row(y: int, total: int, add: int, delete: int) -> str:
    """Lines of Code on left, add/del breakdown on right with } aligned to right edge."""
    net_str = fmt(total)
    add_str = fmt(add)
    del_str = fmt(delete)
    d1 = max(1, PIPE_LEFT - 5 - len('Lines of Code') - len(net_str))
    right_chars = LINE_WIDTH - PIPE_LEFT - 3
    inner = f'{add_str}++, {del_str}--'
    total_pad = right_chars - 2 - len(inner)
    lp = ' ' * (total_pad // 2)
    rp = ' ' * (total_pad - total_pad // 2)
    rhs = (f'{{{lp}<tspan class="addColor">{esc(add_str)}</tspan>++, '
           f'<tspan class="delColor">{esc(del_str)}</tspan>--{rp}}}')
    return trow(y,
        cc('. ') + key('Lines of Code') + cc(f': {"."*d1} ') + val(net_str) +
        cc(' | ') + rhs)

# ---------------------------------------------------------------------------
# SVG builder
# ---------------------------------------------------------------------------

def build_svg(
    ascii_rows: list[str],
    repos: int, contributed: int, stars: int, forks: int,
    commits: int, followers: int,
    prs: int, issues: int, reviews: int, gists: int,
    total_contribs: int, uptime: str,
    loc_total: int, loc_add: int, loc_del: int,
    current_streak: int, longest_streak: int,
    mode: str = 'adaptive',
) -> str:

    if mode == 'dark':
        base_palette = DARK
        media_override = ""
    elif mode == 'light':
        base_palette = LIGHT
        media_override = ""
    else:  # adaptive
        base_palette = DARK
        media_override = f"""
      @media (prefers-color-scheme: light) {{
        .bg       {{ fill: {LIGHT['bg']};     }}
        .fg       {{ fill: {LIGHT['text']};   }}
        .key      {{ fill: {LIGHT['key']};    }}
        .value    {{ fill: {LIGHT['value']};  }}
        .addColor {{ fill: {LIGHT['add']};    }}
        .delColor {{ fill: {LIGHT['delete']}; }}
        .cc       {{ fill: {LIGHT['dots']};   }}
      }}"""

    style = f"""
      @font-face {{
        src: local('Consolas'), local('Consolas Bold');
        font-family: 'ConsolasFallback';
        font-display: swap;
        size-adjust: 109%;
      }}
      .bg       {{ fill: {base_palette['bg']};     }}
      .fg       {{ fill: {base_palette['text']};   }}
      .key      {{ fill: {base_palette['key']};    }}
      .value    {{ fill: {base_palette['value']};  }}
      .addColor {{ fill: {base_palette['add']};    }}
      .delColor {{ fill: {base_palette['delete']}; }}
      .cc       {{ fill: {base_palette['dots']};   }}
      text, tspan {{ white-space: pre; }}{media_override}
    """

    # ASCII art at ASCII_FONT_SIZE: keeps 44-char lines clear of the stats column at x={STATS_X}
    ascii_tspans = [
        f'    <tspan x="{ASCII_X}" y="{ROW_START + ROW_STEP + 10 + ASCII_Y_OFFSET + i * ROW_STEP}">{esc(line)}</tspan>'
        for i, line in enumerate(ascii_rows)
    ]

    Y = [ROW_START + i * ROW_STEP for i in range(STATS_ROWS)]

    header_dashes = '-' * (LINE_WIDTH - len('isaac@adjei '))

    # repos {Contrib} and Streak {Best} share one '{' column target so both braces align vertically.
    # dual_row_detail clamps this to each row's own safe range, so it can only ever land as close
    # as that row's budget allows - it can't push either row past the LINE_WIDTH row budget.
    brace_col_target = shared_brace_col([
        ('Repos', fmt(repos), 'Contrib', fmt(contributed)),
        ('Streak', f'{fmt(current_streak)}d', 'Best', f'{fmt(longest_streak)}d'),
    ])

    stats_tspans = [
        trow(Y[0],  f'isaac@adjei {header_dashes}'),

        info_row(Y[1],  'Host',     'Aston University'),
        info_row(Y[2],  'Mode',     'EECS'),
        info_row(Y[3],  'Region',   'LHR <-> BHX'),
        info_row(Y[4],  'Kernel',   'Sleep deprived but functional'),
        info_row(Y[5],  'OS',       'Windows, macOS, Ubuntu, Linux'),
        info_row(Y[6],  'IDE',      'JetBrains, VS Code, Visual/Microchip Studio'),

        blank(Y[7]),

        info_row(Y[8],  'Languages.Tools',       'Git, Shell, Bash, Docker, Make, CI/CD'),
        info_row(Y[9],  'Languages.Software',    'C, C++, Python, TypeScript, Rust'),
        info_row(Y[10], 'Languages.Hardware',    'Embedded C, MATLAB, MicroPy, FPGA/VHDL'),
        info_row(Y[11], 'Languages.Web',          'HTML, CSS, PHP/Laravel, React, Next.js'),
        info_row(Y[12], 'Languages.Spoken',        'English, French, Twi, Ga'),

        blank(Y[13]),

        info_row(Y[14], 'Hobbies.Tech',      'CyberSec, Cloud, DevOps, Hackathons'),
        info_row(Y[15], 'Hobbies.Software',  'Full Stack, Open Source, DB, AI/ML/DS'),
        info_row(Y[16], 'Hobbies.Hardware',  'Embedded Systems, MCUs, PCBs, Robotics'),
        info_row(Y[17], 'Hobbies.General',  'Fitness, Travel, Piano, Reading, Gaming'),
        info_row(Y[18], 'Hobbies.Status',   'rm -rf impostor_syndrome && touch grass'),

        blank(Y[19]),

        section_header(Y[20], 'Contact'),
        info_row(Y[21], 'Discord',        'zac.cess'),
        info_row(Y[22], 'LinkedIn',       'in/isaacadjei'),
        info_row(Y[23], 'Portfolio',      'isaacadjei.me'),
        info_row(Y[24], 'Email.Main',     'hello@isaacadjei.me'),
        info_row(Y[25], 'Email.Work',     'contact@isaacadjei.me'),

        blank(Y[26]),

        section_header(Y[27], 'Git Stats'),
        dual_row(Y[28], 'Followers',      fmt(followers),        'Stars',          fmt(stars)),
        # forks and Gists are both 0 right now, so this row returns once there are some.
        # dual_row(Y[?], 'Forks',        fmt(forks),            'Gists',          fmt(gists)),
        dual_row(Y[29], 'Commits',        fmt(commits),          'PRs',            fmt(prs)),
        dual_row(Y[30], 'Issues',         fmt(issues),           'Reviews',        fmt(reviews)),
        # the three curly-brace detail rows sit together at the bottom, by design.
        contribs_repos_row(Y[31], 'Contribs', fmt(total_contribs), repos, contributed, brace_col=brace_col_target),
        dual_row_detail(Y[32], 'Uptime', uptime,   'Streak',         f'{fmt(current_streak)}d', 'Best', f'{fmt(longest_streak)}d', brace_col=brace_col_target),
        loc_dual_row(Y[33], loc_total, loc_add, loc_del),
    ]

    ascii_block = '\n'.join(ascii_tspans)
    stats_block = '\n'.join(stats_tspans)

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg"
     font-family="ConsolasFallback,Consolas,monospace"
     width="{SVG_WIDTH}px" height="{SVG_HEIGHT}px"
     font-size="16px">
  <defs><style>{style}  </style></defs>
  <rect width="{SVG_WIDTH}px" height="{SVG_HEIGHT}px" class="bg" rx="15"/>
  <!-- ASCII portrait: {ASCII_FONT_SIZE}px so 44-char lines leave a gap before x={STATS_X} -->
  <text x="{ASCII_X}" y="{ROW_START}" class="fg" font-size="{ASCII_FONT_SIZE}px"
        xml:space="preserve" style="white-space:pre;">
{ascii_block}
  </text>
  <!-- Stats block -->
  <text x="{STATS_X}" y="{ROW_START}" class="fg" style="white-space:pre;">
{stats_block}
  </text>
</svg>"""

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.environ.get('ACCESS_TOKEN', '').strip()
    if not token:
        print('ERROR: ACCESS_TOKEN environment variable is not set.', file=sys.stderr)
        sys.exit(1)
    # GitHub's contributionsCollection withholds private-repo detail (commits, reviews, the
    # calendar) from every API caller, even the account owner, unless the token carries the
    # classic read:user scope - no fine-grained permission grants this. CONTRIB_TOKEN is a
    # separate classic PAT scoped to read:user only, with no repo access at all, so there is no need
    # to widen ACCESS_TOKEN's own repo-content permissions just to see private contributions.
    # falls back to ACCESS_TOKEN so this still runs (with public-only contribution counts) before
    # the secret exists or for local testing with a token that already carries read:user.
    contrib_token = os.environ.get('CONTRIB_TOKEN', '').strip() or token
    username = os.environ.get('USER_NAME', USERNAME)  # USER_NAME env var overrides the hardcoded default

    print('Loading ASCII art...')
    ascii_rows = load_ascii_art(ASCII_ART_PATH)

    print('Fetching GitHub stats...')
    try:
        followers, prs, contributed, issues, gists, creation_year, created_at = get_user_info(token, username)
    except Exception as e:
        print(f'  Warning: {e}', file=sys.stderr)
        # safe defaults if the API call fails
        followers, prs, contributed, issues, gists, creation_year, created_at = 0, 0, 0, 0, 0, 2022, '2022-01-01T00:00:00Z'
    uptime = fmt_uptime(created_at)

    try:
        repos, stars, forks = get_repos_stars_and_forks(token, username)
    except Exception as e:
        print(f'  Warning: {e}', file=sys.stderr)
        repos, stars, forks = 0, 0, 0

    print('  Counting commit and review contributions...')
    try:
        commits, reviews, total_contribs = get_all_contributions(contrib_token, username, creation_year)
    except Exception as e:
        print(f'  Warning: {e}', file=sys.stderr)
        commits, reviews, total_contribs = 0, 0, 0

    print('  Calculating lines of code...')
    try:
        loc_add, loc_del, loc_total = get_loc(token, username)
    except Exception as e:
        print(f'  Warning: {e}', file=sys.stderr)
        loc_add, loc_del, loc_total = 0, 0, 0

    print('  Fetching streak stats...')
    try:
        current_streak, longest_streak = get_streak(contrib_token, username, creation_year)
    except Exception as e:
        print(f'  Warning: {e}', file=sys.stderr)
        current_streak, longest_streak = 0, 0

    print(f'  Followers: {followers} | Stars: {stars}')
    print(f'  Repos: {repos} | Contributed: {contributed} | Contribs: {total_contribs}')
    print(f'  Forks: {forks} | Gists: {gists}')
    print(f'  Commits: {commits} | PRs: {prs}')
    print(f'  Issues: {issues} | Reviews: {reviews}')
    print(f'  Account: {creation_year} | Uptime: {uptime}')
    print(f'  LOC: {fmt(loc_total)} ({fmt(loc_add)}++, {fmt(loc_del)}--)')
    print(f'  Streak: {current_streak} days current, {longest_streak} days best')

    print('Generating profile.svg (adaptive), profile-dark.svg and profile-light.svg...')
    stat_args = (
        ascii_rows,
        repos, contributed, stars, forks,
        commits, followers, prs, issues, reviews, gists,
        total_contribs, uptime,
        loc_total, loc_add, loc_del,
        current_streak, longest_streak,
    )
    out_dir = os.path.dirname(__file__)
    with open(os.path.join(out_dir, 'profile.svg'), 'w', encoding='utf-8') as f:
        f.write(build_svg(*stat_args, mode='adaptive'))
    with open(os.path.join(out_dir, 'profile-dark.svg'), 'w', encoding='utf-8') as f:
        f.write(build_svg(*stat_args, mode='dark'))
    with open(os.path.join(out_dir, 'profile-light.svg'), 'w', encoding='utf-8') as f:
        f.write(build_svg(*stat_args, mode='light'))
    print('Done.')



if __name__ == '__main__':
    main()
