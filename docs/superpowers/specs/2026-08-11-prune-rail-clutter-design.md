# Prune the marker-type filter and "On this day"

**Date:** 2026-08-11
**Status:** Approved

## Problem

Three surfaces in the rail and results pane earn less than they cost:

1. **The `All marker types` dropdown** ([index.html:376](../../../index.html)) filters markers to
   Roadside, City, or Plaque. Markers are already a toggleable layer, and the three types are
   already explained by three colored rows in the legend. The dropdown is a second, redundant
   place to think about marker types.
2. **The "On this day" accordion** fills the results pane when nothing is searched. It is a
   novelty that occupies the pane a user is about to type into.
3. **The "Historical markers" group heading** that replaces it once a search or filter runs.
   Marker hits are the implicit result set; labeling them adds a row without adding meaning.

## Non-goals

- No change to `TYPE_STYLE` or how markers are painted. The map keeps three colors.
- No change to the legend's three "Roadside / City / Plaque marker" rows. The colors on the
  map still need explaining.
- No change to dedication-date data. `m.d` and `MONTHS` stay; `dedicated()` still formats
  "dedicated August 11, 1947" in the marker detail panel.
- No change to the county filter, the decade timeline, or the search box.

## Changes

### 1. Remove the marker-type filter

Delete:

- `<select class="input" id="type">` in the rail ([index.html:376](../../../index.html))
- The `insertAdjacentHTML` that populates it with `['Roadside','City','Plaque']`
  ([index.html:1523-1524](../../../index.html))
- Its `change` → `applyFilters` listener ([index.html:2387](../../../index.html))

In `markerKeep()` ([index.html:1662](../../../index.html)), drop the `ty` read and the
`(!ty||m.t===ty)` term from the returned predicate.

In `renderResults()` ([index.html:1731](../../../index.html)), drop the `ty` read and its term
from the idle guard, leaving `if(!q&&!co&&!state.decade&&!state.sel) return renderIdle(box);`.

**URL compatibility:** none required. `writeHash()` never wrote the type filter, so no shared
link can carry one.

### 2. Remove "On this day"

`renderIdle(box)` ([index.html:1699-1724](../../../index.html)) collapses to the hint it already
falls back to when today has no anniversaries:

```js
function renderIdle(box){
  box.innerHTML='<div class="rail-pad kicker">Search a name, or pick a county, to list what is here</div>';
}
```

That makes the following dead — delete them:

- `onThisDay()` ([index.html:1687-1692](../../../index.html))
- The `CAL` icon constant ([index.html:1695-1697](../../../index.html))
- The `CHEV` icon constant ([index.html:1693-1694](../../../index.html)) — the accordion is its
  only consumer. The rail handle and legend head each inline their own chevron SVG.
- The `otdShut` flag ([index.html:1698](../../../index.html))
- The `.acc-head`, `.acc-head:hover`, `.acc-head .n`, `.acc-head .chev`, `.acc.shut .acc-head
  .chev`, and `.acc.shut .acc-body` CSS rules ([index.html:90-99](../../../index.html)) — the
  accordion is their only consumer.

Verify before deleting each of the three shared-looking items (`CHEV`, `.chev` styles, `.acc*`
styles) that no other call site exists. `.chev` as a bare class *is* used elsewhere
(the rail's sheet toggle); only the `.acc`-scoped rules go.

### 3. Suppress the "Historical markers" heading when it stands alone

In `renderResults()` ([index.html:1774-1780](../../../index.html)), the group render currently
emits a `.grp-head` for every group. Change it to omit the heading when there is exactly one
group and that group is the markers group.

Headings still render whenever a second group is present — a loaded layer's hits, or the USGS
gazetteer — because those groups need distinguishing from each other.

### 4. Preserve the truncation signal

The heading carries `Historical markers · 40 of 812` today, which is the only cue that marker
results cap at 80 (`state.filtered.slice(0,80)`). The persistent `812 markers shown` counter
([index.html:355](../../../index.html)) reports the *filter* total, not the truncation.

When the heading is suppressed **and** the list is truncated, append a footer line below the
results in the same style the accordion used for its own overflow note:

```html
<div class="rail-pad kicker">80 of 812 shown</div>
```

Render it only when `state.filtered.length > 80`. When the heading is shown (multi-group case),
it keeps its existing `· N of M` suffix and no footer is added — the signal is never duplicated.

## Verification

Load the page and confirm:

1. The rail shows the search box, the county select, and the timeline — no type select.
2. The legend still lists three marker rows with three distinct colors, and the map still
   paints Roadside, City, and Plaque in their own hues.
3. With nothing searched, the results pane shows only the one-line hint.
4. Searching a term that matches markers and nothing else lists them with no heading.
5. Searching a term matching over 80 markers shows `N of M shown` beneath the list.
6. Turning on a data layer and searching a term matching both shows headings for both groups,
   with the markers heading carrying its `· N of M` suffix and no footer beneath.
7. Opening a marker still shows "dedicated August 11, 1947" style text where a date exists.
8. An existing shared link (`#z/lat/lon/base/layers/...`) still restores its view.
9. No console errors, and no dead references to `onThisDay`, `CAL`, `CHEV`, or `otdShut`.
