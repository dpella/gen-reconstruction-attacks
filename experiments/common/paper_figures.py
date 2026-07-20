"""
Publication-quality figures for the Evaluation section.

Reads `experiments/benchmark_results.csv` (produced by `benchmark.sh`) and
emits one figure per evaluation claim, each as PDF (vector, for LaTeX)
and PNG (preview). All figures share a consistent style so they can sit
side-by-side in the paper.

Figures:
  fig_scaling          — total wall-clock time vs n, log–log, with the
                         measured trend and O(n), O(n²), O(n³) refs;
                         MIP base=8 only (the uniform pipeline config).
  fig_phase_breakdown  — stacked bars: per-phase time at each n
                         (MIP search / Hadamard / compression / verify);
                         MIP base=8 only.
  fig_mip_sweep        — total time vs n, one line per MIP base ∈ {4,8,16},
                         showing that small base + Hadamard is Pareto.
  fig_schema_invariance— at each n where we have ≥ 2 schemas, plot the
                         individual datapoints to show that pipeline
                         cost depends on n, not schema specifics.
  fig_accuracy         — max reconstruction error vs n, log-log; confirms
                         that reconstruction stays exact under integer
                         rounding across the whole range.

Usage:
    python3 experiments/common/paper_figures.py
                    [--exp-dir experiments]
                    [--fig-dir experiments/figures]
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --- shared style -----------------------------------------------------------

PALETTE = {
    "mip":      "#4E79A7",
    "hadamard": "#F28E2B",
    "compress": "#59A14F",
    "verify":   "#E15759",
    "total":    "#333333",
    "base4":    "#1F77B4",
    "base8":    "#2CA02C",
    "base16":   "#D62728",
}

PHASE_FIELDS = [
    ("t_mip",      "MIP search",        PALETTE["mip"]),
    ("t_hadamard", "Hadamard expansion", PALETTE["hadamard"]),
    ("t_compress", "compression",        PALETTE["compress"]),
    ("t_verify",   "verify (lstsq)",     PALETTE["verify"]),
]

SCHEMA_FAMILY = {
    "01_sdtm_vs":             "CDISC SDTM",
    "02_adam_adsl":           "CDISC ADaM",
    "03_adam_adlb":           "CDISC ADaM",
    "04_adam_adpc":           "CDISC ADaM",
    "05_adam_adpc_extended":  "CDISC ADaM",
    "06_hr_open_n256":        "HR Open",
    "07_hr_open_n512":        "HR Open",
    "08_eurostat_silc_n128":  "SDMX EU-SILC",
    "09_eurostat_silc_n512":  "SDMX EU-SILC",
}
FAMILY_MARKER = {
    "CDISC SDTM":    ("o", PALETTE["mip"]),
    "CDISC ADaM":    ("s", PALETTE["hadamard"]),
    "HR Open":       ("^", PALETTE["compress"]),
    "SDMX EU-SILC":  ("D", PALETTE["verify"]),
}


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi":          120,
        "savefig.dpi":         200,
        "savefig.bbox":        "tight",
        "font.family":         "serif",
        "font.size":           10,
        "axes.titlesize":      11,
        "axes.labelsize":      10,
        "legend.fontsize":     9,
        "xtick.labelsize":     9,
        "ytick.labelsize":     9,
        "axes.grid":           True,
        "grid.alpha":          0.3,
        "grid.linestyle":      "--",
        "axes.axisbelow":      True,
        "lines.markersize":    6,
        "lines.linewidth":     1.6,
    })


PHASES = ["t_mip", "t_hadamard", "t_compress", "t_verify", "t_total"]


def _load_raw(csv_path: Path) -> List[dict]:
    """Per-run samples (benchmark_results_raw.csv)."""
    rows = []
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            r["n"] = int(r["n"])
            r["mip_base"] = int(r["mip_base"])
            r["hadamard_order"] = int(r["hadamard_order"])
            r["rep"] = int(r["rep"])
            for k in PHASES + ["max_abs_error"]:
                r[k] = float(r[k])
            r["exact"] = r["exact"] == "True"
            r["full_rank"] = r["full_rank"] == "True"
            rows.append(r)
    return rows


def _aggregate_by(rows: List[dict], keys: List[str]) -> Dict[tuple, dict]:
    """Group rows by the given keys; return per-group mean, stdev, CI95
    for each timing field.  Robust to single-sample groups."""
    import statistics
    bucket: Dict[tuple, List[dict]] = defaultdict(list)
    for r in rows:
        bucket[tuple(r[k] for k in keys)].append(r)
    out: Dict[tuple, dict] = {}
    for key, samples in bucket.items():
        rec = {"n_samples": len(samples)}
        for f in PHASES + ["max_abs_error"]:
            xs = [s[f] for s in samples]
            mean = statistics.fmean(xs)
            stdev = statistics.stdev(xs) if len(xs) > 1 else 0.0
            ci95 = 1.96 * stdev / (len(xs) ** 0.5) if len(xs) > 1 else 0.0
            rec[f"{f}_mean"] = mean
            rec[f"{f}_stdev"] = stdev
            rec[f"{f}_ci95"] = ci95
        out[key] = rec
    return out


def _save(fig, fig_dir: Path, name: str) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(fig_dir / f"{name}.{ext}")
    plt.close(fig)


# --- fig_scaling ------------------------------------------------------------

def fig_scaling(rows: List[dict], fig_dir: Path) -> None:
    data = [r for r in rows if r["mip_base"] == 8]
    ns = sorted({r["n"] for r in data})
    agg = _aggregate_by(data, ["n"])

    t_mean = np.array([agg[(n,)]["t_total_mean"] for n in ns])
    t_ci = np.array([agg[(n,)]["t_total_ci95"] for n in ns])

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.errorbar(ns, t_mean, yerr=t_ci, fmt="o-", color=PALETTE["total"],
                ecolor="0.3", elinewidth=1, capsize=3,
                label="measured (mean ± 95 % CI)")
    ax.set_xscale("log"); ax.set_yscale("log")

    # Reference lines anchored at the smallest n
    x = np.array(ns, dtype=float)
    anchor_n, anchor_t = x[0], t_mean[0]
    for exp, ls in [(1, ":"), (2, "--"), (3, "-.")]:
        ax.loglog(x, anchor_t * (x / anchor_n) ** exp, ls,
                  alpha=0.45, label=f"O(n^{exp})")

    ax.set_xticks(ns); ax.set_xticklabels([str(n) for n in ns])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("target records n")
    ax.set_ylabel("total wall-clock time (s)")
    ax.set_title("Pipeline scaling (MIP base = 8, p = 0.5, c = 0.25)")
    ax.legend(loc="upper left")
    _save(fig, fig_dir, "fig_scaling")


# --- fig_phase_breakdown ---------------------------------------------------

def fig_phase_breakdown(rows: List[dict], fig_dir: Path) -> None:
    data = [r for r in rows if r["mip_base"] == 8]
    ns = sorted({r["n"] for r in data})
    agg = _aggregate_by(data, ["n"])

    # Per-phase lines on a log-log plot so that the MIP floor (~100 ms) is
    # visible alongside Hadamard (which grows as n^2). A stacked-bar plot
    # on a linear axis hides the small phases entirely.
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    for p, label, color in PHASE_FIELDS:
        means = np.array([agg[(n,)][f"{p}_mean"] for n in ns])
        cis   = np.array([agg[(n,)][f"{p}_ci95"] for n in ns])
        ax.errorbar(ns, means, yerr=cis, fmt="o-", color=color,
                    ecolor=color, elinewidth=1, capsize=3, label=label)

    totals = np.array([agg[(n,)]["t_total_mean"] for n in ns])
    total_ci = np.array([agg[(n,)]["t_total_ci95"] for n in ns])
    ax.errorbar(ns, totals, yerr=total_ci, fmt="s--",
                color=PALETTE["total"], ecolor="0.3", elinewidth=1,
                capsize=3, label="total", alpha=0.85)

    n_samples = agg[(ns[0],)]["n_samples"]
    ax.set_xticks(ns); ax.set_xticklabels([str(n) for n in ns])
    ax.set_xlabel("target records n")
    ax.set_ylabel("wall-clock time (s)")
    ax.set_title(f"Per-phase breakdown (MIP base = 8, {n_samples} reps)")
    ax.legend(loc="upper left", framealpha=0.95)
    _save(fig, fig_dir, "fig_phase_breakdown")


# --- fig_mip_sweep ---------------------------------------------------------

def fig_mip_sweep(rows: List[dict], fig_dir: Path) -> None:
    agg = _aggregate_by(rows, ["mip_base", "n"])

    fig, (ax_t, ax_m) = plt.subplots(1, 2, figsize=(10.5, 4.0))

    for base in sorted({r["mip_base"] for r in rows}):
        ns = sorted({n for (b, n) in agg if b == base})
        ts = np.array([agg[(base, n)]["t_total_mean"] for n in ns])
        ci = np.array([agg[(base, n)]["t_total_ci95"] for n in ns])
        col = PALETTE[f"base{base}"]
        ax_t.errorbar(ns, ts, yerr=ci, fmt="o-", color=col, ecolor=col,
                      elinewidth=1, capsize=3, label=f"MIP base = {base}")
    ax_t.set_xscale("log"); ax_t.set_yscale("log")
    ax_t.set_xticks([16, 32, 64, 128, 256, 512])
    ax_t.set_xticklabels(["16", "32", "64", "128", "256", "512"])
    ax_t.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax_t.set_xlabel("target records n")
    ax_t.set_ylabel("total wall-clock time (s)")
    ax_t.set_title("Total time — MIP base sweep")
    ax_t.legend(loc="upper left")

    for base in sorted({r["mip_base"] for r in rows}):
        ns = sorted({n for (b, n) in agg if b == base})
        ts = np.array([agg[(base, n)]["t_mip_mean"] for n in ns])
        ci = np.array([agg[(base, n)]["t_mip_ci95"] for n in ns])
        col = PALETTE[f"base{base}"]
        ax_m.errorbar(ns, ts, yerr=ci, fmt="o-", color=col, ecolor=col,
                      elinewidth=1, capsize=3, label=f"MIP base = {base}")
    ax_m.set_xscale("log")
    ax_m.set_xticks([16, 32, 64, 128, 256, 512])
    ax_m.set_xticklabels(["16", "32", "64", "128", "256", "512"])
    ax_m.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax_m.set_xlabel("target records n")
    ax_m.set_ylabel("MIP-phase time (s)")
    ax_m.set_title("MIP-phase time — base sweep")
    ax_m.legend(loc="upper left")

    fig.tight_layout()
    _save(fig, fig_dir, "fig_mip_sweep")


def fig_mip_sweep_total(rows: List[dict], fig_dir: Path) -> None:
    """Standalone total-time panel of the MIP base sweep (for appendix)."""
    agg = _aggregate_by(rows, ["mip_base", "n"])
    fig, ax = plt.subplots(figsize=(5.0, 4.0))
    for base in sorted({r["mip_base"] for r in rows}):
        ns = sorted({n for (b, n) in agg if b == base})
        ts = np.array([agg[(base, n)]["t_total_mean"] for n in ns])
        ci = np.array([agg[(base, n)]["t_total_ci95"] for n in ns])
        col = PALETTE[f"base{base}"]
        ax.errorbar(ns, ts, yerr=ci, fmt="o-", color=col, ecolor=col,
                    elinewidth=1, capsize=3, label=f"MIP base = {base}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xticks([16, 32, 64, 128, 256, 512])
    ax.set_xticklabels(["16", "32", "64", "128", "256", "512"])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("target records n")
    ax.set_ylabel("total wall-clock time (s)")
    ax.set_title("Total time — MIP base sweep")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, fig_dir, "fig_mip_sweep_total")


def fig_mip_sweep_mip(rows: List[dict], fig_dir: Path) -> None:
    """Standalone MIP-phase-time panel of the MIP base sweep (for main text)."""
    agg = _aggregate_by(rows, ["mip_base", "n"])
    fig, ax = plt.subplots(figsize=(5.0, 4.0))
    for base in sorted({r["mip_base"] for r in rows}):
        ns = sorted({n for (b, n) in agg if b == base})
        ts = np.array([agg[(base, n)]["t_mip_mean"] for n in ns])
        ci = np.array([agg[(base, n)]["t_mip_ci95"] for n in ns])
        col = PALETTE[f"base{base}"]
        ax.errorbar(ns, ts, yerr=ci, fmt="o-", color=col, ecolor=col,
                    elinewidth=1, capsize=3, label=f"MIP base = {base}")
    ax.set_xscale("log")
    ax.set_xticks([16, 32, 64, 128, 256, 512])
    ax.set_xticklabels(["16", "32", "64", "128", "256", "512"])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("target records n")
    ax.set_ylabel("MIP-phase time (s)")
    ax.set_title("MIP-phase time — base sweep")
    ax.legend(loc="upper left")
    fig.tight_layout()
    _save(fig, fig_dir, "fig_mip_sweep_mip")


# --- fig_schema_invariance -------------------------------------------------

def fig_schema_invariance(rows: List[dict], fig_dir: Path) -> None:
    data = [r for r in rows if r["mip_base"] == 8]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))

    # Per-schema aggregate (each schema → one point with error bars)
    agg = _aggregate_by(data, ["schema", "n"])
    for fam, (mk, col) in FAMILY_MARKER.items():
        fam_schemas = [s for s in SCHEMA_FAMILY if SCHEMA_FAMILY[s] == fam]
        ns, ts, ci = [], [], []
        for s in fam_schemas:
            for key in agg:
                if key[0] == s:
                    ns.append(key[1])
                    ts.append(agg[key]["t_total_mean"])
                    ci.append(agg[key]["t_total_ci95"])
        if not ns:
            continue
        ax.errorbar(ns, ts, yerr=ci, fmt=mk, color=col, ecolor=col,
                    markersize=9, markeredgecolor="white", markeredgewidth=0.7,
                    linestyle="none", capsize=3, label=fam)

    # Cross-schema mean line per n
    agg_n = _aggregate_by(data, ["n"])
    ns = sorted({k[0] for k in agg_n})
    t_mean = [agg_n[(n,)]["t_total_mean"] for n in ns]
    ax.plot(ns, t_mean, "-", color="0.3", alpha=0.5, linewidth=1.3, zorder=1,
            label="cross-schema mean")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xticks([16, 32, 64, 128, 256, 512])
    ax.set_xticklabels(["16", "32", "64", "128", "256", "512"])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("target records n")
    ax.set_ylabel("total wall-clock time (s)")
    ax.set_title("Schema invariance: cost depends on n, not on schema")
    ax.legend(loc="upper left")
    _save(fig, fig_dir, "fig_schema_invariance")


# --- fig_accuracy ----------------------------------------------------------

def fig_accuracy(rows: List[dict], fig_dir: Path) -> None:
    data = [r for r in rows if r["mip_base"] == 8]
    by_n: Dict[int, List[float]] = defaultdict(list)
    for r in data:
        by_n[r["n"]].append(r["max_abs_error"])
    ns = sorted(by_n)
    err_max  = [max(by_n[n]) for n in ns]
    err_mean = [float(np.mean(by_n[n])) for n in ns]

    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.loglog(ns, err_mean, "o-", color=PALETTE["verify"],
              label=r"mean $\max_i |\hat s_i - s_i|$")
    ax.loglog(ns, err_max, "o--", color=PALETTE["hadamard"], markersize=5,
              alpha=0.75, label=r"worst-run $\max_i |\hat s_i - s_i|$")
    ax.axhline(0.5, color="0.3", linestyle="--", alpha=0.7,
               label="integer-rounding threshold (0.5)")
    ax.set_xticks(ns); ax.set_xticklabels([str(n) for n in ns])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("target records n")
    ax.set_ylabel("reconstruction error")
    ax.set_title("Reconstruction is exact after integer rounding at every n")
    ax.legend(loc="center left", framealpha=0.95)
    _save(fig, fig_dir, "fig_accuracy")


# --- main ------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-dir", type=Path,
                    default=Path(__file__).resolve().parents[1])
    ap.add_argument("--fig-dir", type=Path, default=None,
                    help="output directory (default: <exp-dir>/figures)")
    args = ap.parse_args()
    fig_dir = args.fig_dir or (args.exp_dir / "figures")

    raw = args.exp_dir / "benchmark_results_raw.csv"
    if not raw.exists():
        raise SystemExit(
            f"missing {raw} — run `experiments/benchmark.sh` "
            "(it now produces benchmark_results_raw.csv with per-run samples)"
        )
    rows = _load_raw(raw)
    if not rows:
        raise SystemExit(f"empty {raw}")

    _style()
    fig_scaling(rows, fig_dir)
    fig_phase_breakdown(rows, fig_dir)
    fig_mip_sweep(rows, fig_dir)
    fig_mip_sweep_total(rows, fig_dir)
    fig_mip_sweep_mip(rows, fig_dir)
    fig_schema_invariance(rows, fig_dir)
    fig_accuracy(rows, fig_dir)

    produced = sorted(fig_dir.glob("fig_*.pdf"))
    print(f"wrote {len(produced)} figures to {fig_dir}:")
    for p in produced:
        print(f"  {p.name}  (+ {p.stem}.png)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
