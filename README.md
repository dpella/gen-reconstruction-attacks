# generator-reconstruction-attacks

Companion code for the paper _"Schema-Driven Generation of Reconstructable
Datasets from Aggregate Releases"_.

Given only a table schema, this tool automatically produces a **concrete
witness** — a synthetic table together with a typical-looking aggregate
workload — under which the sensitive column can be uniquely reconstructed.
The construction operationalises the classical Dinur–Nissim reconstruction
result at the level of an arbitrary input schema, making the theoretical
risk concrete on data an organisation can recognise as its own.

## Contents

- `src/` — generator core: MIP-guided construction, soundness invariants
  on query size and pairwise overlap, Hadamard/Sylvester specialisation
  at `(p = 1/2, c = 1/4)`, column compression, decoy embedding.
- `main.py` — command-line entry point.
- `experiments/` — reproduction runners and results across nine schemas
  drawn from three industry standards (CDISC SDTM/ADaM, HR Open, SDMX).
- `examples/` — sample fully- and partially-reconstructable datasets.

## Requirements

The tool relies on the GLPK linear-programming solver:

```bash
apt install glpk-utils
```

Python dependencies:

```bash
pip install -r requirements.txt
```

Alternatively, use the provided [Dockerfile](Dockerfile):

```bash
chmod +x setup.sh
./setup.sh
```

or open the project in VS Code with the supplied
[`.devcontainer/`](.devcontainer/) configuration.

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

The [`experiments/`](experiments/) directory contains everything needed
to reproduce the results reported in the paper.

```bash
cd experiments
./run_all.sh
```

Per-experiment READMEs describe individual scenarios (SDTM VS,
ADaM ADSL/ADLB/ADPC, HR Open, SDMX / Eurostat SILC). Result CSVs and
Markdown tables are checked in; scripts overwrite them on re-run.

Additional runners are available:

- `run_privacy_metrics_all.sh` — evaluate Anonymeter, Synthcity, and
  Privacy Meter against generated datasets.
- `run_anonymeter_all.sh` — Anonymeter-only sweep.
- `run_decoys_all.sh` — partially-reconstructable variants with decoy
  embedding.
- `benchmark.sh` — timing / scaling benchmark (Sylvester vs. MIP).

## License

Mozilla Public License 2.0. See [LICENSE](LICENSE).
