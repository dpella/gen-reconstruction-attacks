"""
Healthcare schema templates for the web demo.

The generator needs exactly `n - 1` raw binary "query columns" for a table of
`n` reconstructable records (one per released query, plus the all-records
query added by the Hadamard expansion). The experiment schemas in
`experiments/` hard-code that budget for one fixed `n`; here each template
instead lists *attributes* and `fit()` packs them into the budget for any
supported `n`:

  * numeric attributes become compression groups (k bits -> 2^k bins,
    released as range predicates). The tool bins on integers; each column's
    values and SQL bounds are then mapped by `offset + interval * x`, which
    preserves every predicate and allows fractional bins (e.g. 0.4 mmol/L),
  * categorical attributes each consume one column and are placed last,
    so that `column_{n-3}` (the column the decoy construction negates) is
    always the 4-valued race / country / region attribute.

Static attributes are taken first, then each repeated block (visits, ICU
days, follow-ups, ...) label by label until the budget is exhausted. Any
leftover (< one group) is filled with extra categorical flags.

The templates themselves live in `standards/`: each follows a published
one-row-per-person standard (CDISC ADaM ADSL, OMOP + OHDSI FeatureExtraction,
Swedish register extracts), with its official variable names and codes.
"""
from __future__ import annotations

import re
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

# The MIP solver builds a 16-record core; each Hadamard (Sylvester) doubling
# then doubles it: n = MIP_BASE * 2^(hadamard_order - 1).
MIP_BASE = 16
# 16: the solver-only table used by the walkthrough; each schema's downloads
# use its own `download_n`.
SUPPORTED_N = [16, 32, 64, 128, 256, 512]
SEED = 42


@dataclass
class Numeric:
    name: str
    bits: int
    interval: float  # released bin width
    unit: str
    description: str
    # Added to generated values (and to the SQL range bounds) so bins start
    # at a plausible value; a constant shift preserves every predicate.
    offset: float = 0
    # Released precision. Bin edges must be multiples of 10^-decimals, so
    # flooring keeps every value inside its bin (checked by _validate).
    decimals: int = 0
    # Short plain-language name for the walkthrough (defaults to `name`).
    label: str = ""

    @property
    def range_text(self) -> str:
        lo = Decimal(str(self.offset))
        hi = lo + Decimal(str(self.interval)) * 2 ** self.bits
        return f"{_fmt(lo)}–{_fmt(hi)} {self.unit}".strip()


def _fmt(x: Decimal) -> str:
    return format(x.normalize(), "f")


def N(name: str, bits: int, interval: float, unit: str, description: str,
      offset: float = 0, dec: int = 0, label: str = "") -> Numeric:
    return Numeric(name, bits, interval, unit, description, offset, dec, label)


@dataclass
class Block:
    """Attributes measured repeatedly, once per label (visit, day, ...)."""
    kind: str
    labels: List[str]
    attrs: List[Numeric]


@dataclass
class Categorical:
    name: str
    values: Dict[str, str]  # raw tool value ('1', '0', '2', '3') -> label
    description: str
    label: str = ""


def flag(name: str, description: str) -> Categorical:
    return Categorical(name, {"1": "Y", "0": "N", "2": "N", "3": "N"}, description)


@dataclass
class Sensitive:
    name: str
    low: float
    high: float
    unit: str
    description: str
    decimals: int = 0
    label: str = ""  # readable name for the walkthrough (defaults to `name`)


@dataclass
class SchemaTemplate:
    id: str
    category: str  # key of CATEGORIES
    title: str
    standard: str
    domain: str
    summary: str
    story: str
    sensitive: Sensitive
    static: List[Numeric]
    blocks: List[Block]
    # Final three categorical columns: [.., race-like (4-valued), ..].
    # The middle one lands on column_{n-3}; its '0', '2', '3' labels must be
    # pairwise distinct so the decoy-mode negation query excludes decoys.
    tail: List[Categorical]
    extras: List[Categorical] = field(default_factory=list)
    # Where the schema's structure is taken from: (label, url) pairs.
    sources: List[Tuple[str, str]] = field(default_factory=list)
    # Size of the downloadable datasets: as many records as the standard's
    # independent variables support (n - 1 queries are needed).
    download_n: int = 64
    # Adds the standard's derived variables (IDs, groupings, dates, ...) to a
    # released row: derive(row, rng, index, is_decoy) -> {name: value}.
    # Must also supply any standard variable that the fitter left out at a
    # small n. Derived columns are never queried.
    derive: Optional[Callable] = None
    # The standard's column order (columns absent at a given n are skipped).
    column_order: Optional[List[str]] = None
    # Shown in the "How it works" walkthrough (all schemas are downloadable).
    featured: bool = False
    # Extra files shipped with each dataset: extra_files(header) -> {name: text}.
    extra_files: Optional[Callable] = None


@dataclass
class Column:
    name: str
    kind: str  # "numeric" | "categorical"
    description: str
    raw_columns: List[str]
    detail: str
    label: str = ""


@dataclass
class FittedSchema:
    template: SchemaTemplate
    n: int
    columns: List[Column]
    # released numeric column -> (offset, interval, decimals): released value
    # = offset + interval * tool value, floored to `decimals`.
    transforms: Dict[str, Tuple[float, float, int]]
    config: dict  # driver.py-compatible schema config
    repetitions: Dict[str, int]  # block kind -> labels used


SQL_NAME = re.compile(r"^[^\W\d]\w*$")


def _validate(template, numeric, categorical):
    """Catch schema mistakes that would silently corrupt the published SQL."""
    for name in [a.name for a in numeric + categorical] + [template.sensitive.name]:
        assert SQL_NAME.match(name), f"{template.id}: {name!r} is not a plain SQL identifier"
    for attr in numeric:
        step = Decimal(10) ** attr.decimals
        for what in ("offset", "interval"):
            x = Decimal(str(getattr(attr, what))) * step
            assert x == x.to_integral_value(), (
                f"{template.id}: {attr.name}: {what} {getattr(attr, what)} is finer than "
                f"{attr.decimals} decimals, so rounding could move values across bins"
            )
    for attr in categorical:
        v = attr.values
        assert v["1"] not in (v["0"], v["2"], v["3"]), (
            f"{template.id}: {attr.name}: the 'yes' label {v['1']!r} is shared with a 'no' value"
        )
    neg = template.tail[1].values
    assert len({neg["1"], neg["0"], neg["2"], neg["3"]}) == 4, (
        f"{template.id}: {template.tail[1].name} needs four distinct labels (decoy negation)"
    )


def fit(template: SchemaTemplate, n: int) -> FittedSchema:
    if n not in SUPPORTED_N:
        raise ValueError(f"n must be one of {SUPPORTED_N}")
    assert len(template.tail) == 3

    budget = n - 1
    free = budget - len(template.tail)
    numeric: List[Numeric] = []

    for attr in template.static:
        if attr.bits <= free:
            numeric.append(attr)
            free -= attr.bits

    repetitions: Dict[str, int] = {}
    for block in template.blocks:
        used = 0
        for label in block.labels:
            if free < min(a.bits for a in block.attrs):
                break
            added = False
            for attr in block.attrs:
                if attr.bits <= free:
                    numeric.append(Numeric(
                        f"{attr.name}_{label}", attr.bits, attr.interval, attr.unit,
                        f"{attr.description} ({block.kind} {label.replace('_', ' ')})",
                        attr.offset, attr.decimals,
                        f"{attr.label or attr.name} ({block.kind} {label.replace('_', ' ')})",
                    ))
                    free -= attr.bits
                    added = True
            used += added
        repetitions[block.kind] = used

    if free > len(template.extras):
        raise ValueError(
            f"{template.id}: {free} unused columns at n={n}; add more "
            "repetitions, attributes or extra flags"
        )
    categorical = template.extras[:free] + template.tail

    columns: List[Column] = []
    groups = []
    binary_rename = {}
    col = 0
    for attr in numeric:
        raw = [f"column_{col + j}" for j in range(attr.bits)]
        col += attr.bits
        groups.append({"name": attr.name, "columns": raw, "interval": 1})
        columns.append(Column(
            attr.name, "numeric", attr.description, raw,
            f"{2 ** attr.bits} bins × {_fmt(Decimal(str(attr.interval)))} {attr.unit} ({attr.range_text})",
            attr.label or attr.name,
        ))
    for attr in categorical:
        raw = f"column_{col}"
        col += 1
        binary_rename[raw] = {"name": attr.name, "values": dict(attr.values)}
        labels = sorted(set(attr.values.values()), key=list(attr.values.values()).index)
        columns.append(Column(attr.name, "categorical", attr.description, [raw], " / ".join(labels),
                              attr.label or attr.name))
    assert col == budget, (template.id, n, col, budget)
    _validate(template, numeric, categorical)
    names = [c.name for c in columns] + [template.sensitive.name]
    assert len(names) == len(set(names)), f"{template.id}: duplicate column names"

    hadamard_order = (n // MIP_BASE).bit_length()  # MIP_BASE * 2^(k-1) = n; k = 1 means no expansion
    config = {
        "name": f"{template.id}_n{n}",
        "n_records": n,
        "seed": SEED,
        "mip_base": MIP_BASE,
        "hadamard_order": hadamard_order,
        "population_value": 0.5,
        "communality_value": 0.25,
        "log_level": "WARNING",
        "sensitive_column": template.sensitive.name,
        "compression_groups": groups,
        "binary_rename": binary_rename,
    }
    transforms = {a.name: (a.offset, a.interval, a.decimals) for a in numeric}
    return FittedSchema(template, n, columns, transforms, config, repetitions)


CATEGORIES = {
    "pharma": {
        "title": "Pharma",
        "standard": "CDISC ADaM",
        "description": (
            "Clinical-trial analysis data in CDISC ADaM, the format submitted to EMA "
            "and FDA. ADSL is the standard one-row-per-subject dataset behind every "
            "study report's demographics and baseline tables; under the EU Clinical "
            "Trials Regulation (536/2014), trial results are published in CTIS."
        ),
    },
    "healthcare": {
        "title": "Healthcare",
        "standard": "OMOP CDM · OHDSI",
        "description": (
            "Real-world data in the OMOP common data model, as analysed in the "
            "European networks EHDEN and DARWIN EU (EMA): a study cohort with the "
            "standard OHDSI FeatureExtraction covariates, one row per person. "
            "Network studies share only aggregates, typically suppressing counts "
            "below 5, and the European Health Data Space lets anyone request answers "
            "in 'anonymised statistical format'."
        ),
    },
    "public": {
        "title": "Public sector · Sweden",
        "standard": "Swedish national registers",
        "description": (
            "Extracts from Sweden's national quality registers and SCB's LISA, with "
            "their official variable names and codes. Aggregates are published "
            "openly (Vården i siffror, register annual reports, SCB statistics), and "
            "under the principle of public access (offentlighetsprincipen) more can "
            "be requested."
        ),
    },
}


def _templates():
    from .standards.adsl import ADSL_PILOT, ADSL_T2D
    from .standards.omop_fe import OMOP_COVID, OMOP_HIV, OMOP_T2DM
    from .standards.sweden import LISA, NDR, RIKSHIA

    return {t.id: t for t in [ADSL_PILOT, ADSL_T2D, OMOP_T2DM, OMOP_HIV, OMOP_COVID, RIKSHIA, NDR, LISA]}


TEMPLATES: Dict[str, SchemaTemplate] = _templates()
# Two per category for the walkthrough, chosen for each audience.
for _id in ("adsl_alzheimer", "adsl_diabetes", "omop_t2dm", "omop_hiv", "se_ndr", "se_lisa"):
    TEMPLATES[_id].featured = True


def get(schema_id: str) -> Optional[SchemaTemplate]:
    return TEMPLATES.get(schema_id)
