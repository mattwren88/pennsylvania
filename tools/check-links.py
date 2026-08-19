#!/usr/bin/env python3
"""Regenerate data/live-links.json.

The website fields PASDA carries for local parks and rail trails are municipal and
trail-club addresses collected years ago, and roughly two in three no longer resolve
to the page the record meant. There is no derivable replacement and the page cannot
test them at load time (no CORS on those hosts), so the surviving set is checked here
and committed. Re-run occasionally; expect the list to shrink.

    python3 tools/check-links.py

A URL is kept only if it answers 2xx and does not redirect to a shallower path —
a park page that bounces to the borough homepage is a dead end with a 200 on it.
"""
import concurrent.futures as cf, datetime, json, pathlib, subprocess, urllib.parse, urllib.request

PASDA = 'https://mapservices.pasda.psu.edu/server/rest/services/pasda/'
SOURCES = [('DCNR/MapServer/18', 'URL'), ('DCNR/MapServer/4', 'MGMT_WEBSI')]
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
OUT = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'live-links.json'


def pull(src, field):
    """Every distinct non-empty value of one field, paged past the 1000-record cap."""
    seen, offset = set(), 0
    while True:
        q = PASDA + src + '/query?' + urllib.parse.urlencode({
            'where': f"{field} IS NOT NULL AND {field} <> ''", 'outFields': field,
            'returnGeometry': 'false', 'returnDistinctValues': 'true', 'f': 'json',
            'resultOffset': offset, 'resultRecordCount': 1000})
        feats = json.load(urllib.request.urlopen(q, timeout=120)).get('features', [])
        seen.update(v for f in feats if (v := (f['attributes'][field] or '').strip()))
        if len(feats) < 1000:
            return seen
        offset += 1000


def normalise(u):
    return u if u.lower().startswith(('http://', 'https://')) else 'https://' + u


def alive(u):
    r = subprocess.run(['curl', '-sL', '-o', '/dev/null', '-w', '%{http_code}\t%{url_effective}',
                        '--max-time', '30', '-A', UA, '--compressed', normalise(u)],
                       capture_output=True, text=True)
    try:
        code, effective = r.stdout.split('\t', 1)
    except ValueError:
        return u, False
    if not code.startswith('2'):
        return u, False
    src = [p for p in urllib.parse.urlparse(normalise(u)).path.split('/')
           if p and not p.lower().startswith('index.')]
    dst = [p for p in urllib.parse.urlparse(effective).path.split('/') if p]
    if src and len(dst) < len(src) and (not dst or dst[-1].lower() != src[-1].lower()):
        return u, False
    return u, True


def sweep(urls, workers):
    with cf.ThreadPoolExecutor(workers) as ex:
        return {u for u, ok in ex.map(alive, urls) if ok}


def main():
    urls = sorted(set().union(*(pull(src, field) for src, field in SOURCES)))
    print(f'{len(urls)} distinct URLs')
    good = sweep(urls, 24)
    # One retry at lower concurrency — a slow host timing out in the first sweep is
    # not the same thing as a dead one.
    good |= sweep([u for u in urls if u not in good], 8)
    OUT.write_text(json.dumps({
        'checked': datetime.date.today().isoformat(),
        'note': 'URLs from PASDA DCNR/MapServer/18 (local parks) and /4 (rail trails) that '
                'still resolved to their own page when last checked. '
                'Regenerate with tools/check-links.py.',
        'urls': sorted(good)}, separators=(',', ':')))
    print(f'{len(good)} of {len(urls)} alive -> {OUT}')


if __name__ == '__main__':
    main()
