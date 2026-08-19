#!/usr/bin/env python3
"""Probe every PASDA layer index.html declares.

The atlas fetches all seventy layers live, so a service that PASDA renumbers,
retires or reissues with renamed columns breaks a layer silently — the checkbox
still ticks, nothing draws. This asks each source for one record and reports the
layers that answer wrongly.

    python3 tools/check-layers.py            # summary
    python3 tools/check-layers.py -v         # list every layer, healthy or not

Checked per source: the endpoint resolves, it returns a feature, and every field
the layer's `fields:` list names is actually present. `fields:'*'` skips the
column check. Exits non-zero if anything failed, so CI can run it.
"""
import argparse, concurrent.futures as cf, json, pathlib, re, sys, urllib.error, urllib.parse, urllib.request

PASDA = 'https://mapservices.pasda.psu.edu/server/rest/services/pasda/'
INDEX = pathlib.Path(__file__).resolve().parent.parent / 'index.html'


def layers():
    """Every {id, sources, fields} the DATA table declares, read straight from the page."""
    html = INDEX.read_text()
    for block in re.finditer(r"\{group:'.*?(?=\n \{group:'|\n\];)", html, re.S):
        text = block.group(0)
        ident = re.search(r"id:'([^']+)'", text)
        if not ident:
            continue
        srcs = re.findall(r"src:'([^']+)'", text)
        multi = re.search(r"srcs:\[([^\]]+)\]", text)
        if multi:
            srcs += re.findall(r"'([^']+)'", multi.group(1))
        if not srcs:
            continue                      # raster tiles and the local marker layers
        fields = re.search(r"fields:'([^']*)'", text)
        yield ident.group(1), srcs, (fields.group(1) if fields else '')


def ask(src, capped):
    p = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'f': 'json'}
    if capped:
        p['resultRecordCount'] = 1
    return json.load(urllib.request.urlopen(PASDA + src + '/query?' + urllib.parse.urlencode(p), timeout=90))


def probe(job):
    ident, src, fields = job
    if not re.search(r'/\d+$', src):
        # A bare MapServer is drawn as an image through /export, not queried for
        # features — there is no layer index to ask, so reaching it is the whole test.
        try:
            urllib.request.urlopen(PASDA + src + '?f=json', timeout=90).read(1)
            return ident, src, None
        except (urllib.error.URLError, TimeoutError) as e:
            return ident, src, f'unreachable ({type(e).__name__})'
    try:
        d = ask(src, True)
        # A few services refuse resultRecordCount outright; ask again unbounded.
        if 'error' in d and 'agination' in str(d['error'].get('message', '')):
            d = ask(src, False)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        return ident, src, f'unreachable ({type(e).__name__})'
    if 'error' in d:
        return ident, src, 'service error: ' + str(d['error'].get('message', ''))[:60]
    feats = d.get('features') or []
    if not feats:
        return ident, src, 'no features returned'
    if fields and fields != '*':
        have = set(feats[0]['attributes'])
        missing = [f for f in fields.split(',') if f and f not in have]
        if missing:
            return ident, src, 'missing fields: ' + ', '.join(missing)
    return ident, src, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-v', '--verbose', action='store_true', help='list healthy layers too')
    args = ap.parse_args()

    jobs = [(i, s, f) for i, srcs, f in layers() for s in srcs]
    print(f'probing {len(jobs)} sources across {len({j[0] for j in jobs})} layers\n')
    bad = []
    with cf.ThreadPoolExecutor(12) as ex:
        for ident, src, problem in ex.map(probe, jobs):
            if problem:
                bad.append((ident, src, problem))
                print(f'  FAIL  {ident:14} {src:46} {problem}')
            elif args.verbose:
                print(f'  ok    {ident:14} {src}')
    print(f'\n{len(jobs) - len(bad)}/{len(jobs)} sources healthy')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
