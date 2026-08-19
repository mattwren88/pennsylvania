# Keystone Atlas — A Layered Map of Pennsylvania

An interactive map of Pennsylvania: every PHMC historical marker, plus seventy
layers of parks, trails, waterways, boundaries, geology, mine workings, natural
landmarks and vanished places, drawn over real street geography.

No build step and no dependencies to install — Leaflet, D3 and topojson load from
CDN and every data layer is fetched live. It does need to be served rather than
opened off disk, because browsers block `fetch` of `data/markers.json` from a
`file://` origin:

```
python3 -m http.server 8000    # then open http://localhost:8000
```

## What's on it

**Historical markers** — 2,585 with coordinates, merged from the PHMC CSV export
and the live PHMC map service (neither is a superset of the other). Full marker
text, dedication year, standing/missing status, and links out to Google Maps and
HMdb.

**Layers**, lazy-loaded the first time you tick them:

| Group | Layers |
| --- | --- |
| Map style | USGS topo quads, quad boundaries, railways |
| Protected land | State parks, state forests, wild & natural areas, game lands, forest districts, PA Wilds, local parks, park campgrounds, conserved land, easements |
| Trails | Appalachian Trail, rail trails, statewide land trails, state park hiking trails, bike routes, snowmobile trails, A.T. shelters |
| Water | Stocked trout waters, boat & river access, historic stream network, major watersheds, state scenic rivers, historic & breached dams |
| Geology & ice | Physiographic provinces, bedrock geology, the Late Wisconsinan glacial border, eskers, coal fields, earthquakes 1724–2003 |
| Curiosities | Covered bridges, fire towers & lookouts, geoheritage sites |
| Rails & roads | Rail lines, Amtrak stations, highway tunnels, bridges built before 1900, Turnpike interchanges |
| Boundaries | Municipalities, school districts, State House & Senate districts, U.S. Congressional districts, unpaved roads |
| Survey & industry | NGS survey monuments, historic oil & gas wells |
| Places & names | Populated places, post offices, locales, churches & cemeteries, named mines & tunnels, CCC camps, places that are gone |
| Natural landmarks | County high points, county maximum elevations, summits & ridges, waterfalls & springs, dams & reservoirs |
| Mining & underground | AML problem areas, AML inventory points, coal mining operations, reclamation projects, digitized mined areas, longwall panels, underground mine permits, mine portals |
| Hazards | FEMA flood hazard, environmental justice areas |

The base map is part of that list rather than a separate control. **Map style**
sits at its head: four sheets to draw on — roads, terrain hillshade, plain paper,
satellite — as one-of-four switches, with the topo quads, quad boundaries and
railway overlays stacking on top of whichever you pick.

**Tools** — search across markers, every loaded layer and the USGS gazetteer at
once; filter by county and dedication decade; a distance measure; a collapsible
legend that lists what is drawn and can switch any of it back off; and a
shareable URL that encodes the view, the base map, the active layers, the decade
and the selected marker or feature.

## Data sources

- **PASDA** (Pennsylvania Spatial Data Access, Penn State) — every live layer,
  via ArcGIS REST at `mapservices.pasda.psu.edu`. Underlying agencies: PHMC,
  DCNR and the PA Geological Survey, PennDOT, DEP, PA Fish & Boat, PA Game
  Commission, WeConservePA, FEMA, NGS, USGS and HIFLD.
- **U.S. Census** county geometry, via `us-atlas`.
- **OpenStreetMap** street tiles; **Esri** hillshade & satellite imagery; **USGS**
  topo quads via Esri; **OpenRailwayMap** railway overlay (CC-BY-SA).
- `data/phmc-historical-markers.csv` — the PHMC marker export this was built from.
- `data/markers.json` — the parsed, coordinate-checked markers the page loads.

`markers.json` was merged from the CSV **and** the live PHMC map service, so it
is not reproducible from the CSV alone — don't regenerate it from scratch.
`tools/add-dedication-dates.mjs` augments it in place, copying the month and day
of each dedication across from the CSV (`node tools/add-dedication-dates.mjs`;
idempotent, leaves unmatched records untouched). 165 markers carry a `01/01`
date in the CSV as a stand-in for "day unknown"; those are kept as year-only.

## Notes on the data

Some honesty about what the sources do and don't support:

- **County high points** are the highest *named* summit in each county, derived
  from GNIS elevations. A county's true topographic maximum is often an unnamed
  rise on a ridge — that one is a separate layer, **county maximum elevations**,
  taken from DCNR's elevation model. The two rarely land in the same place, and
  the difference is the point of having both.
- **Bridges built before 1900** carry PennDOT's `YEARBUILT` for the structure,
  so a rebuilt deck on original abutments still reads as early. The `LOCATION`
  string is the inspector's own shorthand, printed verbatim.
- **Dam status and type letters** on the historic & breached dams layer are
  DEP's internal codes. There is no published key, so they are shown as-is
  rather than guessed at.
- **Digitized mined areas** were traced from operators' own mine maps, some a
  century old and surveyed to the standards of their day. They show what was
  reported as worked out, not a verified void.
- **Covered bridges and fire towers** are filtered out of the GNIS gazetteer by
  name — there is no dedicated layer for either, so these are the named features,
  not a complete inventory.
- **Trail activity flags** (hiking, biking, ATV) are undocumented codes; `1` is
  read as permitted and `2` as not. Uses that read as unknown are omitted.
- **"Places that are gone"** are features GNIS marks `(historical)`. The
  gazetteer records no closure date or cause — only the name, location, and when
  the USGS logged it.
- Some services are national despite their name — PASDA's `HIFLD_FEMA_PA` is one,
  and so is the USGS quad grid. Those layers carry an explicit state filter in
  their `where` clause; anything added from them later needs the same, or it will
  quietly drag in the rest of the country.
- Everything is clipped to Pennsylvania on the way in, so a layer's feature count
  will often come in under the count the service reports. The earthquake layer
  holds 232 epicentres and draws 188 — the rest are just over the line.
- Large layers load only what the viewport covers and reload as you pan. A fetch
  that hits the paging cap says so rather than reporting a truncated count.

## Structure

```
index.html                        the whole application
data/markers.json                 parsed PHMC markers
data/phmc-historical-markers.csv  the source export
data/live-links.json              third-party park/trail URLs verified to still resolve
tools/add-dedication-dates.mjs    copies dedication month/day into markers.json
tools/check-layers.py             probes every PASDA source the page declares
tools/check-links.py              re-verifies the links in data/live-links.json
docs/site-health.md               what to check periodically, and how often
assets/styles.css                 Classical design system (tokens + stylesheet)
assets/favicon.svg                tab icon (+ favicon-180.png for iOS)
assets/og.jpg                     1200×630 social preview card
```

## Before going live

- Street tiles come from OpenStreetMap's community tile server, and the railway
  overlay from OpenRailwayMap's. Both are fine for modest traffic; move to a
  provider with a usage allowance (MapTiler, Stadia) if the site gets popular.

## Disclaimer & support

An independent, personal project — not affiliated with, endorsed by, or representing
the Commonwealth of Pennsylvania, the PHMC, or any other agency. All data is drawn
from public sources and presented as-is, with no warranty of accuracy or
completeness; not for navigation, boundary, or safety decisions.

Free, no ads. If it's useful: [☕ support the map](https://ko-fi.com/keystoneatlas).
