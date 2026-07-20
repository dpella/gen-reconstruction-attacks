# Experiments — Reconstructable Datasets from Industry-Standard Schemas

Reproducible experiments demonstrating that the attack-smt tool
generates **fully reconstructable** synthetic datasets with *realistic,
innocent-looking aggregates* over well-populated groups.  Covers three
standard families: clinical trials (CDISC **SDTM**, **ADaM**),
enterprise HR (**HR Open Standards** / HR-XML), and official
statistical microdata (**Eurostat EU-SILC / HBS**, SDMX-compliant).

Each experiment produces:

- `table.csv` — synthetic table with CDISC-style column names and
  categorical values.
- `queries.sql` — the n released aggregate queries.
- `reconstruction.{txt,json}` — proof that the released aggregates
  uniquely determine the sensitive column (full rank + exact solution
  of `M · s = b`).

## Experiments at a glance

| # | Schema | Standard | n | Sensitive | Construction | Wall clock |
|---|---|---|---|---|---|---|
| 01 | VS (Vital Signs) | SDTM | 16 | `sysbp` | MIP base=8 → Hadamard k=2 | < 1 s |
| 02 | ADSL (Subject-Level Analysis) | ADaM | 32 | `egfrbl` | MIP base=8 → Hadamard k=3 | < 1 s |
| 03 | ADLB (Chem + Hematology) | ADaM | 64 | `aval` (PARAMCD=GLUC) | MIP base=8 → Hadamard k=4 | ≈ 2 s |
| 04 | ADPC (PK Concentrations) | ADaM | 128 | `conc_24h` | MIP base=8 → Hadamard k=5 | ≈ 5 s |
| 05 | ADPC extended (parent + metabolite) | ADaM | 256 | `conc_24h` (parent, p1, 24 h) | MIP base=8 → Hadamard k=6 | ≈ 9 s |
| 06 | HR Open Standards (24-month HRIS) | HR-Open | 256 | `salary` | MIP base=8 → Hadamard k=6 | ≈ 9 s |
| 07 | HR Open Standards (36-month HRIS) | HR-Open | 512 | `salary` | MIP base=8 → Hadamard k=7 | ≈ 28 s |
| 08 | Eurostat EU-SILC (4-yr panel) | SDMX | 128 | `total_disposable_income` | MIP base=8 → Hadamard k=5 | ≈ 4 s |
| 09 | Eurostat EU-SILC × HBS integrated | SDMX | 512 | `total_disposable_income` | MIP base=8 → Hadamard k=7 | ≈ 28 s |

All experiments use `(p, c) = (0.5, 0.25)` so each released aggregate
averages exactly `n/2` subjects — innocent-looking "half the cohort"
queries, not singletons.

## Benchmark: MIP base × target n sweep

`experiments/benchmark.sh` runs each of the five schemas at every feasible
MIP base ∈ {4, 8, 16} (with `hadamard_order` derived so the final record
count matches), measuring per-section wall time. Results land in
`benchmark_results.{csv,md}`.

Reproduce with:

```bash
bash experiments/benchmark.sh   # ≈ 2 min end-to-end (21 runs)
```

What the sweep shows (see `benchmark_results.md` for the full table):

- **MIP cost grows with base**: ~20 ms at base=4, ~140 ms at base=8, ~460 ms
  at base=16 — consistent with the exponential MIP search space.
- **Hadamard cost is essentially constant per target n**: dominated by the
  final matrix size, not by how many doublings produced it.
- **At small n, MIP dominates**: pure-MIP (k=1, base=16) at n=16 is ~5×
  slower than MIP base=4 + Hadamard k=3.
- **At large n, Hadamard + verify dominate**: MIP base choice becomes
  irrelevant; total time is ~6.7 s at n=256 and ~29 s at n=512 for all
  three base choices.
- **Hadamard scaling wall**: the sympy-based Sylvester doubling currently
  takes ~26 s at n=512 — the dominant cost. A NumPy-backed implementation
  would reduce this by one or two orders of magnitude.

Paper takeaway: a small MIP base + Hadamard scaling is Pareto-optimal
across the whole range, and the practical bottleneck at large n is the
Hadamard step itself, not the solver.

## Paper figures (for the Evaluation section)

All 9 experiments share the same pipeline parameters — **MIP base = 8,
(p, c) = (0.5, 0.25)** — with Hadamard order k = log₂(n / 8) + 1
automatically derived so n = 8 · 2^(k−1). This makes n the only
variable, so plotting total time vs n directly reflects pipeline
scaling.

```bash
REPEATS=5 bash experiments/benchmark.sh             # ~10 min (warmup + 5 reps per config)
python3 experiments/common/paper_figures.py         # emits figures/ directory
```

### Outputs

- `benchmark_results_raw.csv` — per-run samples (for custom analysis).
- `benchmark_results.csv` — one row per (schema, base) with mean, stdev,
  and 95 % CI half-width for each timing field.
- `benchmark_results.md` — paper-ready markdown, mean ± stdev per cell.
- `figures/fig_scaling.{pdf,png}` — total time vs n, log-log, with a
  power-law fit on the large-n regime and O(n), O(n²), O(n³) references.
  Error bars = 95 % CI.
- `figures/fig_phase_breakdown.{pdf,png}` — stacked bars: MIP search,
  Hadamard expansion, compression, verify — at each n; error bars on
  top of each stack = 95 % CI on total.
- `figures/fig_mip_sweep.{pdf,png}` — total & MIP-phase time vs n for
  each MIP base ∈ {4, 8, 16}; shows base=4 is fastest and base=16 pays
  a constant ~400 ms MIP tax.
- `figures/fig_schema_invariance.{pdf,png}` — per-schema datapoints
  coloured by family, showing tight overlap at each n.
- `figures/fig_accuracy.{pdf,png}` — max reconstruction error vs n
  (mean across reps and worst-case per n), compared to the integer
  rounding threshold (0.5).

### Statistical protocol

- One warmup run per config is always discarded (cold-cache / JIT).
- `REPEATS` defaults to 5; override with env var (e.g., `REPEATS=10 bash experiments/benchmark.sh`).
- Error bars on all plots are 95 % CI half-width (`1.96 · σ / √N`).
- Accuracy plot shows both the *mean* and *worst-run* max reconstruction
  error to ensure no single bad run hides below the mean.

### What the plots show

- **Hadamard expansion dominates at every n**; MIP search is a
  ~100 ms floor regardless of n; reconstruction-verify grows
  noticeably past n = 128.
- **Same-n schemas overlap tightly** (e.g. ADPC-128 and SILC-128 both
  ≈ 2.0 s; ADPC-256 / HR-256 both ≈ 6.7 s; HR-512 / SILC-512 both
  ≈ 28 s) — pipeline cost is a function of n, not of schema specifics.
- **Measured total scales near O(n²) at large n**, matching the sympy
  Sylvester implementation; a NumPy rewrite would flatten this.
- **Reconstruction stays exact** (worst-case error 7+ orders of
  magnitude below the integer rounding threshold) at every n.

## Reproduce

### One-shot

```bash
# From the repo root:
bash experiments/run_all.sh
```

This runs all four experiments sequentially and prints a final summary.

### Single experiment

```bash
bash experiments/01_sdtm_vs/run.sh
bash experiments/02_adam_adsl/run.sh
bash experiments/03_adam_adlb/run.sh
bash experiments/04_adam_adpc/run.sh
bash experiments/05_adam_adpc_extended/run.sh
bash experiments/06_hr_open_n256/run.sh
bash experiments/07_hr_open_n512/run.sh
bash experiments/08_eurostat_silc_n128/run.sh
bash experiments/09_eurostat_silc_n512/run.sh
```

## Prerequisites

- Python 3.10+
- System: `apt-get install -y glpk-utils libglpk-dev`
- Python: `pip install -r requirements.txt && pip install cvxopt cvxpy[GLPK] pyyaml`

The driver imports the tool's `src/` modules directly (no subprocess),
so seeding is deterministic — re-running with the same schema.yaml +
seed yields bit-identical `table.csv` and `queries.sql`.

## Layout

```
experiments/
├── README.md               ← this file
├── run_all.sh              ← one-shot reproduction
├── common/
│   └── driver.py           ← custom runner: MIP → Hadamard → compression
│                              → rename → CSV + SQL + reconstruction check
├── 01_sdtm_vs/
│   ├── README.md
│   ├── schema.yaml          ← single source of truth for this experiment
│   ├── run.sh
│   └── output/
│       ├── table.csv
│       ├── queries.sql
│       ├── reconstruction.txt
│       └── reconstruction.json
├── 02_adam_adsl/ …
├── 03_adam_adlb/ …
└── 04_adam_adpc/
    ├── generate_schema.py   ← emits schema.yaml (43 compression groups)
    └── …
```

## What the driver does

For each experiment the common driver (`common/driver.py`) runs the
same four-stage pipeline described in the paper:

1. **Initial table** — `mip_base` rows of random binary data.
2. **MIP search** (`Search.generate_fullrank_table`) — iteratively
   extends the query matrix with new rows satisfying the
   balance/overlap constraints (Theorem 1 in the paper), reaching
   rank `mip_base − 1`. The final row is added by the closing
   strategy (Theorem 2 / 3).
3. **Hadamard expansion** (`Hadamard.generate_new_table`) — applies
   Sylvester's construction `hadamard_order − 1` times to reach
   `n = mip_base · 2^(hadamard_order − 1)` records and queries
   (Theorems 4–5).
4. **Column compression** (`Compress.compress`) — merges each group
   of k binary columns into one numerical column, rewriting each
   corresponding equality query into an OR-of-ranges predicate
   (Section 4 in the paper). This is lossless at the matrix level.

Then the driver **renames** generic `column_i` / `__comp_i` names to
CDISC-style names per `schema.yaml`, rewrites the SQL literals
(`= '1'` → `= 'M'`, etc.), and verifies reconstruction by solving
`M · s = b` with NumPy's least-squares solver. Success requires
full column rank and max absolute reconstruction error < 0.5.

## Extending

To add a fifth experiment, duplicate any existing folder, edit
`schema.yaml` (change `mip_base`, `hadamard_order`, compression
groups, renames), and run `bash run.sh`. The driver validates the
column budget implicitly — a mismatch surfaces as an error in the
rename pass.
