# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
# copyright (c) 2026 Isaac Adjei <https://isaacadjei.me>
"""Tests for the generator's retry and last good value handling. No network: requests.post is
replaced with a stub for every test and the retry waits are skipped."""

import importlib.util
import json
import os
import sys

import pytest
import requests

HERE = os.path.dirname(os.path.abspath(__file__))


def load_generator():
    # loaded by path under its own name because the stdlib also has a module called profile
    sys.path.insert(0, HERE)  # palettes.py lives beside the generator
    spec = importlib.util.spec_from_file_location('profile_card', os.path.join(HERE, 'profile.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gen(monkeypatch, tmp_path):
    module = load_generator()
    monkeypatch.setattr(module.time, 'sleep', lambda s: None)  # no real waiting between attempts
    monkeypatch.setattr(module, 'OUT_DIR', str(tmp_path))
    monkeypatch.setattr(module, 'LAST_GOOD_PATH', str(tmp_path / 'last-good.json'))
    monkeypatch.setenv('ACCESS_TOKEN', 'test-token')
    monkeypatch.delenv('CONTRIB_TOKEN', raising=False)
    return module


class FakeResponse:
    def __init__(self, status: int, body: dict | None = None):
        self.status_code = status
        self._body = body or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f'{self.status_code}', response=self)

    def json(self):
        return self._body


# one GraphQL answer that satisfies every query the generator sends. Each query reads only its
# own fields, so the extra ones are ignored.
GOOD_DATA = {
    'user': {
        'followers': {'totalCount': 7}, 'pullRequests': {'totalCount': 8}, 'issues': {'totalCount': 9},
        'gists': {'totalCount': 1}, 'repositoriesContributedTo': {'totalCount': 5},
        'createdAt': '2024-12-05T19:07:18Z',
        'repositories': {
            'nodes': [{'stargazerCount': 3, 'forkCount': 2, 'nameWithOwner': 'zaccesss/demo',
                       'isEmpty': False, 'defaultBranchRef': {'name': 'main'}}],
            'pageInfo': {'hasNextPage': False, 'endCursor': None}, 'totalCount': 1,
        },
        'contributionsCollection': {
            'totalCommitContributions': 10, 'totalPullRequestReviewContributions': 2,
            'contributionCalendar': {'totalContributions': 12, 'weeks': [
                {'contributionDays': [{'date': '2026-01-01', 'contributionCount': 1},
                                      {'date': '2026-01-02', 'contributionCount': 1}]}]},
        },
    },
    'repository': {'defaultBranchRef': {'target': {'history': {
        'nodes': [{'additions': 100, 'deletions': 40, 'messageHeadline': 'feat: x',
                   'author': {'user': {'login': 'zaccesss'}}}],
        'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}},
}

STORED = {
    'contributions': {'commits': 3537, 'reviews': 1205, 'total_contribs': 8957, 'updated': '2026-11-03T18:01:36Z'},
    'lines_of_code': {'added': 2317191, 'deleted': 358510, 'net': 1958681, 'updated': '2026-11-03T14:22:29Z'},
    'repos': {'forks': 58, 'repos': 131, 'stars': 93, 'updated': '2026-11-03T18:01:36Z'},
    'streak': {'best': 49, 'current': 36, 'updated': '2026-11-03T18:01:36Z'},
    'user': {'contributed': 151, 'created_at': '2024-12-05T19:07:18Z', 'creation_year': 2024,
             'followers': 25, 'gists': 32, 'issues': 1708, 'prs': 2197, 'updated': '2026-11-03T18:01:36Z'},
}


def test_graphql_retries_502_then_succeeds(gen, monkeypatch):
    answers = [FakeResponse(502), FakeResponse(502), FakeResponse(502),
               FakeResponse(200, {'data': {'ok': True}})]
    calls = []
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: (calls.append(k), answers.pop(0))[1])
    waited = []
    monkeypatch.setattr(gen.time, 'sleep', waited.append)

    assert gen.graphql('t', 'query { ok }') == {'ok': True}
    assert len(calls) == 4
    assert waited == [2, 4, 8]


def test_graphql_gives_up_after_the_waits(gen, monkeypatch):
    calls = []
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: (calls.append(1), FakeResponse(502))[1])
    with pytest.raises(gen.TransientAPIError):
        gen.graphql('t', 'query { ok }')
    assert len(calls) == 4


def test_graphql_does_not_retry_a_client_error(gen, monkeypatch):
    calls = []
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: (calls.append(1), FakeResponse(401))[1])
    with pytest.raises(requests.exceptions.HTTPError):
        gen.graphql('t', 'query { ok }')
    assert len(calls) == 1


def test_graphql_retries_a_connection_error(gen, monkeypatch):
    answers = [requests.exceptions.ConnectionError('down'), FakeResponse(200, {'data': {'ok': 1}})]

    def post(*a, **k):
        a = answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a
    monkeypatch.setattr(gen.requests, 'post', post)
    assert gen.graphql('t', 'q') == {'ok': 1}


def test_successful_run_writes_svgs_and_last_good(gen, monkeypatch, tmp_path):
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: FakeResponse(200, {'data': GOOD_DATA}))
    gen.main()
    for name in ('profile.svg', 'profile-dark.svg', 'profile-light.svg'):
        assert (tmp_path / name).exists()
    store = json.loads((tmp_path / 'last-good.json').read_text())
    assert sorted(store) == ['contributions', 'lines_of_code', 'repos', 'streak', 'user']
    assert store['lines_of_code'] == {'added': 100, 'deleted': 40, 'net': 60,
                                      'updated': store['lines_of_code']['updated']}
    assert store['user']['followers'] == 7
    assert store['repos'] == {'repos': 1, 'stars': 3, 'forks': 2, 'updated': store['repos']['updated']}
    assert sorted(store['streak']) == ['best', 'current', 'updated']
    assert store['streak']['current'] == store['streak']['best'] > 0
    # sorted and indented so the committed file diffs cleanly
    assert (tmp_path / 'last-good.json').read_text() == json.dumps(store, indent=2, sort_keys=True) + '\n'


def test_every_fetch_failing_uses_the_stored_values(gen, monkeypatch, tmp_path, capsys):
    (tmp_path / 'last-good.json').write_text(json.dumps(STORED, indent=2, sort_keys=True) + '\n')
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: FakeResponse(502))

    gen.main()

    svg = (tmp_path / 'profile.svg').read_text()
    for figure in ('1,958,681', '2,317,191', '358,510', '3,537', '2,197', '1,708', '1,205', '8,957',
                   '36d', '49d'):
        assert figure in svg
    assert '>Forks<' in svg and '>58<' in svg and '>Gists<' in svg and '>32<' in svg and '>93<' in svg
    err = capsys.readouterr().err
    for group, stamp in (('lines_of_code', '2026-11-03T14:22:29Z'), ('streak', '2026-11-03T18:01:36Z'),
                         ('user', '2026-11-03T18:01:36Z'), ('repos', '2026-11-03T18:01:36Z'),
                         ('contributions', '2026-11-03T18:01:36Z')):
        assert f'Carried over {group} from last-good.json ({stamp})' in err
    # a carried over group keeps its old timestamp; nothing was fetched so nothing changes
    assert json.loads((tmp_path / 'last-good.json').read_text()) == STORED


def test_no_last_good_file_exits_one_without_an_svg(gen, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(gen.requests, 'post', lambda *a, **k: FakeResponse(502))

    with pytest.raises(SystemExit) as exit_info:
        gen.main()

    assert exit_info.value.code == 1
    assert not list(tmp_path.glob('*.svg'))
    assert not (tmp_path / 'last-good.json').exists()
    assert 'holds no value for it; not writing any SVG' in capsys.readouterr().err


def test_a_transient_error_mid_loop_gives_the_group_up(gen, monkeypatch, tmp_path):
    # the first query (user info) succeeds, then the API goes away. Lines of code must not be
    # stored as a partial total; the stored value is carried over instead.
    (tmp_path / 'last-good.json').write_text(json.dumps(STORED) + '\n')
    state = {'n': 0}

    def post(*a, **k):
        state['n'] += 1
        return FakeResponse(200, {'data': GOOD_DATA}) if state['n'] <= 2 else FakeResponse(503)
    monkeypatch.setattr(gen.requests, 'post', post)

    gen.main()

    store = json.loads((tmp_path / 'last-good.json').read_text())
    assert store['user']['followers'] == 7                      # fetched this run
    assert store['lines_of_code'] == STORED['lines_of_code']    # carried over, not zero or partial
    assert store['streak'] == STORED['streak']


def test_stars_and_forks_are_the_raw_github_sums_across_pages(gen, monkeypatch):
    # two pages of repositories: the totals are stargazerCount and forkCount summed as GitHub
    # reports them, with the repo count taken from the first page only
    pages = [
        {'user': {'repositories': {'totalCount': 3, 'pageInfo': {'hasNextPage': True, 'endCursor': 'c1'},
                                   'nodes': [{'stargazerCount': 80, 'forkCount': 50},
                                             {'stargazerCount': 5, 'forkCount': 6}]}}},
        {'user': {'repositories': {'totalCount': 3, 'pageInfo': {'hasNextPage': False, 'endCursor': None},
                                   'nodes': [{'stargazerCount': 8, 'forkCount': 2}]}}},
    ]
    cursors = []

    def post(*a, **k):
        cursors.append(k['json']['variables']['cursor'])
        return FakeResponse(200, {'data': pages[len(cursors) - 1]})
    monkeypatch.setattr(gen.requests, 'post', post)

    assert gen.get_repos_stars_and_forks('t', 'zaccesss') == (3, 93, 58)
    assert cursors == [None, 'c1']
