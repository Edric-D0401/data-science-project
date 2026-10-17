"""Reproduce the Macao visitor-market comparison from the attributed CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

# Keep machine-specific caches outside the public project.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "macao-tourism-mpl"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MARKETS = ["Chinese mainland", "Hong Kong SAR", "International visitors", "Taiwan region"]
SOURCE_URLS = {
    2024: "https://www.gcs.gov.mo/news/detail/en/N25AUB2Zwi",
    2025: "https://www.gcs.gov.mo/news/detail/en/N26AWC98hd",
}
SOURCE_TOTALS = {2024: 34_928_650, 2025: 40_069_360}
BLUE = "#235A7B"
GREY = "#CAD4DC"
INK = "#183344"


def load_and_validate(csv_path: Path) -> pd.DataFrame:
    """Validate grain, coverage, units and reconciliation to published totals."""
    data = pd.read_csv(csv_path)
    required = {"year", "source_market", "visitor_arrivals", "unit", "source_url"}
    if set(data.columns) != required:
        raise ValueError(f"Expected columns: {sorted(required)}")
    if data.isna().any().any() or len(data) != 8:
        raise ValueError("Expected eight complete rows: two years by four markets.")
    if data.duplicated(["year", "source_market"]).any():
        raise ValueError("Duplicate year-market observations.")
    if set(data["year"]) != {2024, 2025}:
        raise ValueError("Only the two full calendar years 2024 and 2025 are supported.")
    if not data["unit"].eq("arrival visits").all():
        raise ValueError("Counts must be arrival visits, not unique people.")
    counts = pd.to_numeric(data["visitor_arrivals"], errors="raise")
    if not ((counts > 0) & (counts % 1 == 0)).all():
        raise ValueError("Expected positive integer arrival counts.")
    data["visitor_arrivals"] = counts.astype("int64")
    for year, group in data.groupby("year"):
        if set(group["source_market"]) != set(MARKETS):
            raise ValueError(f"Incomplete market coverage in {year}.")
        if not group["source_url"].eq(SOURCE_URLS[year]).all():
            raise ValueError(f"Incorrect source attribution in {year}.")
        if int(group["visitor_arrivals"].sum()) != SOURCE_TOTALS[year]:
            raise ValueError(f"Counts do not reconcile to the published {year} total.")
    return data


def calculate(data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Separate growth rate, market share and arithmetic growth contribution."""
    comparison = data.pivot(index="source_market", columns="year", values="visitor_arrivals").loc[MARKETS]
    comparison = comparison.rename(columns={2024: "arrivals_2024", 2025: "arrivals_2025"})
    comparison.columns.name = None
    increase = SOURCE_TOTALS[2025] - SOURCE_TOTALS[2024]
    comparison["increase_arrivals"] = comparison.arrivals_2025 - comparison.arrivals_2024
    comparison["growth_pct"] = comparison.increase_arrivals / comparison.arrivals_2024 * 100
    comparison["share_2024_pct"] = comparison.arrivals_2024 / SOURCE_TOTALS[2024] * 100
    comparison["share_2025_pct"] = comparison.arrivals_2025 / SOURCE_TOTALS[2025] * 100
    comparison["share_change_pp"] = comparison.share_2025_pct - comparison.share_2024_pct
    comparison["growth_contribution_pct"] = comparison.increase_arrivals / increase * 100
    assert int(comparison.increase_arrivals.sum()) == increase
    assert abs(comparison.growth_contribution_pct.sum() - 100) < 1e-9
    assert abs(comparison.share_2024_pct.sum() - 100) < 1e-9
    assert abs(comparison.share_2025_pct.sum() - 100) < 1e-9
    summary = {
        "years": [2024, 2025],
        "unit": "arrival visits",
        "total_2024": SOURCE_TOTALS[2024],
        "total_2025": SOURCE_TOTALS[2025],
        "total_increase": increase,
        "total_growth_pct": increase / SOURCE_TOTALS[2024] * 100,
        "mainland_growth_contribution_pct": float(comparison.loc["Chinese mainland", "growth_contribution_pct"]),
        "mainland_share_2024_pct": float(comparison.loc["Chinese mainland", "share_2024_pct"]),
        "mainland_share_2025_pct": float(comparison.loc["Chinese mainland", "share_2025_pct"]),
        "international_growth_pct": float(comparison.loc["International visitors", "growth_pct"]),
        "international_share_2024_pct": float(comparison.loc["International visitors", "share_2024_pct"]),
        "international_share_2025_pct": float(comparison.loc["International visitors", "share_2025_pct"]),
        "interpretation": "Descriptive accounting comparison; growth contribution is not a causal effect.",
    }
    return comparison, summary


def set_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 12,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
        "ytick.color": INK, "axes.spines.top": False,
        "axes.spines.right": False, "axes.edgecolor": "#8DA0AC",
        "savefig.facecolor": "white", "svg.fonttype": "none",
        "svg.hashsalt": "macao-tourism-2024-2025",
    })


def add_footer(fig: plt.Figure, note: str) -> None:
    fig.text(.055, .088, note, fontsize=10, color="#4C616E")
    fig.text(.055, .053, "Source: DSEC via NEWS GOV-MO; 2024 and 2025 annual visitor-arrival releases. Accessed 14 Oct 2026.", fontsize=9, color="#4C616E")
    fig.text(.055, .023, "Source links and calculation methods: README.md and data/SOURCES.md. Independent educational analysis.", fontsize=9, color="#4C616E")


def save_figure(fig: plt.Figure, out: Path, stem: str) -> list[Path]:
    files = []
    for ext in ("png", "svg"):
        path = out / f"{stem}.{ext}"
        metadata = {"Date": None} if ext == "svg" else {"Software": "Macao tourism analysis"}
        fig.savefig(path, dpi=180, metadata=metadata)
        files.append(path)
    plt.close(fig)
    return files


def plot_market_size(comparison: pd.DataFrame, out: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=(12, 7.2))
    fig.subplots_adjust(left=.235, right=.92, top=.76, bottom=.21)
    fig.text(.055, .93, "Macao visitor arrivals by source market", fontsize=23, weight="bold")
    fig.text(.055, .872, "Full calendar years 2024 and 2025 | Counts measure visits, including repeat visits", fontsize=12)
    y = list(range(len(comparison)))
    values_old = comparison.arrivals_2024 / 1e6
    values_new = comparison.arrivals_2025 / 1e6
    ax.barh([v-.18 for v in y], values_old, height=.31, color=GREY, edgecolor="#708999", hatch="//", linewidth=.7, label="2024")
    ax.barh([v+.18 for v in y], values_new, height=.31, color=BLUE, label="2025")
    for position, old, new in zip(y, values_old, values_new):
        ax.text(old+.28, position-.18, f"{old:.2f}m", va="center", fontsize=11)
        ax.text(new+.28, position+.18, f"{new:.2f}m", va="center", fontsize=11, weight="bold")
    ax.set_yticks(y, comparison.index)
    ax.invert_yaxis()
    ax.set_xlim(0, 33)
    ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
    ax.set_xlabel("Visitor arrival visits (millions)", labelpad=10)
    ax.xaxis.grid(True, color="#E0E6EA", linewidth=.7)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=2, loc="lower right", bbox_to_anchor=(1, 1.02))
    add_footer(fig, "All four reported source-market categories are included; international visitors exclude the other three categories.")
    return save_figure(fig, out, "01_arrivals_by_market")


def plot_growth(comparison: pd.DataFrame, out: Path) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(12, 7.2), sharey=True)
    fig.subplots_adjust(left=.235, right=.92, top=.70, bottom=.235, wspace=.25)
    fig.text(.055, .93, "Macao visitor-market growth and contribution", fontsize=23, weight="bold")
    fig.text(.055, .872, "Change from 2024 to 2025 | Total increase: 5,140,710 arrival visits (+14.7%)", fontsize=12)
    measures = [
        ("growth_pct", "Growth within each market", "Change / 2024 market arrivals", 26, [0, 10, 20]),
        ("growth_contribution_pct", "Share of the total increase", "Market increase / total increase", 107, [0, 25, 50, 75, 100]),
    ]
    for ax, (column, title, xlabel, limit, ticks) in zip(axes, measures):
        values = comparison[column]
        ax.barh(range(len(values)), values, color=BLUE, height=.46)
        for y, value in enumerate(values):
            ax.text(value + limit*.025, y, f"{value:.1f}%", va="center", fontsize=11, weight="bold")
        ax.set_title(title, loc="left", fontsize=13, weight="bold", pad=22)
        ax.set_xlim(0, limit)
        ax.set_xticks(ticks)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}%"))
        ax.set_xlabel(xlabel, fontsize=10, labelpad=12)
        ax.xaxis.grid(True, color="#E0E6EA", linewidth=.7)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(comparison)), comparison.index)
    axes[0].invert_yaxis()
    axes[1].tick_params(axis="y", left=False)
    axes[1].spines["left"].set_visible(False)
    add_footer(fig, "Panels use different percentage scales and denominators. Contribution is an arithmetic decomposition, not causation.")
    return save_figure(fig, out, "02_growth_and_contribution")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/visitor_arrivals_2024_2025.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    data = load_and_validate(args.data)
    comparison, summary = calculate(data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.output_dir / "market_comparison.csv", float_format="%.10f")
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    set_style()
    files = plot_market_size(comparison, args.output_dir) + plot_growth(comparison, args.output_dir)
    validation = {
        "input_rows": len(data), "year_market_keys_unique": True,
        "missing_values": 0, "source_totals_reconciled": True,
        "market_shares_sum_to_100_pct": True, "growth_contributions_sum_to_100_pct": True,
        "csv_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "figure_files": [p.name for p in files],
        "numeric_checks": "passed", "visual_review": "not performed by this script",
    }
    (args.output_dir / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(data)} source rows; generated 2 figures in PNG and SVG.")
    print(f"Total increase: {summary['total_increase']:,} arrival visits ({summary['total_growth_pct']:.2f}%).")
    print(f"Mainland share of increase: {summary['mainland_growth_contribution_pct']:.2f}%.")


if __name__ == "__main__":
    main()
