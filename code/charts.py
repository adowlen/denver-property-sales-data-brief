#!/usr/bin/env python3
"""Charts for the Denver assessor sales keystone brief - Machine Readable brand palette.

Every figure is drawn from stats.json / data/neighborhood_sales.csv (produced by
analyze.py). Text uses plain hyphens only. Data charts only; the hero is a
generated illustration composited by compose_hero.py. Neighborhood geometry is
read from the warehouse neighborhoods layer (WKB parsed with the standard
library; no geopandas dependency).

Run: python3 code/charts.py
"""
import json
import struct
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mcolors
import pandas as pd

CHARCOAL = "#101417"
AMBER = "#F5A800"
TEAL = "#19B8A6"
PAPER = "#F2EFE9"
TEXT_DIM = "#9AA5AB"
GRID = "#2C343A"

PKG = Path(__file__).resolve().parent.parent
STACK = Path("/home/hatch/workspace/goals/daily-civic-data-brief/hidden_files/stack/denver")
OUT = PKG / "charts"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": CHARCOAL, "axes.facecolor": CHARCOAL,
    "axes.edgecolor": GRID, "axes.labelcolor": PAPER, "text.color": PAPER,
    "xtick.color": TEXT_DIM, "ytick.color": TEXT_DIM, "grid.color": GRID,
    "grid.alpha": 0.5, "font.size": 11, "axes.titlesize": 14,
    "axes.titleweight": "bold", "axes.titlecolor": PAPER,
})

s = json.load(open(PKG / "stats.json"))
nb = pd.read_csv(PKG / "data/neighborhood_sales.csv")
SRC = ("Source: City and County of Denver assessor sales and transfers (open data), "
       "snapshot 2026-10-15. Market sales: warranty or special warranty deed with a recorded price.")


def footnote(fig, text=SRC):
    import textwrap
    wrapped = "\n".join(textwrap.wrap(text, 148))
    fig.text(0.012, 0.008, wrapped, fontsize=8.5, color=TEXT_DIM, va="bottom")


def save(fig, name, bottom=0.055):
    fig.tight_layout(rect=[0, bottom, 1, 1])
    fig.savefig(OUT / name, dpi=150, facecolor=CHARCOAL)
    plt.close(fig)
    print("saved", name)


# ---------- 1. yearly cycle: volume bars + median line ----------
yrs = pd.DataFrame(s["yearly"])
fig, ax = plt.subplots(figsize=(10, 5.2))
colors = [TEAL if not p else "#3E6B64" for p in yrs["partial"]]
ax.bar(yrs["year"], yrs["sales"], color=colors, width=0.62, zorder=2)
for _, r in yrs.iterrows():
    ax.annotate(f"{int(r['sales']):,}", (r["year"], r["sales"] + 500),
                ha="center", fontsize=10, color=PAPER)
ax.set_ylabel("Market sales recorded")
ax.set_ylim(0, 25000)
ax.grid(axis="y")
ax2 = ax.twinx()
ax2.plot(yrs["year"], yrs["median_price"] / 1000, color=AMBER, marker="o", lw=2.4, zorder=5)
for _, r in yrs.iterrows():
    ax2.annotate(f"${int(r['median_price']):,}", (r["year"], r["median_price"] / 1000 + 22),
                 ha="center", fontsize=10, color=AMBER)
ax2.set_ylabel("Median sale price ($ thousands)", color=AMBER)
ax2.tick_params(colors=AMBER)
ax2.set_ylim(0, 720)
ax.set_title("Denver market sales: volume peaked in 2021, the median price in 2022")
ax.annotate("2026 is partial: sales are substantially\ncomplete through August (see brief)",
            (2026, 11200), ha="center", fontsize=9.5, color=TEXT_DIM)
footnote(fig)
save(fig, "yearly_cycle.png")

# ---------- 2. neighborhood map: single-family median, pooled 2020+ ----------
def parse_wkb(buf, off=0):
    """Return (list of polygons, new offset). A polygon is a list of rings; a ring is (xs, ys)."""
    endian = "<" if buf[off] == 1 else ">"
    typ = struct.unpack_from(endian + "I", buf, off + 1)[0]
    off += 5
    if typ == 3:  # Polygon
        nrings = struct.unpack_from(endian + "I", buf, off)[0]
        off += 4
        rings = []
        for _ in range(nrings):
            n = struct.unpack_from(endian + "I", buf, off)[0]
            off += 4
            pts = struct.unpack_from(endian + f"{2 * n}d", buf, off)
            off += 16 * n
            rings.append((pts[0::2], pts[1::2]))
        return [rings], off
    if typ == 6:  # MultiPolygon
        npoly = struct.unpack_from(endian + "I", buf, off)[0]
        off += 4
        polys = []
        for _ in range(npoly):
            p, off = parse_wkb(buf, off)
            polys.extend(p)
        return polys, off
    raise ValueError(f"unsupported WKB type {typ}")


geo = pd.read_parquet(STACK / "layers/neighborhoods_clean.parquet")
med = nb.set_index("neighborhood")["median_sfr"]
cnt = nb.set_index("neighborhood")["sales_sfr"]
fig, ax = plt.subplots(figsize=(10.5, 8.5))
cmap = mcolors.LinearSegmentedColormap.from_list("mr", ["#14423C", TEAL, AMBER, "#FFE9B0"])
norm = mcolors.Normalize(vmin=300_000, vmax=1_700_000)
patches, values = [], []
for _, row in geo.iterrows():
    polys, _ = parse_wkb(bytes(row["geometry_wkb"]))
    v = med.get(row["NBHD_NAME"])
    ok = pd.notna(v) and cnt.get(row["NBHD_NAME"], 0) >= 30
    for rings in polys:
        patches.append(MplPolygon(list(zip(rings[0][0], rings[0][1])), closed=True))
        values.append(v if ok else float("nan"))
vals_series = pd.Series(values, dtype=float)
missing = [p for p, v in zip(patches, vals_series) if pd.isna(v)]
if missing:
    ax.add_collection(PatchCollection(missing, facecolor="#232A2E",
                                      edgecolor=CHARCOAL, linewidth=0.4))
pc = PatchCollection(patches, cmap=cmap, norm=norm, edgecolor=CHARCOAL, linewidth=0.4)
pc.set_array(vals_series.values)
pc.set_clim(300_000, 1_700_000)
ax.add_collection(pc)
ax.autoscale_view()
ax.set_axis_off()
ax.set_title("Median single-family sale price by neighborhood, 2020-2026 (pooled)", pad=14)
cb = fig.colorbar(pc, ax=ax, shrink=0.75, ticks=[400_000, 700_000, 1_000_000, 1_300_000, 1_600_000])
cb.ax.set_yticklabels(["$400k", "$700k", "$1.0M", "$1.3M", "$1.6M"])
cb.outline.set_visible(False)
footnote(fig, "Source: Denver assessor sales (snapshot 2026-10-15) joined to parcels and statistical "
              "neighborhoods. Single-family sales only; neighborhoods with fewer than 30 single-family "
              "sales are shown in gray. Medians reflect what sold, not a price index.")
save(fig, "neighborhood_median_map.png")

# ---------- 3. neighborhood median change, single-family basis ----------
inc = s["neighborhood_change_sfr"]["largest_increases"]
dec = s["neighborhood_change_sfr"]["smallest_changes"]
rows = [(r["neighborhood"], r["change_pct"]) for r in reversed(dec)] + \
       [(r["neighborhood"], r["change_pct"]) for r in reversed(inc)]
fig, ax = plt.subplots(figsize=(10, 5.6))
names = [r[0] for r in rows]
vals = [r[1] for r in rows]
ax.barh(names, vals, color=[TEAL if v < 5 else AMBER for v in vals], height=0.62)
for i, v in enumerate(vals):
    ax.annotate(f"{v:+.1f}%", (v + (0.8 if v >= 0 else -0.8), i),
                va="center", ha="left" if v >= 0 else "right", fontsize=10.5, color=PAPER)
ax.axvline(0, color=PAPER, lw=0.8)
ax.axvline(s["citywide_period_medians"]["sfr"]["change_pct"], color=AMBER, lw=1.0, ls="--")
ax.annotate(f"citywide single-family median: +{s['citywide_period_medians']['sfr']['change_pct']}%",
            (s["citywide_period_medians"]["sfr"]["change_pct"] + 0.8, len(rows) - 0.4),
            fontsize=9.5, color=AMBER)
ax.set_xlim(-16, 42)
ax.grid(axis="x")
ax.set_title("Change in median single-family sale price, 2020-21 to 2024-25")
footnote(fig, "Source: Denver assessor sales (snapshot 2026-10-15). Neighborhoods with at least 30 "
              "single-family sales in both periods (68 of 78 qualify).")
save(fig, "neighborhood_change.png")

# ---------- 4. teardown lifecycle ----------
lc = s["lifecycle_citywide"]
fig, ax = plt.subplots(figsize=(10, 5.2))
labels = ["Last purchase before\ndemolition (n=1,428)", "First sale after the\nrebuild permit (n=1,012)",
          "Paired parcels: purchase\n(n=611)", "Paired parcels: sale after\nthe rebuild permit (n=611)"]
vals = [lc["median_pre_demo_buy"], lc["median_first_post_permit_sale"],
        lc["paired_median_buy"], lc["paired_median_sell"]]
ax.bar(labels, [v / 1000 for v in vals], color=[TEAL, AMBER, TEAL, AMBER], width=0.55)
for i, v in enumerate(vals):
    ax.annotate(f"${v:,.0f}", (i, v / 1000 + 60), ha="center", fontsize=11.5, color=PAPER)
ax.set_ylabel("Median price ($ thousands)")
ax.set_ylim(0, 2600)
ax.grid(axis="y")
ax.set_title("The teardown cycle in prices: purchase, demolition, permit, sale (parcel basis)")
footnote(fig, "Source: Denver assessor sales joined to demolition and construction permits by parcel, "
              "2020-01-01 to 2026-10-12. Permits are authorizations, not construction completion. "
              "Paired parcels completed both a pre-demolition purchase and a post-permit sale inside "
              "the record; of 3,297 demolished parcels 962 had no new-building permit by the window "
              "end, including recent demolitions still in flight. Gross spread excludes construction "
              "and financing costs.")
save(fig, "lifecycle.png", bottom=0.13)
print("charts done")
