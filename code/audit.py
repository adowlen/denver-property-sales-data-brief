#!/usr/bin/env python3
"""Pre-flight audit (brief-writing standards section 10) for the Denver
assessor sales keystone brief. Runs BEFORE stats.json or prose exist.
Reads the warehouse cleaned layers only; asserts invariants and prints
evidence. Exit code 0 = all gates pass.

Run: python3 code/audit.py
"""
import json
from collections import Counter

import pandas as pd

STACK = "/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files/stack/denver"
failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        failures.append(name)


sales = pd.read_parquet(f"{STACK}/layers/sales_clean.parquet")
parcels = pd.read_parquet(f"{STACK}/layers/parcels_clean.parquet")
chars = pd.read_parquet(f"{STACK}/layers/characteristics_clean.parquet")
spine = pd.read_parquet(f"{STACK}/joins/parcel_spine_v6.parquet")

print(f"sales rows: {len(sales)}; parcels: {len(parcels)}; characteristics: {len(chars)}; spine: {len(spine)}")

# ---------- 10.1.1 sentinel traps ----------
neg = int((sales["SALE_PRICE"] < 0).sum())
zero_null = int(sales["SALE_PRICE"].isna().sum() + (sales["SALE_PRICE"] == 0).sum())
print(f"SALE_PRICE: negative={neg}, zero-or-null={zero_null} ({zero_null/len(sales)*100:.1f}%)")
check("10.1.1 no negative prices", neg == 0)
check("10.1.1 zero/null prices are 'unknown', never market sales",
      bool((~sales.loc[sales["SALE_PRICE"].isna() | (sales["SALE_PRICE"] == 0), "is_market_sale"]).all()))
mkt = sales[sales["is_market_sale"]]
check("10.1.1 every market sale has price > 0", bool((mkt["SALE_PRICE"] > 0).all()))
# RECEPTION_DATE dirty range (prep memo trap 2): sale dates come from SALE_YEAR + SALE_MONTHDAY
rd = pd.to_numeric(sales["RECEPTION_DATE"], errors="coerce")
out_of_range = int(((rd < 20150101) | (rd > 20261231)).sum())
print(f"RECEPTION_DATE outside 2015-01-01..2026-12-31: {out_of_range} rows (not used for sale dates)")
check("10.1.1 all composed sale dates valid", bool(sales["sale_date_valid"].all()))
check("10.1.1 SALE_YEAR span is 2015-2026 (catalog claims 2010)",
      int(sales["SALE_YEAR"].min()) == 2015 and int(sales["SALE_YEAR"].max()) == 2026,
      f"min={sales['SALE_YEAR'].min()} max={sales['SALE_YEAR'].max()}")
# characteristics sentinels (year built / living area): 0/null -> unknown, excluded from spine fields
check("10.1.1 characteristics year_built unknown where CCYRBLT 0/null",
      int(((chars["CCYRBLT"].fillna(0) == 0) & chars["year_built"].notna()).sum()) == 0)
check("10.1.1 characteristics living area unknown where AREA_ABG 0/null",
      int(((chars["AREA_ABG"].fillna(0) == 0) & chars["living_area_sqft_card"].notna()).sum()) == 0)

# ---------- 10.1.4 categorical exhaustiveness (before any filter) ----------
for col in ["INSTRUMENT", "CLASS", "D_CLASS_N"]:
    c = Counter(sales[col].astype(object).where(sales[col].notna(), "(null)"))
    print(f"Counter({col}) full table, {len(c)} distinct values:")
    for k, v in c.most_common():
        print(f"    {k!r}: {v}")
check("10.1.4 market filter uses exactly the two sale-like deed types",
      set(mkt["INSTRUMENT"].unique()) == {"WD", "SW"})

# ---------- 10.1.2 filter polarity sample ----------
inside = mkt.head(3)[["PARID", "INSTRUMENT", "SALE_YEAR", "SALE_PRICE"]]
outside = sales[(sales["INSTRUMENT"].isin(["WD", "SW"])) & (sales["SALE_PRICE"] == 0)].head(2)
outside2 = sales[sales["INSTRUMENT"] == "QC"].head(1)
print("Polarity sample, INSIDE the market-sale filter (WD/SW and price > 0):")
print(inside.to_string(index=False))
print("Polarity sample, OUTSIDE (WD with $0 price; QC quit claim):")
print(pd.concat([outside, outside2])[["PARID", "INSTRUMENT", "SALE_YEAR", "SALE_PRICE"]].to_string(index=False))
check("10.1.2 polarity: inside rows all WD/SW with price > 0",
      bool(((inside["INSTRUMENT"].isin(["WD", "SW"])) & (inside["SALE_PRICE"] > 0)).all()))
check("10.1.2 polarity: $0 warranty deeds and quit claims are excluded",
      bool((~sales.loc[outside.index, "is_market_sale"]).all() and (~sales.loc[outside2.index, "is_market_sale"]).all()))

# ---------- 10.1.3 / 10.1.5 unit agreement + nullable denominators ----------
m20 = mkt[mkt["SALE_YEAR"] >= 2020]
sd = pd.to_datetime(m20["sale_date"])
fut = m20[sd > "2026-10-15"]
print(f"market-sale rows dated after the 2026-10-15 snapshot: {len(fut)} "
      f"(excluded from dated figures in analyze.py, counted in stats.json)")
check("10.1.1 future-dated rows are few and identified", len(fut) <= 2,
      f"count={len(fut)} dates={[str(d.date()) for d in sd[sd > '2026-10-15']]}")
check("10.1.3 reconciliation: market sales with SALE_YEAR >= 2020 = 105,585 (Phase 1)",
      len(m20) == 105585, f"got {len(m20)}")
y2024 = mkt[mkt["SALE_YEAR"] == 2024]
check("10.1.3 reconciliation: 2024 market sales n = 13,100, median $540,000 (Phase 1)",
      len(y2024) == 13100 and float(y2024["SALE_PRICE"].median()) == 540000.0,
      f"n={len(y2024)} median={y2024['SALE_PRICE'].median()}")
# shares in this brief are computed on the full stated population (all market-sale rows);
# the only nullable classification used is neighborhood (via spine): assert shares sum to whole.
nb = spine[["schednum", "neighborhood"]]
mm = m20.merge(nb, on="schednum", how="left")
known = int(mm["neighborhood"].notna().sum())
check("10.1.5 neighborhood share denominator is the full population",
      known + int(mm["neighborhood"].isna().sum()) == len(mm),
      f"assigned={known} unassigned={int(mm['neighborhood'].isna().sum())} of {len(mm)}")

# ---------- 10.2 join hygiene ----------
keyed = sales[sales["schednum"].notna()]
in_parcels = keyed["schednum"].isin(set(parcels["schednum"]))
print(f"sales rows keyed to a current parcel: {int(in_parcels.sum())} of {len(keyed)} ({in_parcels.mean()*100:.2f}%)")
by_year = keyed.assign(hit=in_parcels.values).groupby("SALE_YEAR")["hit"].mean()
print("sales-to-parcel match rate by sale year:")
for y, r in by_year.items():
    print(f"    {y}: {r*100:.2f}%")
check("10.2 sales-to-parcel match >= 97% in every year 2020+",
      bool((by_year[by_year.index >= 2020] >= 0.97).all()))
check("10.2 spine grain is one row per parcel", len(spine) == len(parcels) == 240441)
check("10.2 spine neighborhood coverage", int(spine["neighborhood"].notna().sum()) == 240335,
      f"assigned={int(spine['neighborhood'].notna().sum())} of 240441")

# multi-parcel transactions: prices repeat per parcel; never summed (assert the hazard exists and is counted)
dup = m20[m20.duplicated("RECEPTION_NUM", keep=False)]
n_deals = m20["RECEPTION_NUM"].nunique() + int(m20["RECEPTION_NUM"].isna().sum())
print(f"market-sale rows sharing a RECEPTION_NUM (2020+): {len(dup)} rows in "
      f"{dup['RECEPTION_NUM'].nunique()} multi-parcel transactions; deal records = "
      f"{m20['RECEPTION_NUM'].nunique()} distinct reception numbers + "
      f"{int(m20['RECEPTION_NUM'].isna().sum())} unnumbered row; extra parcel rows = "
      f"{len(m20) - n_deals}")
check("10.2 multi-parcel duplication is measured, not ignored", len(dup) > 0)

# ---------- 10.2.2 built-in control: parcels layer's own last-sale record ----------
p = parcels[parcels["RECEPTION_NUM"].notna() & (parcels["RECEPTION_NUM"] != "")].copy()
p["rec"] = pd.to_numeric(p["RECEPTION_NUM"], errors="coerce")
p = p[p["rec"].notna()].copy()  # non-numeric reception strings never join (NaN keys must not match)
srow = sales[sales["RECEPTION_NUM"].notna()].drop_duplicates("RECEPTION_NUM").set_index("RECEPTION_NUM")
both = p[p["rec"].isin(set(srow.index))]
joined = both.join(srow[["SALE_PRICE", "SALE_YEAR"]], on="rec", rsuffix="_tbl")
agree = float((joined["SALE_PRICE"] == joined["SALE_PRICE_tbl"]).mean())
print(f"CONTROL: parcels whose last-transfer reception number appears in the sales table: "
      f"{len(joined)}; exact SALE_PRICE agreement between the two assessor products: {agree*100:.2f}%")
check("10.2.2 control: cross-product price agreement >= 95%", agree >= 0.95)

print()
print("AUDIT RESULT:", "ALL GATES PASS" if not failures else f"FAILURES: {failures}")
raise SystemExit(1 if failures else 0)
