# Verification - Denver real property sales brief (assessor keystone)

Package built 2026-10-15 overnight for the 2026-10-16 brief, from the
Machine Readable Denver warehouse snapshots of 2026-10-15 (stack/denver).
Sections: pre-flight audit (standards section 10), methods checklist
(section 3) with the layering admission test, built-in controls (section
10.2.2), the section 11 independent verification ledger with its fix-loop
closure, and the adversarial review dispositions (section 11, pass 4).

## Pre-flight audit (standards section 10) - code/audit.py

Run BEFORE stats.json or prose were generated, against the warehouse
cleaned layers, and re-run after every fix-loop change. Final run: exit
code 0, 20 of 20 checks PASS. Decision-relevant output (the audit script
ships in code/ and prints the full INSTRUMENT / CLASS / D_CLASS_N
counters - 52, 10, and 89 distinct values - on every run):

```
sales rows: 313361; parcels: 240441; characteristics: 212850; spine: 240441
SALE_PRICE: negative=0, zero-or-null=56031 (17.9%)
[PASS] 10.1.1 no negative prices
[PASS] 10.1.1 zero/null prices are 'unknown', never market sales
[PASS] 10.1.1 every market sale has price > 0
RECEPTION_DATE outside 2015-01-01..2026-12-31: 343 rows (not used for sale dates)
[PASS] 10.1.1 all composed sale dates valid
[PASS] 10.1.1 SALE_YEAR span is 2015-2026 (catalog claims 2010) min=2015 max=2026
[PASS] 10.1.1 characteristics year_built unknown where CCYRBLT 0/null
[PASS] 10.1.1 characteristics living area unknown where AREA_ABG 0/null
[PASS] 10.1.4 market filter uses exactly the two sale-like deed types
[PASS] 10.1.2 polarity: inside rows all WD/SW with price > 0
[PASS] 10.1.2 polarity: $0 warranty deeds and quit claims are excluded
market-sale rows dated after the 2026-10-15 snapshot: 1 (excluded from dated figures in analyze.py, counted in stats.json)
[PASS] 10.1.1 future-dated rows are few and identified count=1 dates=['2026-12-30']
[PASS] 10.1.3 reconciliation: market sales with SALE_YEAR >= 2020 = 105,585 (Phase 1) got 105585
[PASS] 10.1.3 reconciliation: 2024 market sales n = 13,100, median $540,000 (Phase 1) n=13100 median=540000.0
[PASS] 10.1.5 neighborhood share denominator is the full population assigned=103823 unassigned=1762 of 105585
sales rows keyed to a current parcel: 308788 of 313360 (98.54%)
[PASS] 10.2 sales-to-parcel match >= 97% in every year 2020+
[PASS] 10.2 spine grain is one row per parcel
[PASS] 10.2 spine neighborhood coverage assigned=240335 of 240441
market-sale rows sharing a RECEPTION_NUM (2020+): 10343 rows in 3133 multi-parcel transactions; deal records = 98374 distinct reception numbers + 1 unnumbered row; extra parcel rows = 7210
[PASS] 10.2 multi-parcel duplication is measured, not ignored
CONTROL: parcels whose last-transfer reception number appears in the sales table: 152181; exact SALE_PRICE agreement between the two assessor products: 99.85%
[PASS] 10.2.2 control: cross-product price agreement >= 95%
AUDIT RESULT: ALL GATES PASS
```

Gate detail recorded by the audit:

- **10.1.1 sentinels.** No negative prices exist. Zero/null price
  (56,031 rows, 17.9 percent) maps to unknown and is never inside the
  market-sale set (asserted row by row). RECEPTION_DATE has 343 rows
  outside 2015-01-01..2026-12-31 (maximum 50250305); it is never used
  as a sale date - sale dates are composed from SALE_YEAR +
  SALE_MONTHDAY and all 313,361 compose to valid dates. One market-sale
  row is dated after the snapshot (2026-12-30); it is identified by the
  audit and excluded from dated figures in analyze.py under a printed
  exclusion (recorded population 105,585; dated analysis population
  105,584 - the audit's own population lines above are on the recorded
  basis). Characteristics sentinels (CCYRBLT 0/null, AREA_ABG 0/null)
  map to unknown in the cleaned layer.
- **10.1.2 polarity.** Three rows inside the filter (WD 2015
  $9,350,000; SW 2022 $13,500,000; WD 2017 $22,660,000) and three
  outside (WD 2016 $0 - correctly excluded; SW 2020 $0 - correctly
  excluded; QC 2023 $10 - quit claim, correctly excluded) printed by
  the audit and eyeballed: the code's behavior matches the definition
  in sources.md.
- **10.1.3 unit agreement.** Every rate names its unit on both sides:
  neighborhood assignment shares are over the full population;
  price-band shares are over each year's market-sale rows; the
  lifecycle shares are over rebuilt parcels (1,428 and 1,012 of 2,335).
  Prices are never summed (multi-parcel duplication: 10,343
  market-sale rows sit in 3,133 multi-parcel transactions; 7,210
  extra parcel rows beyond one per deal record).
- **10.1.4 exhaustiveness.** Full counters recorded by the audit
  before any filter. The market filter uses exactly WD and SW.
  AUDIT-CAUGHT CORRECTION: the full D_CLASS_N counter exposes an
  unhyphenated naming variant, 'RESIDENTIAL CONDOMINIUM' (97 rows in
  the 2020+ recorded market population), alongside
  'RESIDENTIAL-CONDOMINIUM'. The first composition mapping sent the
  variant to "Other"; the mapping counts both spellings as
  Condominium (24,764 sales in the dated population, 23.5 percent,
  median $330,000; "Other" is 521 rows and is now printed in Finding 3).
- **10.1.5 nullable denominators.** The only nullable classification
  used in a rate is neighborhood assignment; its denominator is the
  full population and determined + not-determined sum to the whole
  (asserted). No NaN-skipping mean is used anywhere in analyze.py.
- **10.2 join hygiene.** Sales-to-current-parcel match: 98.54 percent
  of keyed rows (308,788 of 313,360), by sale year 97.77-98.93 percent
  with no trend break - the match-rate drift the prep memo warned
  about does not materialize at a size that could move a median. One
  sales row carries a non-positive PARID and no key. AUDIT-ERA DEFECT
  FOUND BY THE SECTION 11 VERIFIER AND FIXED: the control join (below)
  originally coerced 5,463 non-numeric parcels-layer reception strings
  to NaN, and pandas matched NaN keys to the sales table's
  null-reception rows. The join now requires numeric keys on both
  sides, in audit.py and analyze.py alike.
- **10.3 sync gate.** README dependency list matches code imports
  (pandas, numpy, matplotlib, Pillow, pyarrow - no geopandas or
  shapely; the map's WKB geometry is parsed with the standard
  library). Every number in brief-draft.md, README.md, and
  social-drafts.md was cross-checked against the final stats.json
  after the last analyze.py run, including the figures changed by the
  fix loop (condominium variant, period definition, future-dated
  exclusion, control recomputation).

## Built-in controls (standards section 10.2.2)

1. **Cross-product control (primary).** The parcels layer carries the
   assessor's own last-transfer summary per parcel, produced by a
   different assessor product than the sales ledger. For the 152,181
   parcels whose last-transfer reception number matches a ledger row
   on a numeric key, the two products agree exactly on price for
   99.85 percent and on sale year for 99.91 percent. The 221
   disagreements are concentrated in the ambiguous population: in
   43.9 percent of them the ledger records a price of zero where the
   parcels summary carries one. (First-run values - 157,644 checked,
   96.50 percent - were contaminated by the NaN-key defect described
   under 10.2 above; the verifier's clean recomputation and the fixed
   builder code agree exactly on the corrected values.) The control
   proves the schedule-number join maps sales to the right parcels.
2. **Phase 1 reconciliation (external anchor).** The warehouse
   Phase 1 build and its independent verifier measured, from the raw
   snapshots with a separate implementation: 105,585 market sales
   2020+ and a 2024 median of $540,000 on n=13,100. This package's
   audit asserts both figures before any analysis runs; both match
   exactly.
3. **Permit-layer cross-check.** Recomputed from the warehouse
   permit and demolition layers in this build: 11,585 new-building
   permits and 3,837 demolition permits issued 2020-01-01 to
   2026-10-12 - exactly the published figures of the October 15 net
   housing change brief, from its own layers.
4. **Washington Park lifecycle control (cross-package).** This
   package's lifecycle code, run on Washington Park alone, gives 268
   demolished parcels and 237 rebuilt (88.4 percent) - exactly the
   pilot readout v2.1's independently verified counts. Its price
   medians differ from the pilot's by 1.5 percent or less (buy
   $1,034,500 over 176 parcels here vs $1,050,000 in the pilot; first
   post-permit sale $2,930,000 over 110 vs $2,965,000; paired 85 vs 84
   parcels, spread $2,140,000 vs $2,135,000, 28.8 vs 28.7 months).
   The deltas are edge definitions: this package takes the buy
   strictly before the first demolition date and the exit strictly
   after the first new-building permit date on the surviving-parcel
   record, and one additional parcel completes both sides under this
   reading. Recorded as REPRODUCED-WITH-EXPLAINED-DELTAS, not
   smoothed: the citywide figures in the brief are this package's own
   computation throughout.

## Methods checklist (standards section 3)

- Base rates and exposure: price figures are medians of recorded
  market sales; volume figures are counts of the same population.
  Neighborhood medians are printed with their sale counts, and no
  neighborhood rate is normalized by housing stock because a stock
  denominator at statistical-neighborhood level would itself be built
  from the current (post-change) parcel file.
- Direction of causality: no causal claim is made. The volume/price
  co-movement with permits is reported as agreement between two
  records, not as one causing the other.
- Category and definition changes: the D_CLASS_N hyphen variant was
  caught and merged (see audit). INSTRUMENT codes are stable
  two-letter Clerk and Recorder codes across the window (full counter
  in the audit output). The sales service's own coverage claim (2010)
  is wrong against its data (2015) and the brief says so.
  Neighborhood boundaries are the current published statistical
  layer, applied to the whole window as in the prior briefs.
- Time windows: sale years 2020-2026 with 2026 labeled partial
  everywhere it appears, including pooled totals. Movement periods
  are 2020-21 and 2024-25; partial-2026 sales are in NEITHER period.
  FIX-LOOP DEFECT (found independently by the builder's re-check and
  by the section 11 verifier): the first build's period mapping
  (SALE_YEAR >= 2024) silently folded partial-2026 sales into the
  period labeled "2024-25", moving every movement figure (citywide
  SFR +12.1 percent on the contaminated basis vs +11.2 percent true;
  Cheesman Park's change even flipped sign, +0.8 to -7.5). All
  movement figures in the final package are computed on calendar
  2024-2025 only, and the verifier's recomputed values match the
  final stats exactly (see the section 11 ledger).
- Joins: sales-to-parcel 98.54 percent of keyed rows; sales-to-
  neighborhood 98.3 percent of the dated market population. The 1,761
  unassigned dated market sales (parcels retired by splits/mergers)
  carry a lower median price ($401,000) than assigned sales and
  spread across all years of the window; at 1.7 percent of the
  population they cannot move a citywide figure. Citywide medians
  are computed on the full dated population, assigned or not (the
  first build computed the "citywide" period medians on the assigned
  subset only; corrected in the fix loop - adversarial finding B7).
- Small numbers: neighborhood level rankings require n >= 100 pooled
  single-family sales (the rule is printed in Finding 4, with its
  largest effect named: Sun Valley, 9 single-family sales, median
  $370,000, would otherwise rank fourth-lowest); movement rankings
  require n >= 30 in both periods (68 of 78 qualify). Kennedy (8
  market sales, pooled median $66,250,000 on airport-area land
  parcels) is excluded from every ranking and recorded in stats.json.
  The published CSV carries sfr_change_qualifies / small_n_flag
  columns so sub-threshold change percentages are flagged in the
  file itself, never silently dropped (adversarial finding B12).
  Sun Valley's 64 sales are reported as a count, never a rate.
- Official definitions: market-sale status uses the Clerk and
  Recorder's own instrument codes; statistical neighborhoods are the
  city's own geography; assessed and appraised values appear nowhere
  in any price figure.
- Layering admission test:
  ADMITTED - Parcels / spine neighborhood assignment. Claim the
  brief could not make without it: single-family medians and their
  2020-21 to 2024-25 movement for all 78 statistical neighborhoods
  on the same geography as the prior briefs (the ledger's own
  neighborhood field is a different geography).
  ADMITTED - Permit and demolition layers (via the spine). Claim:
  the teardown cycle priced end to end (70.8 percent of 3,297
  demolished parcels received a new-building permit; paired median
  buy $650,000, post-permit sale $2,299,525, median difference
  $1,635,000) - no single dataset contains both a parcel's
  demolition and its deeds.
  ADMITTED - Parcels layer's last-sale summary. Claim: the 99.85
  percent cross-product price agreement over 152,181 parcels that
  validates the join (the control above).
  ADMITTED (fix loop) - Neighborhood under-$500,000 shares by
  period, computed from the same assigned sales. Claim: the Housing
  Stability watch list (Bear Valley 81.2 to 52.1 percent; Capitol
  Hill 80.7 to 53.2; Harvey Park South 66.3 to 41.8; 75 qualifying
  neighborhoods), shipped as columns in data/neighborhood_sales.csv.
  CUT - Residential characteristics (price per square foot, year
  built of what sold). The file describes the building standing
  today, not the one that sold; after teardowns and remodels the
  per-square-foot series would silently change composition. Cut
  under the admission test and documented in sources.md.
  CUT - Buyer/seller concentration from GRANTOR/GRANTEE. Raw name
  strings (trusts, estates, variants) need a normalization pass the
  prep memo scopes as later work; no concentration claim is made.
- Censoring and effective windows (section 12.3): the snapshot's
  sales are substantially complete through 2026-08-31; September
  2026 records 207 sales against 1,099 in September 2025; October
  2026 holds 1 sale; one December 30, 2026 sale dated after the
  snapshot is excluded from dated figures (printed exclusion).
  Lifecycle buys are left-censored at 2015 (the ledger's first year)
  and by the market-sale definition; lifecycle exits are
  right-censored at the snapshot; the rebuilt share is itself
  right-censored (demolitions in the final 12 months: 460 parcels,
  46.1 percent rebuilt so far, vs 74.8 percent for earlier
  demolitions; 962 not-rebuilt parcels printed). All floors are
  printed with counts in Finding 5.
- Event-ordering near misses (section 12.2): the lifecycle's strict
  inequalities exclude, and Finding 5 now prints: 0 sales on a
  demolition date, 1 sale on a permit date, 77 sales between a
  parcel's demolition and its rebuild permit (counted as neither
  buy nor exit).
- Basis discipline (section 12.4): parcel rows, distinct deal
  records, permits, and parcels are labeled wherever they appear;
  the one place two bases meet (Finding 5's 70.8 percent parcel
  basis vs the October 15 brief's 60.0 percent address basis) prints
  both units and states the counts are not expected to agree.
  Multi-parcel price repetition is measured at the lifecycle's own
  exposure point: 7 of 611 paired parcels involve a multi-parcel
  deed; the single-parcel restriction (604 parcels) moves the
  median spread to $1,637,601, and both figures are printed.

## Section 11 independent verification (pass 3)

Verifier: code/verify_independent.py (separate implementation -
pyarrow column reads, dictionary accumulation, statistics-module
medians; recomputes from the RAW sales snapshot, not the cleaned
layers). Ledger: verification_results.json - 294 figures.

First pass against the builder's draft: **237 REPRODUCED / 53
CORRECTED / 4 CAVEATED.** The 53 corrected figures form four groups,
all fixed and closed by re-verification:

1. **Period definition (46 figures).** The verifier diagnosed that
   every "2024-25" figure reproduced exactly only if partial-2026
   sales were pooled into the period, and recomputed the true
   2024-25 values. The builder's own re-check found the same defect
   independently. After the fix, a mechanical closure check compared
   every checkable corrected value against the final stats.json and
   data/neighborhood_sales.csv: **47 of 47 match the verifier's
   recomputation exactly** (citywide SFR $595,000 / +11.2 percent;
   68 qualifying neighborhoods; every named neighborhood's median,
   change, and count; both Goldsmith bases). One residual basis
   difference, not an error: the citywide all-sales period medians -
   the verifier computed them on neighborhood-assigned sales
   ($538,000 / +9.8 percent); the package's stats.json now carries
   the all-population basis ($532,882.50 / +9.9 percent) with the
   population labeled in the file. The brief prints neither figure.
2. **Control join NaN keys (5 figures).** The verifier traced the
   control's checked population (claimed 157,644) to NaN-key
   matching and recomputed the clean control (152,181 / 99.85 /
   99.91 / 221 / 43.9). The fixed builder code reproduces those
   values exactly; they are the values now in stats.json, the
   audit, and the brief.
3. **Post-snapshot sales count (1 figure).** Claimed 2 sales dated
   after the snapshot; recomputed 1 (the second is dated October 13,
   before the snapshot). Brief and sources now tell the single
   correct story (see B10 disposition).
4. **Rankings restatement (1 composite figure).** The Finding 4
   ranking set under the true period definition - new top six
   (Southmoor Park, Belcaro, Cole, Windsor, Cory - Merrill,
   Marston) and FOUR decliners, not three. The final brief prints
   exactly this set.

The 4 CAVEATED figures: the $690,637.50 median printed truncated as
$690,637 (fixed to the standard rounding $690,638 - finding C2);
Sun Valley's 78 demolition permits and the October 15 brief's 60.0
percent follow rate (cross-package figures, not recomputable from
this package's parcel-basis sources; both are now cited in the
brief with their source and unit); and the City Council budget
dates (external calendar facts, outside the verifier's scope; the
October 19 date was dropped and October 26 is sourced in
sources.md item 9).

## Adversarial review dispositions (pass 4)

Full report: adversarial-review.md (29 findings: 3 blocking / 13
major / 11 minor / 2 nit; reviewed draft pinned by hash in that
file). Every finding was adjudicated from the full text. All 29 are
FIXED in the final package except where a disposition below says
otherwise; the section 12.7 three-part verdicts are in the report
itself and are adopted unless noted.

Blocking:
- **A1 (verification artifacts missing at review time).** TRUE when
  written - the review ran in parallel with the verification pass.
  Both artifacts now exist (this file; code/verify_independent.py;
  verification_results.json), and the brief's pointer is now true.
  The reviewer's stronger cure (a manifest existence check) is
  adopted as the freeze manifest at the end of this file.
- **A2 (partial-2026 labeling).** CORRECT. "(2026 partial)" now
  appears at Finding 3, Finding 4 (both paragraphs), the TL;DR, the
  hero subhead, the README lede, X posts 1 and 3, and the LinkedIn
  draft; the brief's assurance sentence now reads "2026 is labeled
  partial wherever it appears, including in pooled totals" - and is
  true of the final text.
- **A3 (Finding 3 dropped the 521 "Other" sales).** CORRECT. The
  521 sales (0.5 percent, median $1,010,000) are printed in
  Finding 3; the enumeration now sums to the stated population.

Major:
- **B1 ("gave back about a third").** CORRECT (the true figure is
  48.3 percent of the gain). Restated: "gave back about half of its
  2020-2022 gain from the peak ($70,000 of $145,000)".
- **B2 (permit events narrated as physical events).** CORRECT.
  Every surface now uses permit language ("carry a demolition
  permit", "received a new-building permit", "first sale after the
  rebuild permit"); Finding 5 states that the record shows permits,
  not construction completion; the lifecycle chart was relabeled
  and retitled to match.
- **B3 (rebuilt share right-censoring undisclosed).** CORRECT.
  Finding 5 and the Who can act bullet print the floor, the 962
  not-rebuilt count, and the exposure split (final-12-month
  demolitions 46.1 percent so far vs 74.8 percent earlier); the
  lifecycle chart footnote carries the 962 count.
- **B4 (Housing Stability lever pointed at a nonexistent
  measurement).** CORRECT. The measurement now exists: neighborhood
  under-$500,000 shares by period are computed, shipped as CSV
  columns (75 qualifying neighborhoods), and the lever names the
  three fastest fallers from that table.
- **B5 (Sun Valley passage: unsourced 78, dropped "residential"
  scope, ecological inference).** CORRECT on all three parts. The
  passage now cites the 78 to the October 15 brief with its unit,
  restores "residential" (also in Finding 1), and states the
  conclusion at aggregate level only.
- **B6 (hidden 100-sale filter on the extremes list).** CORRECT.
  The rule is printed in Finding 4 and its largest effect is named
  (Sun Valley, 9 sales, $370,000).
- **B7 ("citywide" medians computed on the assigned subset).**
  CORRECT. Citywide period and pooled medians are now computed on
  the full dated population and stats.json labels the population.
- **B8 (multi-parcel repetition unmeasured at the lifecycle).**
  CORRECT as a disclosure gap; now measured: 7 of 611 paired
  parcels involve a multi-parcel deed; the single-parcel
  restriction's spread ($1,637,601) is printed beside the headline.
- **B9 (hero curve falsified the median path).** CORRECT. The base
  art was regenerated: the drawn line now rises gently and runs
  long and flat at the higher level (rise-and-plateau, matching
  Finding 1). The composited figures were already accurate and are
  unchanged except the added "(2026 partial)".
- **B10 (three stories about the two post-September sales).**
  CORRECT. One story everywhere: 1 sale dated October 13, 2026
  (partial month, included), 1 sale dated December 30, 2026
  (after the snapshot, excluded from dated figures under a printed
  exclusion; 2026 dated count 8,728).
- **B11 (movement percentages without counts).** CORRECT. Every
  featured movement figure in Finding 4 now carries its two sale
  counts; X post 4 carries the smallest featured base.
- **B12 (CSV printed small-number figures unflagged).** CORRECT.
  The CSV carries sfr_change_qualifies and small_n_flag columns;
  the README's data note states the rule.
- **B13 ("refilled faster than the middle" inverted the band
  facts).** CORRECT. Finding 2's final sentence now states the
  measured version: the recovery is entirely a bottom-band
  recovery; the $250,000-$500,000 band has not recovered at all.

Minor and nits (all FIXED unless noted):
- C1: summary surfaces now say "the median difference between the
  two deeds", matching Finding 5.
- C2: $690,638 (standard rounding) in brief, chart, and notes.
- C3: the reception field's dirt (537 negative lags, 4 missing;
  denominator 105,581) is disclosed in What we used and sources.md.
- C4: deal arithmetic corrected everywhere (98,374 distinct
  reception numbers + 1 unnumbered = 98,375 deal records; 7,210
  extra parcel rows), in brief, sources, audit, and stats.
- C5: (a) the October 19 date is dropped; October 26 is sourced
  (sources.md item 9). (b) "guess at the 50-plus instrument codes"
  softened to recovering the codes "from a second file's value
  labels". (c) the CPD bullet carries the parcel basis, the floor,
  and the median-difference wording.
- C6 (package edited mid-review): process finding, accepted. The
  condominium-variant fix landed during the review window; the
  final package is frozen with the hash manifest below, and the
  closure check ran against the frozen stats.
- C7: the 98.54 percent join rate is now COMPUTED in analyze.py
  (it was a hard-coded literal) and the brief names its population
  ("sales rows carrying a schedule number").
- C8: boundary counts (0 / 1 / 77) and buy-recency (median gap 7.6
  months; 91.2 percent within 36 months; within-36-month spread
  $1,649,000 over 557 parcels) are printed in Finding 5 and
  stats.json.
- C9: the demolition window reads "January 1, 2020 to October 12,
  2026" in the TL;DR, Finding 5, and Who can act.
- C10: the LinkedIn draft uses the snapshot wording and "(2026
  partial)"; the join phrase no longer overstates coverage.
- C11: "collapsed" heading replaced ("fell sharply"); "settled"
  removed from the TL;DR. The title's "actually" is KEPT - the one
  disposition not adopted in full; the reviewer flagged it as
  Alex's voice call rather than prescribing, and it is recorded
  here for the morning QA read.
- D1: the band-rounding note is in Methods.
- D2: the cross-check sentence is softened to two series from
  different records peaking in the same year, and the parcels
  control (99.85 percent over 152,181 parcels) is printed in What
  we used.

Section 11.3 exception flags (for Alex): the Who can act section
names the Denver Assessor's Office, Denver City Council, the
Department of Housing Stability, and Community Planning and
Development; no individual official is named; no finding alleges
error or wrongdoing by any of them. First use of a new dataset
family (assessor sales, parcels, characteristics) is itself a
standing flag.

## Freeze manifest (adversarial finding C6 / A1 cure)

Hashes of the frozen package files are recorded at the end of the
build in the delivery report; any later edit restarts the affected
checks. Files: brief-draft.md, stats.json, verification.md,
reviewer-notes.md, sources.md, README.md, social-drafts.md,
adversarial-review.md, verification_results.json,
data/neighborhood_sales.csv, code/audit.py, code/analyze.py,
code/charts.py, code/compose_hero.py, code/verify_independent.py,
charts/hero.png, charts/yearly_cycle.png,
charts/neighborhood_median_map.png, charts/neighborhood_change.png,
charts/lifecycle.png.
