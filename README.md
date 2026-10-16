# Denver's median sale price peaked at $595,000 in 2022 - and has held a band since

A Machine Readable data brief (2026-10-16), built on the assessor
sales keystone of the Denver locality stack and layered with the
permit and demolition records from
[denver-net-housing-change-data-brief](https://github.com/adowlen/denver-net-housing-change-data-brief).

Denver recorded 105,585 market sales from 2020 through the October 15,
2026 snapshot of the assessor's sales and transfers ledger (2026
partial; sales substantially complete through August 31, 2026). The
median price rose from $450,000 in 2020 to $595,000 in 2022 and has
held between $525,000 and $550,000 since. The share of sales at or
under $500,000 fell from 57.2 percent (2020) to 38.6 percent (2022)
and recovered to 47.4 percent (2025). On the parcel record, 70.8
percent of the 3,297 parcels with a demolition dated in the window
later received a new-building permit (a floor; recent demolitions
have had less time), and the 611 parcels that completed a full
recorded cycle show a median difference of $1,635,000 between their
purchase and post-permit sale deeds, before construction and
financing costs.

Proposed repository name: **denver-property-sales-data-brief**
(full URL on publication: https://github.com/adowlen/denver-property-sales-data-brief)

## Contents

- `brief-draft.md` - the full brief, including "What this might mean" and "Who can act"
- `charts/` - hero.png plus four data charts (yearly cycle, neighborhood median map, neighborhood change, teardown lifecycle)
- `data/` - the derived neighborhood table (neighborhood_sales.csv; change percentages resting on fewer than 30 sales in either period are flagged in the file's small_n_flag column and are not ranked in the brief)
- `code/` - audit.py (section 10 pre-flight), analyze.py, charts.py, compose_hero.py, verify_independent.py (section 11)
- `stats.json` - every headline figure in machine-readable form
- `sources.md` - numbered source audit
- `verification.md` - pre-flight audit output, independent verification ledger, methods checklist
- `reviewer-notes.md` - claims most likely to be challenged, surprises, checks not completed
- `social-drafts.md` - LinkedIn post, personal repost comment, X thread (for Alex's approval)

## Data sources

City and County of Denver open data (ArcGIS): Real Property Sales and
Transfers (table 51), Parcels (layer 245), Residential Characteristics
(table 50), statistical neighborhoods, and the residential construction
and demolition permit layers, all snapshotted 2026-10-15 through the
Machine Readable Denver warehouse. Full audit in sources.md.

## Reproduce

```
python code/audit.py               # section 10 pre-flight gates (must pass first)
python code/analyze.py             # writes stats.json and data/neighborhood_sales.csv
python code/charts.py              # redraws the data charts
python code/verify_independent.py  # section 11 independent recomputation; writes verification_results.json
```

(Python environment: pandas, numpy, matplotlib, Pillow, pyarrow.)

## Caveats (short version)

- "Market sale" is a derived definition (warranty or special warranty
  deed with a recorded price above zero). The source is a transfers
  ledger: 17.9 percent of its rows record zero or no price and are
  excluded from price figures.
- All prices are nominal dollars as recorded, and medians describe
  what sold in each period, not a repeat-sales price index.
- Prices are never summed across parcels; one transaction spanning
  several parcels repeats its price on each parcel row.
- The snapshot's sales are substantially complete through August 31,
  2026; September-October 2026 are recording-lag partials.
- Parcel-basis and permit-basis figures from the companion brief are
  different units and are labeled wherever they appear.
