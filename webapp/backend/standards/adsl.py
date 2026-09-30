"""
CDISC ADaM ADSL (subject-level analysis dataset), modelled on the CDISC pilot
study CDISCPILOT01 (xanomeline in mild-to-moderate Alzheimer's disease), whose
ADSL has 49 variables. Variable names, order, controlled terms and codes
(RACEN, TRT01PN, AVGDD, completion flags by VISNUMEN, DCDECOD/DCSREAS pairs,
pooled site 900) follow that dataset.

Released (queried) variables are the independent baseline characteristics
that study reports tabulate subgroups by. Everything that ADaM derives from
them is derived here the same way, so rows are internally consistent. Four
baseline covariates (ACTOTBL, SYSBPBL, DIABPBL, PULSEBL) are sponsor-added
ADSL variables following the *BL convention and the pilot's ADADAS/ADVS
PARAMCDs; they are not in the pilot ADSL itself.
"""
from __future__ import annotations

import datetime as dt

from ..schemas import Categorical, N, SchemaTemplate, Sensitive

SDTMIG = "https://www.cdisc.org/standards/foundational/adam"
PILOT = "https://github.com/RConsortium/submissions-pilot1-to-fda"

TRT = Categorical(
    "TRT01P",
    {"1": "Xanomeline High Dose", "0": "Placebo", "2": "Xanomeline Low Dose", "3": "Placebo"},
    "Planned treatment for period 01",
)
RACE = Categorical(
    "RACE",
    {"1": "WHITE", "0": "BLACK OR AFRICAN AMERICAN", "2": "BLACK OR AFRICAN AMERICAN",
     "3": "AMERICAN INDIAN OR ALASKA NATIVE"},
    "Race",
)
# Four distinct labels: this column carries the decoy-mode negation query.
SITEGR1 = Categorical(
    "SITEGR1", {"1": "701", "0": "710", "2": "704", "3": "900"},
    "Pooled site group 1 (900 = pooled small sites)",
)

TRT_N = {"Placebo": 0, "Xanomeline Low Dose": 54, "Xanomeline High Dose": 81}
RACE_N = {"WHITE": 1, "BLACK OR AFRICAN AMERICAN": 2, "AMERICAN INDIAN OR ALASKA NATIVE": 6}
POOLED_SITES = ["702", "706", "707", "711", "714", "715", "717"]
# (DCDECOD, DCSREAS, weight) for discontinued subjects, as in the pilot.
DISCONTINUATION = [
    ("ADVERSE EVENT", "Adverse Event", 92), ("WITHDRAWAL BY SUBJECT", "Withdrew Consent", 27),
    ("STUDY TERMINATED BY SPONSOR", "Sponsor Decision", 7), ("LACK OF EFFICACY", "Lack of Efficacy", 4),
    ("PROTOCOL VIOLATION", "Protocol Violation", 3), ("PROTOCOL VIOLATION", "I/E Not Met", 3),
    ("PHYSICIAN DECISION", "Physician Decision", 3), ("DEATH", "Death", 3),
    ("LOST TO FOLLOW-UP", "Lost to Follow-up", 2),
]
# Last visit reached -> approximate days on treatment.
VISIT_DAYS = {4: 14, 5: 28, 6: 42, 7: 56, 8: 70, 9: 84, 10: 112, 11: 140}


def _iso(d: dt.date) -> str:
    return d.isoformat()


def derive(r, rng, i, is_decoy):
    out = {}

    def need(name, make):
        if name not in r:
            out[name] = make()
            r[name] = out[name]

    # Standard variables the fitter may have left out at small n.
    need("TRT01P", lambda: rng.choice(list(TRT_N)))
    need("RACE", lambda: "WHITE")
    need("ETHNIC", lambda: "NOT HISPANIC OR LATINO")
    need("SITEGR1", lambda: rng.choice(["701", "704", "710", "900"]))
    need("EFFFL", lambda: "Y")
    need("COMP24FL", lambda: rng.choice(["Y", "N"]))
    need("DURDIS", lambda: f"{rng.uniform(12, 150):.1f}")

    site = r["SITEGR1"] if r["SITEGR1"] != "900" else rng.choice(POOLED_SITES)
    subjid = str(1001 + i)
    trt = r["TRT01P"]
    age = int(float(r["AGE"]))
    height, weight = float(r["HEIGHTBL"]), float(r["WEIGHTBL"])
    bmi = round(weight / (height / 100) ** 2, 1)
    durdis = float(r["DURDIS"])

    visit1 = dt.date(2012, 8, 1) + dt.timedelta(days=rng.randint(0, 800))
    trtsdt = visit1 + dt.timedelta(days=rng.randint(1, 14))
    completed = r["COMP24FL"] == "Y"
    if completed:
        visnumen, trtdurd = 12, rng.randint(168, 200)
        dcdecod, dcsreas, eosstt = "COMPLETED", "", "COMPLETED"
    else:
        visnumen = rng.randint(4, 11)
        trtdurd = VISIT_DAYS[visnumen] + rng.randint(-6, 6)
        dcdecod, dcsreas, _ = rng.choices(DISCONTINUATION, weights=[w for *_, w in DISCONTINUATION])[0]
        eosstt = "DISCONTINUED"
    trtedt = trtsdt + dt.timedelta(days=trtdurd - 1)
    rfendt = trtedt + dt.timedelta(days=rng.randint(0, 14))
    avgdd = {"Placebo": 0.0, "Xanomeline Low Dose": 54.0}.get(trt) or round(rng.uniform(54, 78.6), 1)

    out.update({
        "STUDYID": "CDISCPILOT01",
        "USUBJID": f"01-{site}-{subjid}",
        "SUBJID": subjid,
        "SITEID": site,
        "ARM": trt,
        "TRT01PN": TRT_N[trt],
        "TRT01A": trt,
        "TRT01AN": TRT_N[trt],
        "TRTSDT": _iso(trtsdt),
        "TRTEDT": _iso(trtedt),
        "TRTDURD": trtdurd,
        "AVGDD": f"{avgdd:.1f}",
        "CUMDOSE": round(avgdd * trtdurd),
        "AGEGR1": "<65" if age < 65 else ("65-80" if age <= 80 else ">80"),
        "AGEGR1N": 1 if age < 65 else (2 if age <= 80 else 3),
        "AGEU": "YEARS",
        "RACEN": RACE_N[r["RACE"]],
        "SAFFL": "Y",
        "ITTFL": "Y",
        "COMP8FL": "Y" if completed or visnumen >= 8 else "N",
        "COMP16FL": "Y" if completed or visnumen >= 10 else "N",
        "DISCONFL": "" if completed else "Y",
        "DSRAEFL": "Y" if dcdecod == "ADVERSE EVENT" else "",
        "DTHFL": "Y" if dcdecod == "DEATH" else "",
        "BMIBL": f"{bmi:.1f}",
        "BMIBLGR1": "<25" if bmi < 25 else ("25-<30" if bmi < 30 else ">=30"),
        "DISONSDT": _iso(visit1 - dt.timedelta(days=round(durdis * 30.4375))),
        "DURDSGR1": "<12" if durdis < 12 else ">=12",
        "VISIT1DT": _iso(visit1),
        "RFSTDTC": _iso(trtsdt),
        "RFENDTC": _iso(rfendt),
        "VISNUMEN": visnumen,
        "RFENDT": _iso(rfendt),
        "DCDECOD": dcdecod,
        "EOSSTT": eosstt,
        "DCSREAS": dcsreas,
    })
    return out


# The pilot ADSL's variable order; sponsor-added baselines before MMSETOT.
COLUMN_ORDER = [
    "STUDYID", "USUBJID", "SUBJID", "SITEID", "SITEGR1", "ARM", "TRT01P", "TRT01PN",
    "TRT01A", "TRT01AN", "TRTSDT", "TRTEDT", "TRTDURD", "AVGDD", "CUMDOSE", "AGE",
    "AGEGR1", "AGEGR1N", "AGEU", "RACE", "RACEN", "SEX", "ETHNIC", "SAFFL", "ITTFL",
    "EFFFL", "COMP8FL", "COMP16FL", "COMP24FL", "DISCONFL", "DSRAEFL", "DTHFL", "BMIBL",
    "BMIBLGR1", "HEIGHTBL", "WEIGHTBL", "EDUCLVL", "DISONSDT", "DURDIS", "DURDSGR1",
    "VISIT1DT", "RFSTDTC", "RFENDTC", "VISNUMEN", "RFENDT", "DCDECOD", "EOSSTT", "DCSREAS",
    "ACTOTBL", "SYSBPBL", "DIABPBL", "PULSEBL", "MMSETOT",
]

ADSL_PILOT = SchemaTemplate(
    id="adsl_alzheimer",
    category="pharma",
    title="Subject-level trial data (ADSL)",
    standard="CDISC ADaM · ADSL",
    domain="Alzheimer's disease trial (CDISC pilot study)",
    summary=(
        "The subject-level analysis dataset of a 3-arm Alzheimer's trial, with the "
        "same 49 variables, names, codes and derivations as the CDISC pilot study "
        "(CDISCPILOT01), plus four baseline covariates."
    ),
    story=(
        "Suppose the sponsor shares the subject-level dataset with researchers, but "
        "without the baseline MMSE score, while the study report gives the mean "
        "baseline MMSE for broad subgroups: by treatment arm, site, sex, race, age, "
        "height, weight, education, disease duration and baseline vital signs."
    ),
    sensitive=Sensitive(
        "MMSETOT", 10, 24, "points",
        "Mini-Mental State Examination total at baseline (cognitive impairment)",
    ),
    static=[
        N("AGE", 3, 5, "years", "Age", 50),
        N("HEIGHTBL", 2, 8, "cm", "Baseline height", 155, 1),
        N("WEIGHTBL", 3, 6, "kg", "Baseline weight", 50, 1),
        N("EDUCLVL", 2, 5, "years", "Years of education", 4),
        N("DIABPBL", 2, 7, "mmHg", "Baseline diastolic BP (sponsor-added)", 62),
        N("DURDIS", 3, 20, "months", "Duration of disease", 6, 1),
        N("ACTOTBL", 3, 5, "points", "Baseline ADAS-Cog(11) total (sponsor-added)", 10),
        N("SYSBPBL", 3, 8, "mmHg", "Baseline systolic BP (sponsor-added)", 112),
        N("PULSEBL", 3, 5, "beats/min", "Baseline pulse rate (sponsor-added)", 54),
    ],
    blocks=[],
    tail=[
        Categorical("SEX", {"1": "M", "0": "F", "2": "F", "3": "F"}, "Sex"),
        SITEGR1,
        Categorical("EFFFL", {"1": "Y", "0": "N", "2": "N", "3": "N"}, "Efficacy population flag"),
    ],
    extras=[
        TRT,
        RACE,
        Categorical(
            "ETHNIC",
            {"1": "HISPANIC OR LATINO", "0": "NOT HISPANIC OR LATINO",
             "2": "NOT HISPANIC OR LATINO", "3": "NOT HISPANIC OR LATINO"},
            "Ethnicity",
        ),
        Categorical("COMP24FL", {"1": "Y", "0": "N", "2": "N", "3": "N"}, "Completers of week 24 population flag"),
    ],
    sources=[
        ("CDISC ADaM — ADSL", SDTMIG),
        ("CDISC pilot study ADSL (R Consortium submission)", PILOT),
    ],
    download_n=32,
    derive=derive,
    column_order=COLUMN_ORDER,
)


# ------------------------------------------------ type 2 diabetes trial

COUNTRY = Categorical(
    "COUNTRY", {"1": "SWE", "0": "DEU", "2": "POL", "3": "ESP"},
    "Country (ISO 3166-1 alpha-3, as in SDTM DM)",
)
T2D_TRT = Categorical(
    "TRT01P", {"1": "Drug X 10 mg", "0": "Placebo", "2": "Drug X 5 mg", "3": "Placebo"},
    "Planned treatment for period 01",
)
T2D_TRT_N = {"Placebo": 0, "Drug X 5 mg": 5, "Drug X 10 mg": 10}
T2D_SITES = {"SWE": ["101", "102"], "DEU": ["201", "202", "203"], "POL": ["301", "302"], "ESP": ["401", "402"]}


def derive_t2d(r, rng, i, is_decoy):
    out = {}

    def need(name, make):
        if name not in r:
            out[name] = make()
            r[name] = out[name]

    need("TRT01P", lambda: rng.choice(list(T2D_TRT_N)))
    need("RACE", lambda: "WHITE")
    need("ETHNIC", lambda: "NOT HISPANIC OR LATINO")
    need("COMP26FL", lambda: rng.choice(["Y", "N"]))
    need("PPROTFL", lambda: "Y")

    site = rng.choice(T2D_SITES[r["COUNTRY"]])
    subjid = f"{site}{1001 + i:04d}"
    trt = r["TRT01P"]
    age = int(float(r["AGE"]))
    height, weight = float(r["HEIGHTBL"]), float(r["WEIGHTBL"])
    bmi = round(weight / (height / 100) ** 2, 1)
    randdt = dt.date(2021, 3, 1) + dt.timedelta(days=rng.randint(0, 540))
    completed = r["COMP26FL"] == "Y"
    trtdurd = rng.randint(180, 190) if completed else rng.randint(14, 170)
    trtedt = randdt + dt.timedelta(days=trtdurd - 1)
    dcdecod, dcsreas, _ = ("COMPLETED", "", 0) if completed else rng.choices(
        DISCONTINUATION, weights=[w for *_, w in DISCONTINUATION])[0]
    out.update({
        "STUDYID": "T2D-EU-301",
        "USUBJID": f"T2D-EU-301-{subjid}",
        "SUBJID": subjid,
        "SITEID": site,
        "ARM": trt,
        "ARMCD": {"Placebo": "PBO", "Drug X 5 mg": "X5", "Drug X 10 mg": "X10"}[trt],
        "TRT01PN": T2D_TRT_N[trt],
        "TRT01A": trt,
        "TRT01AN": T2D_TRT_N[trt],
        "RANDDT": randdt.isoformat(),
        "TRTSDT": randdt.isoformat(),
        "TRTEDT": trtedt.isoformat(),
        "TRTDURD": trtdurd,
        "AGEGR1": "<65" if age < 65 else ">=65",
        "AGEU": "YEARS",
        "SAFFL": "Y",
        "ITTFL": "Y",
        "BMIBL": f"{bmi:.1f}",
        "BMIBLGR1": "<25" if bmi < 25 else ("25-<30" if bmi < 30 else ">=30"),
        "EOSSTT": "COMPLETED" if completed else "DISCONTINUED",
        "DCDECOD": dcdecod,
        "DCSREAS": dcsreas,
    })
    return out


ADSL_T2D = SchemaTemplate(
    id="adsl_diabetes",
    category="pharma",
    title="Diabetes trial (ADSL)",
    standard="CDISC ADaM · ADSL",
    domain="Phase 3 type 2 diabetes trial, 4 EU countries",
    summary=(
        "The subject-level analysis dataset of a placebo-controlled type 2 diabetes "
        "trial run in Sweden, Germany, Poland and Spain: ADSL core variables and "
        "derivations as in the CDISC pilot, with the baseline covariates (*BL) a "
        "diabetes study report tabulates."
    ),
    story=(
        "Suppose the sponsor shares the subject-level dataset with researchers, but "
        "without baseline HbA1c, while the study report and the CTIS results summary "
        "give mean baseline HbA1c by treatment arm, country, sex, age, weight, blood "
        "pressure, kidney function and diabetes duration."
    ),
    sensitive=Sensitive("HBA1CBL", 7.0, 10.5, "%", "Baseline HbA1c (%)", decimals=1),
    static=[
        N("AGE", 3, 6, "years", "Age", 30),
        N("HEIGHTBL", 2, 8, "cm", "Baseline height", 155, 1),
        N("WEIGHTBL", 3, 7, "kg", "Baseline weight", 60, 1),
        N("DIABPBL", 2, 7, "mmHg", "Baseline diastolic BP", 62),
        N("SYSBPBL", 3, 8, "mmHg", "Baseline systolic BP", 112),
        N("EGFRBL", 3, 10, "mL/min/1.73m²", "Baseline eGFR", 30),
        N("DIABDURY", 3, 2, "years", "Duration of diabetes", 1, 1),
        N("FPGBL", 3, 1, "mmol/L", "Baseline fasting plasma glucose", 6, 1),
        N("LDLBL", 2, 0.6, "mmol/L", "Baseline LDL cholesterol", 1.4, 1),
    ],
    blocks=[],
    tail=[
        Categorical("SEX", {"1": "M", "0": "F", "2": "F", "3": "F"}, "Sex"),
        COUNTRY,
        Categorical("PPROTFL", {"1": "Y", "0": "N", "2": "N", "3": "N"}, "Per-protocol population flag"),
    ],
    extras=[
        T2D_TRT,
        Categorical("COMP26FL", {"1": "Y", "0": "N", "2": "N", "3": "N"}, "Completers of week 26 flag"),
        Categorical("RACE", {"1": "WHITE", "0": "ASIAN", "2": "BLACK OR AFRICAN AMERICAN", "3": "ASIAN"}, "Race"),
        Categorical(
            "ETHNIC",
            {"1": "HISPANIC OR LATINO", "0": "NOT HISPANIC OR LATINO",
             "2": "NOT HISPANIC OR LATINO", "3": "NOT HISPANIC OR LATINO"},
            "Ethnicity",
        ),
    ],
    sources=[
        ("CDISC ADaM — ADSL", SDTMIG),
        ("CDISC pilot study ADSL (R Consortium submission)", PILOT),
    ],
    download_n=32,
    derive=derive_t2d,
    column_order=[
        "STUDYID", "USUBJID", "SUBJID", "SITEID", "COUNTRY", "ARM", "ARMCD", "TRT01P", "TRT01PN",
        "TRT01A", "TRT01AN", "RANDDT", "TRTSDT", "TRTEDT", "TRTDURD", "AGE", "AGEGR1", "AGEU",
        "SEX", "RACE", "ETHNIC", "SAFFL", "ITTFL", "PPROTFL", "COMP26FL", "EOSSTT", "DCDECOD",
        "DCSREAS", "HEIGHTBL", "WEIGHTBL", "BMIBL", "BMIBLGR1", "SYSBPBL", "DIABPBL", "EGFRBL",
        "LDLBL", "FPGBL", "DIABDURY", "HBA1CBL",
    ],
)
