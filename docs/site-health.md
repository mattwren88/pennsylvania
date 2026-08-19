# Site health checklist

Everything on this map is fetched live from somebody else's server, and the page
has no build step to fail loudly when one of them changes. That is the trade: no
dependencies to maintain, but a layer can go dark without a single line of our
code changing. This is the list of things to check, and how often.

Run the two scripts from the repo root. Both need only Python 3 and `curl`.

## Every few months

**1. Probe the data layers.**

```
python3 tools/check-layers.py          # -v to list the healthy ones too
```

Asks each of the 76 PASDA sources for one record and checks that the columns
each layer names still exist. Exits non-zero on any failure. This is the check
that matters most: PASDA renumbers and retires services without notice, and the
symptom in the browser is a checkbox that ticks and draws nothing.

- *unreachable* — usually PASDA being down. Re-run before believing it.
- *service error / no features* — the service moved. Find the new endpoint in
  the [PASDA REST directory](https://mapservices.pasda.psu.edu/server/rest/services/pasda)
  and update `src:` in the layer's entry in `index.html`.
- *missing fields* — the service was reissued with renamed columns. The layer
  still draws; its detail panel is what quietly empties out. Fix `fields:` and
  the `rows:`/`name:` functions that read them.

**2. Open the page and tick through a few layers**, at least one per group. The
prober confirms a service answers; it cannot tell you the geometry still lands in
Pennsylvania or that the styling reads. Check the map at both a state-wide zoom
and a street-level one.

**3. Click a state park and a campground.** Both link out through `parkPage()`,
which builds a pa.gov URL from the park name rather than trusting the dead
`WEBLINK` field. If PA reorganizes that path again, every one of the 124 breaks
at once — and a wrong slug 404s rather than redirecting, so this is quick to spot.

## Twice a year

**4. Re-check the third-party website links.**

```
python3 tools/check-links.py           # ~4 minutes, rewrites data/live-links.json
```

Municipal and trail-club sites in the PASDA records rot continuously — only 39%
survived the last sweep. The script re-verifies them and commits the survivors,
which is what `checked()` filters against at runtime. Expect the count to fall
each time; that is the data aging, not the script breaking. Commit the rewritten
`data/live-links.json` along with its new `checked` date.

**5. Refresh the marker data.** `data/markers.json` is a snapshot of the PHMC CSV
export merged with their live service, and the page merges the live PHMC service
over it again at boot (`mergePhmc()`) — so new markers do appear without a
refresh, and this is about the baseline drifting, not the map going stale. Pull a
current CSV export from PHMC into `data/phmc-historical-markers.csv`, re-run
`node tools/add-dedication-dates.mjs` (idempotent, augments in place), and confirm
the header count still looks sane. There is no script that rebuilds `markers.json`
from scratch; that merge was done once by hand.

## Once a year, or after any dependency news

**6. Check the CDN pins.** Leaflet 1.9.4 and topojson-client 3.1.0 load from
unpkg with SRI hashes; `us-atlas` 3.0.1 comes from jsDelivr unpinned by hash.
All three are exact-version pins, so they will not shift under us — but a
security advisory against Leaflet is the one thing here that would need a same-day
bump, and bumping means recomputing the `integrity` attribute.

**7. Check the tile providers.** OpenStreetMap, Esri hillshade and imagery, USGS
topo via Esri, and OpenRailwayMap are all used under their terms as courtesy
services. If any of them starts requiring a key or rate-limits us, tiles go blank
or grey while everything else keeps working. The OSM tile policy is the one worth
re-reading if traffic grows.

**8. Confirm the domain and certificate.** `keystoneatlas.org` is served by GitHub
Pages from `CNAME`. Certificate renewal is automatic; the failure mode to watch is
the custom-domain setting being dropped by a repo change, which shows up as a
certificate warning or a redirect to the `github.io` address.

## What is deliberately not checked

The 70+ layers' *content* — whether DEP's mine data is current, whether a park
boundary moved. We render what the agencies publish and say so in the About
modal; correcting their data is not this project's job.
