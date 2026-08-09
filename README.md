# Keystone Atlas — A Layered Map of Pennsylvania

An interactive map of Pennsylvania: every PHMC historical marker, plus forty-odd
layers of parks, trails, waterways, boundaries, abandoned mine lands, natural
landmarks and vanished places, drawn over real street geography.

Open `index.html`. No build step, no dependencies to install — Leaflet, D3 and
topojson load from CDN and every data layer is fetched live.

## What's on it

**Historical markers** — 2,585 with coordinates, merged from the PHMC CSV export
and the live PHMC map service (neither is a superset of the other). Full marker
text, dedication year, standing/missing status, and links out to Google Maps,
ExplorePAhistory and HMdb.

**Layers**, lazy-loaded the first time you tick them:

| Group | Layers |
| --- | --- |
| Protected land | State parks, state forests, wild & natural areas, game lands, forest districts, PA Wilds, local parks, conserved land, easements |
| Trails | Appalachian Trail, rail trails, statewide land trails, bike routes, snowmobile trails, A.T. shelters |
| Water | Stocked trout waters, boat & river access, historic stream network |
| Curiosities | Covered bridges, fire towers & lookouts |
| Boundaries | Municipalities, school districts, State House & Senate districts, unpaved roads |
| Survey & industry | NGS survey monuments, historic oil & gas wells |
| Places & names | Populated places, post offices, locales, churches & cemeteries, named mines & tunnels, places that are gone |
| Natural landmarks | County high points, summits & ridges, waterfalls & springs, dams & reservoirs |
| Abandoned mine lands | AML problem areas, AML inventory points, coal mining operations, reclamation projects |
| Hazards | FEMA flood hazard, environmental justice areas |

**Tools** — search across markers, every loaded layer and the USGS gazetteer at
once; filter by county, marker type and dedication decade; four base maps
(roads, terrain hillshade, plain paper, satellite); a distance measure; a
collapsible legend; and a shareable URL that encodes the view, the active
layers, the decade and the selected marker. With nothing searched, the results
pane lists the markers dedicated on today's date.

## Data sources

- **PASDA** (Pennsylvania Spatial Data Access, Penn State) — every live layer,
  via ArcGIS REST at `mapservices.pasda.psu.edu`. Underlying agencies: PHMC,
  DCNR, PennDOT, DEP, PA Fish & Boat, PA Game Commission, WeConservePA, FEMA, NGS.
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
  rise on a ridge.
- **Covered bridges and fire towers** are filtered out of the GNIS gazetteer by
  name — there is no dedicated layer for either, so these are the named features,
  not a complete inventory.
- **Trail activity flags** (hiking, biking, ATV) are undocumented codes; `1` is
  read as permitted and `2` as not. Uses that read as unknown are omitted.
- **"Places that are gone"** are features GNIS marks `(historical)`. The
  gazetteer records no closure date or cause — only the name, location, and when
  the USGS logged it.
- Large layers load only what the viewport covers and reload as you pan. A fetch
  that hits the paging cap says so rather than reporting a truncated count.

## Structure

```
index.html                        the whole application
data/markers.json                 parsed PHMC markers
data/phmc-historical-markers.csv  the source export
tools/add-dedication-dates.mjs    copies dedication month/day into markers.json
assets/styles.css                 Classical design system (tokens + stylesheet)
assets/favicon.svg                tab icon (+ favicon-180.png for iOS)
assets/og.jpg                     1200×630 social preview card
```

## Before going live

- Replace `ko-fi.com/CHANGEME` with a real donation link (two spots in
  `index.html`, one below).
- Make `og:image` absolute — `https://<domain>/assets/og.jpg`. Twitter and some
  other scrapers ignore relative image paths.
- Street tiles come from OpenStreetMap's community tile server, and the railway
  overlay from OpenRailwayMap's. Both are fine for modest traffic; move to a
  provider with a usage allowance (MapTiler, Stadia) if the site gets popular.

## Disclaimer & support

An independent, personal project — not affiliated with, endorsed by, or representing
the Commonwealth of Pennsylvania, the PHMC, or any other agency. All data is drawn
from public sources and presented as-is, with no warranty of accuracy or
completeness; not for navigation, boundary, or safety decisions.

Free, no ads. If it's useful: [☕ support the map](https://ko-fi.com/CHANGEME).
