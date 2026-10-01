# generator-reconstruction-attacks

Companion code for the paper _"Schema-Driven Generation of Reconstructable
Datasets from Aggregate Releases"_, to appear at
[NordSec 2026](https://nordsec2026.dk/).

Given only a table schema, this tool automatically produces a **concrete
witness** — a synthetic table together with a typical-looking aggregate
workload — under which the sensitive column can be uniquely reconstructed.
The construction builds on and adapts the classical Dinur–Nissim
reconstruction attack to an arbitrary input schema, making the theoretical
risk concrete on data an organisation can recognise as its own.

## Contents

- `src/` — generator core: MIP-guided construction, soundness invariants
  on query size and pairwise overlap, Hadamard/Sylvester specialisation
  at `(p = 1/2, c = 1/4)`, column compression, decoy embedding.
- `main.py` — command-line entry point.
- `experiments/` — reproduction runners and results across nine schemas
  drawn from three industry standards (CDISC SDTM/ADaM, HR Open, SDMX).
- `examples/` — sample fully- and partially-reconstructable datasets.
- `webapp/` — public showcase site: a plain-language explanation of the
  risk, an interactive walkthrough, and downloadable reconstructable
  datasets in CDISC ADaM, OMOP and Swedish register formats. See
  [`webapp/README.md`](webapp/README.md).

## Getting started

The recommended path is to open the project in VS Code and let it
build the supplied [`.devcontainer/`](.devcontainer/) — you get a Python
3.12 environment with GLPK, all tool dependencies, and all
privacy-metrics dependencies installed. See _Reproducing the paper
results_ below.

If you prefer a manual install:

```bash
apt install glpk-utils                       # LP/MIP solver
pip install -r requirements.txt              # tool dependencies
pip install -r requirements-eval.txt         # privacy-metrics deps (optional)
```

Or build the Docker image directly:

```bash
chmod +x setup.sh
./setup.sh
```

## Usage

```bash
python main.py --number-of-records NUMBER_OF_RECORDS [OPTIONS]
```

### Required arguments

- `--number-of-records N` — number of records to generate in the table.

### Optional arguments

#### Table generation parameters
- `--population-value FLOAT` — fraction `p` of records each query
  involves (default: `0.5`).
- `--communality-value FLOAT` — fraction `c` of records any two queries
  share (default: `0.25`).
- `--titles [TITLES ...]` — initial column titles.
- `--new-titles [NEW_TITLES ...]` — additional column titles to add.
- `--sensitive-column NAME` — name of the sensitive column (default
  depends on dataset).
- `--seed INT` — RNG seed for reproducibility.
- `--number-of-decoys INT` — number of decoy rows to embed (default: `0`).

#### Hadamard construction
- `--hadamard-order INT` — construct a Hadamard matrix of the specified
  order in place of MIP (available when `(p, c) = (1/2, 1/4)` and
  `n` is a multiple of 4).

#### Column compression
- `--columns-to-compress [COLUMNS ...]` — list of columns to compress
  (repeatable).
- `--compressed-title TITLE` — output title for the compressed column
  (default: `column_compressed`).
- `--interval-length LENGTH` — interval length for numeric compression.
- `--start-date YYYY-MM-DD` — anchor date for date-based compression.

#### Logging
- `--level LEVEL` — logging level (`DEBUG`, `INFO`, `CREATION`; default
  `INFO`).
- `--log-file PATH` — path to a log file.

### Examples

Generate a small reconstructable table with the default parameters:

```bash
python main.py --number-of-records 8
```

Generate a table of size 16 with non-default `(p, c)`:

```bash
python main.py --number-of-records 16 --level creation \
    --population-value 0.625 --communality-value 0.375
```

Embed decoy rows for a partially-reconstructable table:

```bash
python main.py --number-of-records 20 --number-of-decoys 5 \
    --population-value 0.5 --communality-value 0.25
```

Reproduce a specific run:

```bash
python main.py --number-of-records 16 --seed 42 \
    --population-value 0.625 --communality-value 0.375
```

## Reproducing the paper results

Two top-level scripts in [`scripts/`](scripts/) reproduce the paper's
results and print a clear success/failure summary. The easiest path is
to open the project in VS Code with the supplied
[`.devcontainer/`](.devcontainer/) — VS Code will build the container,
install everything, and drop you into a shell where the scripts are
ready to run.

### Table generation (~1–5 min)

```bash
bash scripts/reproduce_generation.sh
```

Runs the tool on nine schemas drawn from three industry standards
(CDISC SDTM/ADaM, HR Open, SDMX / Eurostat SILC). Every schema should
end with `reconstructed : EXACT`. Per-run logs land under `logs/`.

### Privacy-metrics evaluation (~1 hour)

The privacy-metrics stack (Anonymeter, synthcity, PyTorch, XGBoost) is
heavy, so it is **not** installed in the base devcontainer. Install it
once with:

```bash
bash scripts/install_eval_deps.sh      # ~5-15 min, one-time
```

Then run the evaluation:

```bash
bash scripts/reproduce_privacy_metrics.sh
```

For each schema, generates the decoy-augmented dataset (10 %
reconstructable core + 90 % decoys) and evaluates it with three
state-of-the-art privacy metrics: **Anonymeter**, **synthcity**
(`DataLeakageXGB`, `IdentifiabilityScore`), and a **Privacy-Meter**-style
Random-Forest attribute-inference attack. Every metric should report
near-zero risk despite the fact that our tool can reconstruct the
sensitive column exactly. Aggregate results land in
`experiments/anonymeter_results.md` and
`experiments/privacy_metrics_results.md`.

### Comparing against checked-in results

Both scripts overwrite the outputs under `experiments/*/output` and
`experiments/*/output_decoys`. To check that your re-run matches the
committed reference:

```bash
git diff experiments/
```

### Individual runners

The `experiments/` directory also exposes finer-grained scripts if you
want to run one piece at a time: `experiments/<NN_name>/run.sh`,
`experiments/run_all.sh`, `experiments/run_decoys_all.sh`,
`experiments/run_anonymeter_all.sh`,
`experiments/run_privacy_metrics_all.sh`, `experiments/benchmark.sh`
(Sylvester-vs-MIP scaling sweep).

## License

Mozilla Public License 2.0. See [LICENSE](LICENSE).
