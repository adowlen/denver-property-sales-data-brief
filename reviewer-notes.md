# Reviewer notes - Denver real property sales brief (assessor keystone)

## Claim most likely challenged 1: the market-sale definition carries the whole brief

There is no qualified-sale flag in the public transfers ledger, so
every price figure rests on the derived filter (warranty or special
warranty deed, price above zero). A critic can correctly note both
error directions: some WD transfers are related-party, and some quit
claims are genuine sales. Why the definition is defensible: it is the
filter the warehouse Phase 1 build applied, it reconciles exactly
with two independent prior measurements (105,585 market sales 2020+;
2024 median $540,000 on n=13,100), and the brief states the definition
and its error directions wherever the population is introduced. The
alternative (all transfers with a price) would mix estate and
intra-family transfers into price medians at scale - 56,031 rows
record zero or no price, and the QC class alone is 55,435 rows.

## Claim most likely challenged 2: medians describe what sold, not price movement

A real-estate reader will want a repeat-sales index and will note
that mix shift moves medians. Conceded in the brief itself, twice:
the "What we used" section defines every median as the mix of
properties that changed hands, and "What this might mean" names
composition and nominal dollars as the strongest alternative
explanation and quantifies the direction (real-terms flattening).
The Goldsmith case (+115.8 percent all-sales vs +20.3 percent
single-family) is printed in Finding 4 as the worked example, and
neighborhood movement is reported on the single-family basis for
exactly this reason. A repeat-sales index is buildable from this
ledger and is the natural follow-up brief.

## Claim most likely challenged 3: the teardown spread will be quoted as profit

The paired-parcel gross spread ($1,635,000 median) is the figure most
likely to be lifted out of context. Mitigations in the brief: it is
labeled gross at every appearance, the sentence itself excludes
demolition, construction, holding, and financing costs, and the
interpretation section prints the wider unpaired medians ($690,638
purchase; $1,875,000 post-permit sale) next to it so the selection
range is visible. If Alex wants a harder guard, the social drafts can
drop the spread entirely; the LinkedIn and X drafts currently carry
it with the "before construction and financing costs" rider attached.

## Claim most likely challenged 4: 70.8 percent rebuilt vs the Oct 15 brief's 60.0 percent

Two different measurements of related things: parcel-record basis
(this brief: the parcel's own record shows a demolition and a later
new-building permit) vs street-address pairing (Oct 15). The brief
states both units and says the counts are not expected to agree. A
checker who conflates them will manufacture a contradiction; the
wording in Finding 5 is written to pre-empt that, and QA should
confirm it reads that way.

## Surprises found while building

- The low end of the market refilled faster than the middle after
  2022: the under-$250,000 band recovered from 11.8 percent of sales
  (2022) to 21.2 percent (2025), above its 2020 share, while the
  $250,000-$500,000 band kept shrinking (37.6 to 26.1 percent). The
  brief reports the combined under-$500,000 share; the band detail is
  in stats.json if Alex wants it promoted.
- Sales volume and new-building permits peaked in the same year
  (2021) and fell by nearly identical shares to 2025 (-41.9 and
  -44.1 percent), despite coming from different offices and records.
- Kennedy's pooled all-sales median is $66,250,000 on 8 sales
  (airport-area land parcels). It is excluded from every ranking
  under the small-numbers rule and recorded in stats.json; it is the
  kind of artifact that would have headlined a careless version of
  this brief.
- The assessor table's own loading lag is the binding completeness
  constraint, not deed recording: deeds record a median of 3 days
  after sale, yet the October 15 snapshot holds only 207
  September-dated sales against 1,099 in September 2025.

## Checks that could not be completed

- Buyer/seller concentration (repeat investors, LLC share): GRANTOR
  and GRANTEE are raw name strings with trusts, estates, and spelling
  variants; a defensible concentration claim needs the name
  normalization pass the prep memo flags as v2 work. Not attempted.
- Price per square foot: cut under the layering admission test
  (characteristics describe the building standing today, not the one
  that sold). Documented in sources.md and verification.md.
- Whether unassigned sales (1,762, parcels retired by splits and
  mergers) differ systematically by neighborhood: by construction
  they cannot be assigned one; their price distribution was compared
  citywide only (see verification.md).
- Arm's-length validation of individual WD transfers: no data source
  in the ledger distinguishes related-party warranty deeds; the
  two-direction error statement in the brief is the honest bound.

## Agency flag (standards sections 6 and 11.3)

The "Who can act" section names the Denver Assessor's Office (a
documentation ask: publish the deed-instrument codebook and a
market-sale indicator), Denver City Council, the Department of
Housing Stability, and Community Planning and Development. No finding
claims error or wrongdoing by any of them; every statement is a count
of the bodies' own published records, and the Assessor's Office item
is framed as a documentation improvement to a file the office already
publishes. First use of a new dataset family (assessor sales, parcels,
characteristics) is itself a section 11.3 exception flag; this brief
is that first use.
