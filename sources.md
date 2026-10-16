# Sources - Denver real property sales brief (assessor keystone)

All data is City and County of Denver open data (ArcGIS Hub org
zdB7qR0BtYrg0Xpl, services1.arcgis.com), snapshotted 2026-10-15 into
the Machine Readable Denver warehouse and read from those snapshots.
The brief's population: transfers with SALE_YEAR 2020-2026 recorded as
market sales (definition in source 2). Sale dates run 2020-01-01
through the snapshot; the snapshot's sales are substantially complete
through 2026-08-31 (recording lag, source 7).

1. Real Property Sales and Transfers - ODC_real_property_sales_and_
   transfers, FeatureServer table 51. The assessor / Clerk and
   Recorder transfers ledger: 313,361 rows, SALE_YEAR 2015-2026 (the
   catalog description claims 2010 to present; the earliest sale year
   in the data is 2015). Service last edited 2026-10-15T13:24:24Z;
   snapshot file snapshots/2026-10-15/sales.parquet (sha256
   747d31b7616e8b34...). Fields used: PARID, RECEPTION_NUM, INSTRUMENT,
   SALE_YEAR, SALE_MONTHDAY (composed into the sale date), RECEPTION_
   DATE (lag analysis only), SALE_PRICE, D_CLASS_N, CLASS.
2. Market-sale definition (derived): INSTRUMENT in (WD, SW) and
   SALE_PRICE > 0. WD is a warranty deed, SW a special warranty deed -
   the two deed types that behave like arm's-length sales. 56,031 rows
   (17.9 percent) record a price of zero or null and are excluded from
   every price figure; the full INSTRUMENT counter (50-plus codes:
   WD 158,260; QC 55,435; SW 55,257; PR 9,959; PS 9,385; DC 6,605;
   and a long tail) is recorded in verification.md. The filter is
   imperfect in both directions (some WD transfers are related-party;
   occasional QC deeds are genuine sales) and the brief states this.
   For 2020 and later the filter gives 105,585 parcel rows over
   98,374 distinct RECEPTION_NUM values plus one row with none
   (98,375 deal records; one transaction can span several parcels;
   the source repeats the transaction price on each parcel row, and
   prices are never summed in this package).
3. Parcels - ODC_PROP_PARCELS_A, FeatureServer layer 245: 240,441
   current parcels keyed by SCHEDNUM (13-character zero-padded
   schedule number). Service last edited 2026-10-15T11:13:12Z.
   Sales rows join by normalized schedule number (sales PARID read as
   a number, zero-padded to 13 characters): 98.54 percent of sales
   rows key to a parcel that exists today. The parcels layer also
   carries the assessor's own last-transfer summary per parcel
   (RECEPTION_NUM, SALE_PRICE, SALE_YEAR), used as the built-in
   control in verification.md.
4. Statistical neighborhoods - the city's 78 statistical neighborhood
   polygons, assigned to parcels in the warehouse spine by spatial
   join of parcel geometry (240,335 of 240,441 parcels assigned).
   The sales ledger's own NBHD_1_CN field is the assessor's
   neighborhood geography, a different set of boundaries, and is not
   used anywhere in this brief.
5. Residential construction permits and demolition permits - the same
   warehouse layers used by the 2026-10-15 net housing change brief
   (ODC_DEV_RESIDENTIALCONSTPERMIT_P layer 316; ODC_DEV_DEMOLITION-
   PERMIT_P layer 318), joined to parcels in the warehouse spine
   (parcel_spine_v6). Figures reused as cross-checks recompute exactly
   from these layers: 11,585 new-building permits and 3,837 demolition
   permits issued 2020-01-01 to 2026-10-12. Finding 5's lifecycle uses
   the spine's per-parcel first demolition date, first new-building
   permit date, and demolished-then-rebuilt flag (surviving-parcel
   basis).
6. Real Property Residential Characteristics - ODC_real_property_
   residential_characteristics, FeatureServer table 50: 212,850 rows
   (building cards). Joined for coverage checks only (93.0 percent of
   market sales 2020+ key to a parcel with a characteristics record).
   CUT under the layering admission test: no price-per-square-foot
   figure is published, because the file describes the building
   standing today, not the one that sold; after a teardown or remodel
   those are different buildings.
7. Recording completeness (derived): deeds are recorded a median of
   3 days after sale (96.7 percent within 30 days, over the 105,581
   market sales carrying a reception date; 537 deeds show a reception
   date before their sale date), but the published table loads in
   batches. Sales dated September 2026 number 207 in the snapshot
   against 1,099 dated September 2025, and October 2026 holds 1 sale
   (dated October 13). One further sale carries a December 30, 2026
   sale date - after the October 15 snapshot - and is excluded from
   every dated figure under a printed exclusion (dated analysis
   population 105,584; recorded in stats.json reconciliation). The
   brief treats sale dates through 2026-08-31 as substantially
   complete and labels 2026 partial.
8. Prior Machine Readable briefs layered here: Denver net housing
   change (2026-10-15, permits and demolitions) and the Washington
   Park teardown pilot readout v2.1 (2026-10-15, warehouse product,
   unpublished), whose Washington Park lifecycle figures serve as a
   cross-package control in verification.md.
9. Denver City Council budget calendar (denvergov.org), for the one
   calendar fact cited in Who can act: the public hearing on the
   city budget falls on October 26, 2026.
