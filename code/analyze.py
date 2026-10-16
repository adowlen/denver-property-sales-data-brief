#!/usr/bin/env python3
"""Analysis for the Denver assessor sales keystone brief (2026-10-16).

Reads the warehouse cleaned layers (snapshotted 2026-10-15) and writes
stats.json plus data/*.csv. Market sale = INSTRUMENT in (WD, SW) and
SALE_PRICE > 0 (the cleaned layer's is_market_sale flag). Sale dates are
composed from SALE_YEAR + SALE_MONTHDAY in the layer build, never from
RECEPTION_DATE. Prices are never summed across parcels: multi-parcel
transactions repeat one price per parcel row in the source.

Run: python3 code/analyze.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

STACK = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files/stack/denver")
PKG = Path(__file__).resolve().parent.parent
WIN0, WIN1 = pd.Timestamp("2020-01-01"), pd.Timestamp("2026-10-12")
PARTIAL_CUTOFF = pd.Timestamp("2026-08-31")  # last substantially complete sale month

sales = pd.read_parquet(STACK / "layers/sales_clean.parquet")
parcels = pd.read_parquet(STACK / "layers/parcels_clean.parquet")
chars = pd.read_parquet(STACK / "layers/characteristics_clean.parquet")
spine = pd.read_parquet(STACK / "joins/parcel_spine_v6.parquet")
permits = pd.read_parquet(STACK / "layers/permits_clean.parquet")
demos = pd.read_parquet(STACK / "layers/demolitions_clean.parquet")

mkt = sales[sales["is_market_sale"]].copy()
mkt["sale_date"] = pd.to_datetime(mkt["sale_date"])
mkt["tx_size"] = mkt.groupby("RECEPTION_NUM")["PARID"].transform("size")
m_all = mkt[(mkt["SALE_YEAR"] >= 2020)].copy()  # 105,585 reconciliation population
assert len(m_all) == 105585
# Section 12.6 visible exclusion (adversarial review B10): one market-sale
# row carries a sale date after the snapshot date (2026-12-30 in a
# 2026-10-15 snapshot; a forward-dated recording artifact). It stays in
# the recorded population count and is excluded from every dated figure.
SNAPSHOT_DATE = pd.Timestamp("2026-10-15")
N_FUTURE_DATED = int((m_all["sale_date"] > SNAPSHOT_DATE).sum())
assert N_FUTURE_DATED == 1
m = m_all[m_all["sale_date"] <= SNAPSHOT_DATE].copy()
mkt = mkt[mkt["sale_date"] <= SNAPSHOT_DATE].copy()
nb = spine[["schednum", "neighborhood"]]
m = m.merge(nb, on="schednum", how="left")

stats = {"meta": {
    "brief": "Denver real property sales (assessor keystone)",
    "snapshot_date": "2026-10-15",
    "sources": "City and County of Denver open data via the Machine Readable Denver warehouse "
               "(snapshots of 2026-10-15; sales service last edited 2026-10-15T13:24:24Z, "
               "parcels 2026-10-15T11:13:12Z, characteristics 2026-10-15T09:48:04Z)",
    "population": "Market sales: INSTRUMENT in (WD, SW) and SALE_PRICE > 0, SALE_YEAR 2020-2026. "
                  "Unit of observation is the parcel row; distinct recorded transactions are "
                  "counted by RECEPTION_NUM where the deal is the unit.",
    "price_basis": "Nominal dollars, as recorded. Not inflation-adjusted.",
}}

# ---------- reconciliation ----------
y2024 = m[m["SALE_YEAR"] == 2024]
stats["reconciliation"] = {
    "sales_table_rows_all_years": int(len(sales)),
    "zero_or_null_price_rows_all_years": int((sales["SALE_PRICE"].isna() | (sales["SALE_PRICE"] == 0)).sum()),
    "market_sales_2020_plus_rows": int(len(m_all)),
    "future_dated_rows_excluded_from_dated_figures": N_FUTURE_DATED,
    "analysis_population_rows": int(len(m)),
    "distinct_reception_numbers_2020_plus": int(m["RECEPTION_NUM"].nunique()),
    "market_rows_with_no_reception_number": int(m["RECEPTION_NUM"].isna().sum()),
    "median_2024": float(y2024["SALE_PRICE"].median()),
    "n_2024": int(len(y2024)),
    "median_2024_distinct_transactions": float(
        m.drop_duplicates("RECEPTION_NUM").query("SALE_YEAR == 2024")["SALE_PRICE"].median()),
}

# ---------- yearly ----------
rows = []
for y in range(2020, 2027):
    sub = m[m["SALE_YEAR"] == y]
    rows.append({
        "year": y, "sales": int(len(sub)),
        "median_price": float(sub["SALE_PRICE"].median()),
        "p25": float(sub["SALE_PRICE"].quantile(0.25)),
        "p75": float(sub["SALE_PRICE"].quantile(0.75)),
        "partial": y == 2026,
    })
stats["yearly"] = rows
m_complete = m[m["sale_date"] <= PARTIAL_CUTOFF]
y26 = m[m["SALE_YEAR"] == 2026]
y26_complete = y26[y26["sale_date"] <= PARTIAL_CUTOFF]
stats["year_2026_detail"] = {
    "rows_all": int(len(y26)),
    "rows_through_aug_31": int(len(y26_complete)),
    "median_through_aug_31": float(y26_complete["SALE_PRICE"].median()),
    "rows_sep_2026": int(((y26["sale_date"] >= "2026-09-01") & (y26["sale_date"] <= "2026-09-30")).sum()),
    "rows_october_2026_partial": int(((y26["sale_date"] >= "2026-10-01") & (y26["sale_date"] <= SNAPSHOT_DATE)).sum()),
    "future_dated_rows_excluded": N_FUTURE_DATED,
    "sep_2025_rows": int(((m["sale_date"] >= "2025-09-01") & (m["sale_date"] <= "2025-09-30")).sum()),
}
# reception lag (sale date -> recording date), market sales 2020+
mm = m.copy()
mm["rec"] = pd.to_datetime(mm["RECEPTION_DATE"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
mm["lag_days"] = (mm["rec"] - mm["sale_date"]).dt.days
lag = mm["lag_days"].dropna()
stats["recording_lag"] = {
    "median_days": float(lag.median()),
    "p25_days": float(lag.quantile(0.25)), "p75_days": float(lag.quantile(0.75)),
    "share_within_30_days_pct": round(float((lag.between(0, 30)).mean() * 100), 1),
    "negative_lag_rows": int((lag < 0).sum()),
    "missing_reception_date_rows": int(mm["lag_days"].isna().sum()),
}

# ---------- price distribution ----------
bands = [0, 250_000, 500_000, 750_000, 1_000_000, 1_500_000, np.inf]
labels = ["<=250k", "250-500k", "500-750k", "750k-1M", "1-1.5M", ">1.5M"]
dist = {}
for y in [2020, 2021, 2022, 2023, 2024, 2025]:
    sub = m[m["SALE_YEAR"] == y]
    b = pd.cut(sub["SALE_PRICE"], bands, labels=labels)
    dist[str(y)] = {k: round(float(v) * 100, 1) for k, v in b.value_counts(normalize=True).sort_index().items()}
    dist[str(y)]["share_le_500k_pct"] = round(float((sub["SALE_PRICE"] <= 500_000).mean() * 100), 1)
stats["price_bands_pct"] = dist

# ---------- composition (property class of what sold) ----------
def group_of(d):
    if not isinstance(d, str):
        return "Other / unclassified"
    if d.startswith("SFR"):
        return "Single-family residential"
    if d in ("RESIDENTIAL-CONDOMINIUM", "RESIDENTIAL CONDOMINIUM"):  # hyphen variant exists in source
        return "Condominium"
    if d == "RESIDENTIAL-ROWHOUSE":
        return "Rowhouse"
    if d in ("RESIDENTIAL-DUPLEX", "RESIDENTIAL-TRIPLEX", "RESIDENTIAL-4 TO 8 UNITS"):
        return "Duplex / triplex / 4-8 units"
    if d in ("RESIDENTIAL-APARTMENT", "RESIDENTIAL-MULTI UNIT APTS"):
        return "Apartment (larger multifamily)"
    if d.startswith("VACANT LAND"):
        return "Vacant land"
    if d.startswith("COMMERCIAL") or d.startswith("INDUSTRIAL"):
        return "Commercial / industrial"
    return "Other / unclassified"

m["group"] = m["D_CLASS_N"].map(group_of)
comp = (m.groupby("group")["SALE_PRICE"].agg(["count", "median"])
        .assign(share_pct=lambda d: (d["count"] / len(m) * 100).round(1))
        .sort_values("count", ascending=False))
assert int(comp["count"].sum()) == len(m)
stats["composition"] = {g: {"sales": int(r["count"]), "share_pct": float(r["share_pct"]),
                            "median_price": float(r["median"])} for g, r in comp.iterrows()}

# ---------- neighborhoods ----------
def period_of(y):
    # Period 2 is 2024-2025 ONLY. 2026 is a partial year and belongs to
    # neither comparison period (a prior version silently folded 2026
    # into "2024-25"; caught in the fix loop - see verification.md).
    return "2020-21" if y <= 2021 else ("2024-25" if y in (2024, 2025) else "other")

m["period"] = m["SALE_YEAR"].map(period_of)
assigned = m[m["neighborhood"].notna()]
pooled_all = assigned.groupby("neighborhood")["SALE_PRICE"].agg(["count", "median"])
sfr = assigned[assigned["group"] == "Single-family residential"]
pooled_sfr = sfr.groupby("neighborhood")["SALE_PRICE"].agg(["count", "median"])
nb_rows = []
for name in sorted(set(pooled_all.index) | set(pooled_sfr.index)):
    row = {"neighborhood": name}
    if name in pooled_all.index:
        row["sales_all"] = int(pooled_all.loc[name, "count"])
        row["median_all"] = float(pooled_all.loc[name, "median"])
    if name in pooled_sfr.index:
        row["sales_sfr"] = int(pooled_sfr.loc[name, "count"])
        row["median_sfr"] = float(pooled_sfr.loc[name, "median"])
    for basis, frame in [("all", assigned), ("sfr", sfr)]:
        for per in ["2020-21", "2024-25"]:
            sub = frame[(frame["neighborhood"] == name) & (frame["period"] == per)]
            row[f"n_{basis}_{per}"] = int(len(sub))
            row[f"median_{basis}_{per}"] = float(sub["SALE_PRICE"].median()) if len(sub) else None
    nb_rows.append(row)
nbdf = pd.DataFrame(nb_rows)
for basis in ["all", "sfr"]:
    a, b = f"median_{basis}_2020-21", f"median_{basis}_2024-25"
    nbdf[f"change_{basis}_pct"] = (nbdf[b] / nbdf[a] - 1) * 100
# under-$500,000 share by neighborhood and period (all-sales basis) - the
# measurement the Housing Stability lever points to (adversarial review B4)
le = assigned.assign(le500=assigned["SALE_PRICE"] <= 500_000)
le_share = le[le["period"].isin(["2020-21", "2024-25"])].groupby(
    ["neighborhood", "period"])["le500"].mean().unstack() * 100
nbdf = nbdf.set_index("neighborhood")
nbdf["share_le500_2020_21_pct"] = le_share["2020-21"].round(1)
nbdf["share_le500_2024_25_pct"] = le_share["2024-25"].round(1)
nbdf["share_le500_change_pts"] = (nbdf["share_le500_2024_25_pct"] - nbdf["share_le500_2020_21_pct"]).round(1)
# eligibility flags printed IN the table (adversarial review B12): change
# percentages below the threshold are flagged, never silently dropped
nbdf["sfr_change_qualifies"] = (nbdf["n_sfr_2020-21"] >= 30) & (nbdf["n_sfr_2024-25"] >= 30)
nbdf["share_le500_qualifies"] = (nbdf["n_all_2020-21"] >= 30) & (nbdf["n_all_2024-25"] >= 30)
nbdf["small_n_flag"] = ~nbdf["sfr_change_qualifies"]
nbdf = nbdf.reset_index()
nbdf.to_csv(PKG / "data/neighborhood_sales.csv", index=False)
le_elig = nbdf[nbdf["share_le500_qualifies"]].sort_values("share_le500_change_pts")
stats["neighborhood_under_500k_share"] = {
    "basis": "all market sales assigned a neighborhood; share at or under $500,000",
    "neighborhoods_qualifying": int(len(le_elig)),
    "largest_decreases": [
        {"neighborhood": r["neighborhood"], "share_2020_21_pct": float(r["share_le500_2020_21_pct"]),
         "share_2024_25_pct": float(r["share_le500_2024_25_pct"]),
         "change_pts": float(r["share_le500_change_pts"]),
         "n_2020_21": int(r["n_all_2020-21"]), "n_2024_25": int(r["n_all_2024-25"])}
        for _, r in le_elig.head(5).iterrows()],
}
stats["citywide_pooled"] = {
    "population": "all market sales in the analysis population (not only neighborhood-assigned)",
    "median_all_2020_plus": float(m["SALE_PRICE"].median()),
    "median_sfr_2020_plus": float(m[m["group"] == "Single-family residential"]["SALE_PRICE"].median()),
    "sales_with_neighborhood": int(len(assigned)),
    "sales_without_neighborhood": int(len(m) - len(assigned)),
}
elig = nbdf[(nbdf["n_sfr_2020-21"] >= 30) & (nbdf["n_sfr_2024-25"] >= 30)].sort_values("change_sfr_pct")
sfr_all = m[m["group"] == "Single-family residential"]  # all-population basis (review B7)
stats["neighborhood_change_sfr"] = {
    "neighborhoods_qualifying": int(len(elig)),
    "citywide_basis": "all single-family market sales, assigned or not",
    "citywide_sfr_median_2020_21": float(sfr_all[sfr_all["period"] == "2020-21"]["SALE_PRICE"].median()),
    "citywide_sfr_median_2024_25": float(sfr_all[sfr_all["period"] == "2024-25"]["SALE_PRICE"].median()),
    "largest_increases": [
        {"neighborhood": r["neighborhood"], "median_2020_21": r["median_sfr_2020-21"],
         "median_2024_25": r["median_sfr_2024-25"], "change_pct": round(float(r["change_sfr_pct"]), 1),
         "n_2020_21": int(r["n_sfr_2020-21"]), "n_2024_25": int(r["n_sfr_2024-25"])}
        for _, r in elig.tail(6).iloc[::-1].iterrows()],
    "smallest_changes": [
        {"neighborhood": r["neighborhood"], "median_2020_21": r["median_sfr_2020-21"],
         "median_2024_25": r["median_sfr_2024-25"], "change_pct": round(float(r["change_sfr_pct"]), 1),
         "n_2020_21": int(r["n_sfr_2020-21"]), "n_2024_25": int(r["n_sfr_2024-25"])}
        for _, r in elig.head(6).iterrows()],
}
top_sfr = nbdf[nbdf["sales_sfr"] >= 100].sort_values("median_sfr", ascending=False)
stats["neighborhood_sfr_extremes"] = {
    "highest": [{"neighborhood": r["neighborhood"], "median_sfr": float(r["median_sfr"]),
                 "sales_sfr": int(r["sales_sfr"])} for _, r in top_sfr.head(5).iterrows()],
    "lowest": [{"neighborhood": r["neighborhood"], "median_sfr": float(r["median_sfr"]),
                "sales_sfr": int(r["sales_sfr"])} for _, r in top_sfr.tail(5).iloc[::-1].iterrows()],
}

stats["citywide_period_medians"] = {
    "population": "all market sales in the analysis population (not only neighborhood-assigned)",
    "all_sales": {
        "median_2020_21": float(m[m["period"] == "2020-21"]["SALE_PRICE"].median()),
        "median_2024_25": float(m[m["period"] == "2024-25"]["SALE_PRICE"].median()),
    },
    "sfr": {
        "median_2020_21": float(sfr_all[sfr_all["period"] == "2020-21"]["SALE_PRICE"].median()),
        "median_2024_25": float(sfr_all[sfr_all["period"] == "2024-25"]["SALE_PRICE"].median()),
    },
}
stats["citywide_period_medians"]["all_sales"]["change_pct"] = round(
    (stats["citywide_period_medians"]["all_sales"]["median_2024_25"]
     / stats["citywide_period_medians"]["all_sales"]["median_2020_21"] - 1) * 100, 1)
stats["citywide_period_medians"]["sfr"]["change_pct"] = round(
    (stats["citywide_period_medians"]["sfr"]["median_2024_25"]
     / stats["citywide_period_medians"]["sfr"]["median_2020_21"] - 1) * 100, 1)
gs = nbdf[nbdf["neighborhood"] == "Goldsmith"].iloc[0]
stats["goldsmith_composition_case"] = {
    "all_sales_median_2020_21": float(gs["median_all_2020-21"]),
    "all_sales_median_2024_25": float(gs["median_all_2024-25"]),
    "all_sales_change_pct": round(float(gs["change_all_pct"]), 1),
    "sfr_median_2020_21": float(gs["median_sfr_2020-21"]),
    "sfr_median_2024_25": float(gs["median_sfr_2024-25"]),
    "sfr_change_pct": round(float(gs["change_sfr_pct"]), 1),
    "note": "All-sales median swings +115.8% on a change in what sold (low-priced condos dominated "
            "2020-21 sales); the single-family median for the same periods moves +20.3%. The "
            "brief's neighborhood movement finding is therefore computed on the single-family basis.",
}
kn = nbdf[nbdf["neighborhood"] == "Kennedy"].iloc[0]
stats["kennedy_small_n"] = {"market_sales_2020_plus": int(kn["sales_all"]),
                            "median_all": float(kn["median_all"]),
                            "note": "Eight recorded market sales in 2020+ (airport-area land parcels); "
                                    "excluded from neighborhood rankings under the small-numbers rule."}

# ---------- teardown lifecycle (parcel basis, surviving parcels) ----------
sp = spine.copy()
for c in ["first_demolition_date", "first_new_building_permit_date"]:
    sp[c] = pd.to_datetime(sp[c])
sales_by_parcel = {k: g.sort_values("sale_date") for k, g in mkt.groupby("schednum")}


def lifecycle(frame):
    d = frame[(frame["first_demolition_date"] >= WIN0) & (frame["first_demolition_date"] <= WIN1)]
    reb = d[d["demolished_then_rebuilt"] == True]  # noqa: E712
    buys, exits, paired = [], [], []
    bnd = {"on_demolition_date": 0, "on_permit_date": 0, "between_demolition_and_permit": 0}
    for _, row in reb.iterrows():
        g = sales_by_parcel.get(row["schednum"])
        if g is None:
            continue
        dd = row["first_demolition_date"]
        pd_ = row["first_new_building_permit_date"]
        # Section 12.2 near misses for the strict event-ordering definitions
        bnd["on_demolition_date"] += int((g["sale_date"] == dd).sum())
        if pd.notna(pd_):
            bnd["on_permit_date"] += int((g["sale_date"] == pd_).sum())
            bnd["between_demolition_and_permit"] += int(
                ((g["sale_date"] > dd) & (g["sale_date"] < pd_)).sum())
        pre = g[g["sale_date"] < dd]
        post = g[g["sale_date"] > pd_] if pd.notna(pd_) else g.iloc[0:0]
        b = pre.iloc[-1] if len(pre) else None
        e = post.iloc[0] if len(post) else None
        if b is not None:
            buys.append(b)
        if e is not None:
            exits.append(e)
        if b is not None and e is not None:
            paired.append({"buy": b["SALE_PRICE"], "sell": e["SALE_PRICE"],
                           "spread": e["SALE_PRICE"] - b["SALE_PRICE"],
                           "months": (e["sale_date"] - b["sale_date"]).days / 30.4375,
                           "buy_group": group_of(b["D_CLASS_N"]),
                           "buy_tx_size": int(b["tx_size"]), "sell_tx_size": int(e["tx_size"]),
                           "buy_to_demolition_months": (dd - b["sale_date"]).days / 30.4375})
    pa = pd.DataFrame(paired)
    # Section 12.3 censoring exposure for the rebuilt share itself (review B3)
    recent_cut = WIN1 - pd.DateOffset(months=12)
    recent = d[d["first_demolition_date"] > recent_cut]
    earlier = d[d["first_demolition_date"] <= recent_cut]
    out = {
        "parcels_demolished_in_window": int(len(d)),
        "rebuilt_parcels": int(len(reb)),
        "rebuilt_share_pct": round(len(reb) / len(d) * 100, 1),
        "not_rebuilt_parcels": int(len(d) - len(reb)),
        "rebuilt_share_censoring": {
            "demolitions_final_12_months": int(len(recent)),
            "rebuilt_share_final_12_months_pct": round(
                float(recent["demolished_then_rebuilt"].mean() * 100), 1) if len(recent) else None,
            "demolitions_earlier": int(len(earlier)),
            "rebuilt_share_earlier_pct": round(
                float(earlier["demolished_then_rebuilt"].mean() * 100), 1) if len(earlier) else None,
        },
        "boundary_sales_section_12_2": bnd,
        "rebuilt_with_pre_demo_market_buy": int(len(buys)),
        "median_pre_demo_buy": float(pd.Series([b["SALE_PRICE"] for b in buys]).median()) if buys else None,
        "rebuilt_with_post_permit_sale": int(len(exits)),
        "median_first_post_permit_sale": float(pd.Series([e["SALE_PRICE"] for e in exits]).median()) if exits else None,
        "paired_parcels": int(len(pa)),
    }
    if len(pa):
        single = pa[(pa["buy_tx_size"] == 1) & (pa["sell_tx_size"] == 1)]
        w36 = pa[pa["buy_to_demolition_months"] <= 36]
        out.update({
            "paired_median_buy": float(pa["buy"].median()),
            "paired_median_sell": float(pa["sell"].median()),
            "paired_median_gross_spread": float(pa["spread"].median()),
            "paired_median_deed_to_deed_months": round(float(pa["months"].median()), 1),
            "paired_buy_composition": {k: int(v) for k, v in pa["buy_group"].value_counts().items()},
            "paired_multi_parcel_deeds": int(((pa["buy_tx_size"] > 1) | (pa["sell_tx_size"] > 1)).sum()),
            "paired_single_parcel_transactions": {
                "parcels": int(len(single)),
                "median_buy": float(single["buy"].median()),
                "median_sell": float(single["sell"].median()),
                "median_gross_spread": float(single["spread"].median()),
                "median_deed_to_deed_months": round(float(single["months"].median()), 1),
            },
            "buy_recency": {
                "median_months_buy_to_demolition": round(float(pa["buy_to_demolition_months"].median()), 1),
                "share_bought_within_36_months_pct": round(
                    float((pa["buy_to_demolition_months"] <= 36).mean() * 100), 1),
            },
            "paired_buy_within_36_months": {
                "parcels": int(len(w36)),
                "median_buy": float(w36["buy"].median()),
                "median_sell": float(w36["sell"].median()),
                "median_gross_spread": float(w36["spread"].median()),
                "median_deed_to_deed_months": round(float(w36["months"].median()), 1),
            },
        })
    return out


stats["lifecycle_citywide"] = lifecycle(sp)
stats["lifecycle_washington_park_control"] = lifecycle(sp[sp["neighborhood"] == "Washington Park"])
stats["lifecycle_censoring_note"] = (
    "Buys are observable only from 2015 (the sales table's first year) and only when the purchase "
    "was itself a market sale; exits are observable only if the rebuilt parcel sold again before "
    "the 2026-10-15 snapshot. Both shares are floors. The rebuilt share is also right-censored: "
    "demolitions in the final 12 months of the window have had under a year to draw a permit "
    "(see rebuilt_share_censoring). One market-sale row with a sale date after the snapshot "
    "(2026-12-30) is excluded from every dated figure (reconciliation).")

# ---------- cross-layer: permit volumes (Oct 15 brief's layers) ----------
per = permits.copy()
per["date"] = pd.to_datetime(per["date"])
nb_perm = per[(per["is_new_building"]) & (per["active"]) &
              (per["date"] >= WIN0) & (per["date"] <= WIN1)]
stats["permit_crosscheck"] = {
    "new_building_permits_window": int(len(nb_perm)),
    "new_building_by_year": {str(y): int((nb_perm["date"].dt.year == y).sum()) for y in range(2020, 2027)},
}
dm = demos.copy()
dm["date"] = pd.to_datetime(dm["date"])
wreck = dm[(dm["is_wreck"]) & (dm["active"]) & (dm["date"] >= WIN0) & (dm["date"] <= WIN1)]
stats["permit_crosscheck"]["demolition_permits_window"] = int(len(wreck))

focus = {}
for name in ["Sun Valley", "Civic Center", "Globeville", "Capitol Hill", "Hampden South",
             "Washington Park", "Hilltop", "Belcaro", "Central Park", "Gateway - Green Valley Ranch", "DIA"]:
    sub = assigned[assigned["neighborhood"] == name]
    focus[name] = {"market_sales_2020_plus": int(len(sub)),
                   "median_all": float(sub["SALE_PRICE"].median()) if len(sub) else None}
stats["focus_neighborhoods"] = focus

# ---------- control: parcels layer last-sale record vs sales table ----------
# Join on NUMERIC reception numbers only, on both sides. 5,463 parcels carry
# non-numeric RECEPTION_NUM strings (judgment-style numbers and dates); a
# first version coerced them to NaN and pandas matched NaN keys to the
# sales table's null-reception rows, inflating the checked population and
# contaminating the agreement rates. Caught by the Section 11 verifier;
# see verification.md.
p = parcels[parcels["RECEPTION_NUM"].notna() & (parcels["RECEPTION_NUM"] != "")].copy()
p["rec"] = pd.to_numeric(p["RECEPTION_NUM"], errors="coerce")
p = p[p["rec"].notna()].copy()
srow = sales[sales["RECEPTION_NUM"].notna()].drop_duplicates("RECEPTION_NUM").set_index("RECEPTION_NUM")
both = p[p["rec"].isin(set(srow.index))]
joined = both.join(srow[["SALE_PRICE", "SALE_YEAR"]], on="rec", rsuffix="_tbl")
disagree = joined[joined["SALE_PRICE"] != joined["SALE_PRICE_tbl"]]
stats["control_parcels_last_sale"] = {
    "parcels_checked": int(len(joined)),
    "price_agreement_pct": round(float((joined["SALE_PRICE"] == joined["SALE_PRICE_tbl"]).mean() * 100), 2),
    "year_agreement_pct": round(float((joined["SALE_YEAR"] == joined["SALE_YEAR_tbl"]).mean() * 100), 2),
    "disagreements": int(len(disagree)),
    "disagreements_where_table_price_is_zero_pct": round(
        float((disagree["SALE_PRICE_tbl"] == 0).mean() * 100), 1) if len(disagree) else None,
}
# characteristics join coverage for market sales (recorded; price-per-sqft not used - see verification.md)
char_parcels = set(chars["schednum"].unique())
parcel_keys = set(parcels["schednum"].unique())
keyed = sales[sales["schednum"].notna()]
stats["joins"] = {
    "sales_rows_matched_to_current_parcel_pct": round(
        float(keyed["schednum"].isin(parcel_keys).mean() * 100), 2),
    "sales_rows_keyed": int(len(keyed)),
    "sales_rows_total": int(len(sales)),
    "market_sales_2020_plus_with_neighborhood": int(len(assigned)),
    "market_sales_2020_plus_with_characteristics_record_pct": round(
        float(m["schednum"].isin(char_parcels).mean() * 100), 2),
}

with open(PKG / "stats.json", "w") as f:
    json.dump(stats, f, indent=1)
print(json.dumps({k: stats[k] for k in ["reconciliation", "year_2026_detail", "citywide_pooled",
                                        "lifecycle_citywide", "permit_crosscheck",
                                        "control_parcels_last_sale"]}, indent=1))
print("wrote stats.json and data/neighborhood_sales.csv")
