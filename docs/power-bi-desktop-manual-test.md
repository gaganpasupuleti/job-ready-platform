# Power BI Desktop — manual verification sheet

Status: **pending** (no automated Desktop run in CI). Do not mark `pending_desktop` workshop steps verified until these pass.

## Setup

1. Blank PBIX, follow workshop only (no reference file open).
2. Power BI Desktop 2024–2025, HTML Content **1.2.1.17**.

## Data & model

| # | Check | Pass |
|---|--------|------|
| 1 | All eight CSV imports refresh with `DataFolder` | ☐ |
| 2 | Table names match workshop (spaces) | ☐ |
| 3 | Four relationships active, single-direction from dimensions | ☐ |
| 4 | Date Table marked; months sort chronologically | ☐ |

## Measures (cleared slicers)

Compare to `expected-results.json` → `displayCurrency`:

| Measure | Expected (2dp USD) | Actual | Pass |
|---------|-------------------|--------|------|
| Total Sales | 44365028.02 | | ☐ |
| Total Cost | 31689305.73 | | ☐ |
| Total Profit | 12675722.29 | | ☐ |
| Total Orders (units) | 110402 | | ☐ |

Profit must equal Sales − Cost at display precision.

## D/W/M

| # | Check | Pass |
|---|--------|------|
| 5 | Fields parameter switches trend axis Day / Week / Month | ☐ |
| 6 | Percentile slicers change line conditional formatting | ☐ |

## Bars

| # | Check | Pass |
|---|--------|------|
| 7 | 100% stacked bar = Total Cost + Total Profit (composition) | ☐ |
| 8 | Separate target bar uses Target vs Previous month / Target Diff | ☐ |

## Toast

| # | Check | Pass |
|---|--------|------|
| 9 | No toast with no slicers | ☐ |
| 10 | Product / store / team filters show toast; animation replays | ☐ |
| 11 | Stylesheet measure applied; box-shadow CSS valid | ☐ |

## Bookmarks

| # | Bookmark display name | Pass |
|---|----------------------|------|
| 12 | Top Selected | ☐ |
| 13 | Bottom Selected | ☐ |
| 14 | Show date / Hide date | ☐ |
| 15 | --Show settings / --Hide settings | ☐ |
| 16 | Calendar show / close | ☐ |

## Persistence

| # | Check | Pass |
|---|--------|------|
| 17 | Save, close, reopen, refresh | ☐ |
