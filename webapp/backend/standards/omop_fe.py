"""
OMOP CDM v5.4 cohort + OHDSI FeatureExtraction covariates, one row per cohort
subject (as PatientLevelPrediction/CohortMethod analysts see them after
pivoting the sparse covariate table).

Covariate IDs and names follow FeatureExtraction v3.14 (analysisId scheme:
conceptId*1000 + analysisId; measurement values conceptId*1e6 +
(unitConceptId % 1000)*1000 + 706; concept-less covariates 1000 + analysisId).
Concept IDs were checked against the OHDSI vocabulary (api.ohdsi.org). Risk
scores are derived from the released condition covariates with
FeatureExtraction's own category weights (CharlsonIndex.sql, Chads2.sql,
Chads2Vasc.sql), and age groups from age, so rows are consistent. A
`covariate_ref.csv` (covariateId, covariateName, analysisId, conceptId) ships
with every dataset.

Columns are named `cov_<covariateId>` (SQL identifiers cannot start with a
digit); `care_site_id` (a CDM field) carries the decoy-mode negation query.
"""
from __future__ import annotations

import datetime as dt
import math

from ..schemas import Categorical, N, SchemaTemplate, Sensitive

FE = "https://github.com/OHDSI/FeatureExtraction"
CDM = "https://ohdsi.github.io/CommonDataModel/cdm54.html"
WINDOW = "during day -365 through 0 days relative to index"

# (concept_id, name) — all verified standard concepts.
CONDITIONS = {
    "t2dm": (201826, "Type 2 diabetes mellitus"),
    "htn": (320128, "Essential hypertension"),
    "hf": (316139, "Heart failure"),
    "copd": (255573, "Chronic obstructive pulmonary disease"),
    "ckd": (46271022, "Chronic kidney disease"),
    "mi": (4329847, "Myocardial infarction"),
    "cvd": (381591, "Cerebrovascular disease"),
    "pvd": (321052, "Peripheral vascular disease"),
    "af": (313217, "Atrial fibrillation"),
    "dementia": (4182210, "Dementia"),
    "depression": (440383, "Depressive disorder"),
    "obesity": (433736, "Obesity"),
    "hyperlipidemia": (432867, "Hyperlipidemia"),
    "liver": (4212540, "Chronic liver disease"),
    "aki": (197320, "Acute kidney injury"),
    "dm_retinopathy": (4174977, "Retinopathy due to diabetes mellitus"),
    "dm_neuropathy": (443730, "Disorder of nervous system due to diabetes mellitus"),
    "hiv": (439727, "Human immunodeficiency virus infection"),
    "covid": (37311061, "COVID-19"),
}
DRUGS = {
    "diabetes_drugs": (21600712, "DRUGS USED IN DIABETES"),
    "insulins": (21600713, "INSULINS AND ANALOGUES"),
    "glucose_lowering": (21600744, "BLOOD GLUCOSE LOWERING DRUGS, EXCL. INSULINS"),
    "antithrombotic": (21600960, "ANTITHROMBOTIC AGENTS"),
    "lipid": (21601853, "LIPID MODIFYING AGENTS"),
    "beta_blockers": (21601664, "BETA BLOCKING AGENTS"),
    "ras": (21601782, "AGENTS ACTING ON THE RENIN-ANGIOTENSIN SYSTEM"),
    "diuretics": (21601461, "DIURETICS"),
    "antivirals": (21603126, "ANTIVIRALS FOR SYSTEMIC USE"),
    "psychoanaleptics": (21604685, "PSYCHOANALEPTICS"),
    "opioids": (21604254, "OPIOIDS"),
    "corticosteroids": (21602722, "CORTICOSTEROIDS FOR SYSTEMIC USE"),
    "antibacterials": (21602796, "ANTIBACTERIALS FOR SYSTEMIC USE"),
    "immunosuppressants": (21603890, "IMMUNOSUPPRESSANTS"),
}
# (concept_id, name, unit_concept_id, unit_name)
MEASUREMENTS = {
    "hba1c": (3004410, "Hemoglobin A1c/Hemoglobin.total in Blood", 8554, "percent"),
    "viral_load": (3010747, "HIV 1 RNA [#/volume] (viral load) in Serum or Plasma by NAA with probe detection", 8799, "copies per milliliter"),
    "cd4": (3028167, "CD3+CD4+ (T4 helper) cells [#/volume] in Blood", 8784, "cells per microliter"),
    "bmi": (3038553, "Body mass index (BMI) [Ratio]", 9531, "kilogram per square meter"),
    "sbp": (3004249, "Systolic blood pressure", 8876, "millimeter mercury column"),
    "dbp": (3012888, "Diastolic blood pressure", 8876, "millimeter mercury column"),
    "ldl": (3028437, "Cholesterol in LDL [Mass/volume] in Serum or Plasma", 8840, "milligram per deciliter"),
    "hdl": (3007070, "Cholesterol in HDL [Mass/volume] in Serum or Plasma", 8840, "milligram per deciliter"),
    "tg": (3022192, "Triglyceride [Mass/volume] in Serum or Plasma", 8840, "milligram per deciliter"),
    "chol": (3027114, "Cholesterol [Mass/volume] in Serum or Plasma", 8840, "milligram per deciliter"),
    "hgb": (3000963, "Hemoglobin [Mass/volume] in Blood", 8713, "gram per deciliter"),
    "crp": (3020460, "C reactive protein [Mass/volume] in Serum or Plasma", 8751, "milligram per liter"),
    "creat": (3016723, "Creatinine [Mass/volume] in Serum or Plasma", 8840, "milligram per deciliter"),
    "spo2": (40762499, "Oxygen saturation in Arterial blood by Pulse oximetry", 8554, "percent"),
    "resp": (3024171, "Respiratory rate", None, None),
}
VISITS = {"inpatient": (9201, "Inpatient Visit"), "outpatient": (9202, "Outpatient Visit"), "er": (9203, "Emergency Room Visit")}


def cid_condition(key):
    return CONDITIONS[key][0] * 1000 + 210


def cid_drug(key):
    return DRUGS[key][0] * 1000 + 410


def cid_measurement(key):
    concept, _, unit, _ = MEASUREMENTS[key]
    return concept * 1_000_000 + ((unit or 0) % 1000) * 1000 + 706


def col(covariate_id):
    return f"cov_{covariate_id}"


REF = {}  # covariateId -> (name, analysisId, conceptId)


def _ref(cov_id, name, analysis, concept):
    REF[cov_id] = (name, analysis, concept)
    return cov_id


def condition(key, label):
    cid = _ref(cid_condition(key),
               f"condition_era group (ConditionGroupEraLongTerm) {WINDOW}: {CONDITIONS[key][1]}",
               210, CONDITIONS[key][0])
    return Categorical(col(cid), {"1": "1", "0": "0", "2": "0", "3": "0"}, REF[cid][0], label)


def drug(key, label):
    cid = _ref(cid_drug(key),
               f"drug_era group (DrugGroupEraLongTerm) {WINDOW}: {DRUGS[key][1]}",
               410, DRUGS[key][0])
    return Categorical(col(cid), {"1": "1", "0": "0", "2": "0", "3": "0"}, REF[cid][0], label)


def procedure(concept, name, label):
    cid = _ref(concept * 1000 + 502, f"procedure_occurrence {WINDOW}: {name}", 502, concept)
    return Categorical(col(cid), {"1": "1", "0": "0", "2": "0", "3": "0"}, REF[cid][0], label)


def measurement_name(key):
    concept, name, unit, unit_name = MEASUREMENTS[key]
    return f"measurement value {WINDOW}: {name} ({unit_name or 'Unknown unit'})"


def measurement(key, bits, interval, unit, label, offset=0, dec=0):
    cid = _ref(cid_measurement(key), measurement_name(key), 706, MEASUREMENTS[key][0])
    return N(col(cid), bits, interval, unit, REF[cid][0], offset, dec, label)


def visits(key, bits, interval, label):
    concept, name = VISITS[key]
    cid = _ref(concept * 1000 + 923,
               f"visit_occurrence concept count during day -365 through 0 concept_count relative to index: {name}",
               923, concept)
    return N(col(cid), bits, interval, "visits", REF[cid][0], 0, 0, label)


AGE = _ref(1002, "age in years", 2, 0)
CHOL = _ref(cid_measurement("chol"), measurement_name("chol"), 706, MEASUREMENTS["chol"][0])
MALE = _ref(8507001, "gender = MALE", 1, 8507)
FEMALE = _ref(8532001, "gender = FEMALE", 1, 8532)
SCORES = {
    "charlson": _ref(1901, "Charlson index - Romano adaptation", 901, 0),
    "chads2": _ref(1903, "CHADS2", 903, 0),
    "chads2vasc": _ref(1904, "CHADS2VASc", 904, 0),
}
for lo in range(15, 100, 5):
    _ref((lo // 5) * 1000 + 3, f"age group: {lo:>3} - {lo + 4:>3}", 3, 0)
for y in range(2019, 2025):
    _ref(y * 1000 + 6, f"index year: {y}", 6, 0)

AGE_COL = N(col(AGE), 3, 10, "years", "age in years", 18, 0, "age")
GENDER = Categorical(col(MALE), {"1": "1", "0": "0", "2": "0", "3": "0"}, "gender = MALE", "male")
CARE_SITE = Categorical(
    "care_site_id", {"1": "1001", "0": "1002", "2": "1003", "3": "1004"},
    "CARE_SITE of the index visit (CDM field)", "care site",
)

# Charlson categories (FeatureExtraction CharlsonIndex.sql) reached by our
# condition concepts, with their weights.
CHARLSON = {
    "mi": 1, "hf": 1, "pvd": 1, "cvd": 1, "dementia": 1, "copd": 1, "liver": 1,
    "t2dm": 1, "dm_complications": 2, "ckd": 2, "hiv": 6,
}


def _flag(r, key, table):
    c = col(cid_condition(key)) if table == "condition" else col(cid_drug(key))
    return r.get(c) == "1"


def fe_derive(cohort_conditions=(), cohort_start=dt.date(2020, 1, 1), cohort_days=1460):
    """Derived FeatureExtraction covariates + cohort fields.

    `cohort_conditions`: conditions every cohort member has by definition
    (e.g. T2DM in a T2DM cohort); they are emitted as constant 1."""

    def derive(r, rng, i, is_decoy):
        out = {}
        for key in cohort_conditions:
            c = col(cid_condition(key))
            if c not in r:
                out[c] = "1"
                r[c] = "1"
        age = int(float(r[col(AGE)]))
        male = r.get(col(MALE)) == "1"
        index = cohort_start + dt.timedelta(days=rng.randint(0, cohort_days))
        out["subject_id"] = 100000 + i
        out["cohort_definition_id"] = 1
        out["cohort_start_date"] = index.isoformat()
        out[col(FEMALE)] = "0" if male else "1"
        for lo in range(15, 100, 5):
            out[col((lo // 5) * 1000 + 3)] = "1" if lo <= age <= lo + 4 else "0"
        for y in range(2019, 2025):
            out[col(y * 1000 + 6)] = "1" if index.year == y else "0"
        lipids = [r.get(col(cid_measurement(k))) for k in ("ldl", "hdl", "tg")]
        if all(lipids):
            ldl, hdl, tg = map(float, lipids)
            # Total cholesterol consistent with Friedewald: LDL = TC - HDL - TG/5.
            out[col(CHOL)] = f"{ldl + hdl + tg / 5:.0f}"
        has = lambda k: r.get(col(cid_condition(k))) == "1"  # noqa: E731
        cats = {k for k in CHARLSON if k != "dm_complications" and has(k)}
        if has("dm_retinopathy") or has("dm_neuropathy"):
            cats.add("dm_complications")
        out[col(SCORES["charlson"])] = sum(CHARLSON[k] for k in cats)
        stroke, vascular = has("cvd"), has("mi") or has("pvd")
        diabetes = has("t2dm")
        out[col(SCORES["chads2"])] = (
            has("hf") + has("htn") + (age >= 75) + diabetes + 2 * stroke
        )
        out[col(SCORES["chads2vasc"])] = (
            has("hf") + has("htn") + diabetes + 2 * stroke + vascular
            + (2 if age >= 75 else 1 if age >= 65 else 0) + (not male)
        )
        return out

    return derive


def fe_order(template_columns):
    head = ["subject_id", "cohort_definition_id", "cohort_start_date", "care_site_id"]
    demo = [col(MALE), col(FEMALE), col(AGE)] + [col((lo // 5) * 1000 + 3) for lo in range(15, 100, 5)] \
        + [col(y * 1000 + 6) for y in range(2019, 2025)]
    scores = [col(v) for v in SCORES.values()]
    return head + demo + template_columns + scores


def covariate_ref(header):
    """covariate_ref.csv for the covariates present in a dataset."""
    lines = ["covariateId,covariateName,analysisId,conceptId"]
    for h in header:
        if h.startswith("cov_"):
            cid = int(h[4:])
            name, analysis, concept = REF[cid]
            lines.append(f'{cid},"{name}",{analysis},{concept}')
    return {"covariate_ref.csv": "\n".join(lines) + "\n"}


def _members(template_parts):
    return [p.name for p in template_parts]


# ---------------------------------------------------------------- cohorts

T2DM_NUMERIC = [
    AGE_COL,
    measurement("bmi", 3, 2.5, "kg/m²", "BMI", 22, 1),
    measurement("sbp", 3, 8, "mmHg", "systolic BP", 110),
    measurement("dbp", 2, 7, "mmHg", "diastolic BP", 64),
    measurement("ldl", 3, 15, "mg/dL", "LDL cholesterol", 60),
    measurement("hdl", 2, 10, "mg/dL", "HDL cholesterol", 30),
    measurement("tg", 3, 25, "mg/dL", "triglycerides", 60),
    measurement("hgb", 2, 1, "g/dL", "haemoglobin", 12, 1),
    visits("inpatient", 2, 1, "inpatient visits"),
    visits("outpatient", 3, 3, "outpatient visits"),
    visits("er", 2, 1, "ER visits"),
    measurement("crp", 2, 2.5, "mg/L", "CRP", 0, 1),
    measurement("creat", 2, 0.2, "mg/dL", "creatinine", 0.7, 1),
]
T2DM_FLAGS = [
    condition("htn", "hypertension"), condition("hyperlipidemia", "hyperlipidaemia"),
    condition("obesity", "obesity"), condition("ckd", "chronic kidney disease"),
    condition("hf", "heart failure"), condition("mi", "myocardial infarction"),
    condition("cvd", "cerebrovascular disease"), condition("pvd", "peripheral vascular disease"),
    condition("af", "atrial fibrillation"), condition("dm_retinopathy", "diabetic retinopathy"),
    condition("dm_neuropathy", "diabetic neuropathy"), condition("depression", "depression"),
    condition("copd", "COPD"), condition("dementia", "dementia"), condition("liver", "chronic liver disease"),
    condition("aki", "acute kidney injury"),
    drug("insulins", "insulin"), drug("glucose_lowering", "non-insulin glucose-lowering drugs"),
    drug("lipid", "lipid-modifying drugs"), drug("antithrombotic", "antithrombotic drugs"),
    drug("ras", "RAS inhibitors"), drug("beta_blockers", "beta blockers"), drug("diuretics", "diuretics"),
    drug("psychoanaleptics", "antidepressants/psychoanaleptics"), drug("opioids", "opioids"),
    drug("corticosteroids", "systemic corticosteroids"), drug("antibacterials", "antibiotics"),
    drug("immunosuppressants", "immunosuppressants"),
]
T2DM_TAIL = [GENDER, CARE_SITE, drug("diabetes_drugs", "any diabetes drug")]
condition("t2dm", "type 2 diabetes")  # cohort-defining: constant 1, listed in covariate_ref

OMOP_T2DM = SchemaTemplate(
    id="omop_t2dm",
    category="healthcare",
    title="Type 2 diabetes cohort",
    standard="OMOP CDM v5.4 · OHDSI FeatureExtraction",
    domain="Observational study (EHDEN / DARWIN EU style)",
    summary=(
        "A type 2 diabetes cohort with the standard OHDSI FeatureExtraction covariates "
        "— demographics, condition and drug group eras, measurement values, visit counts "
        "and Charlson/CHADS2/CHADS2VASc — one row per cohort subject."
    ),
    story=(
        "A network study reports mean HbA1c for cohort subgroups defined by covariates: "
        "comorbidities, drug classes, measurement ranges, age and care site — the "
        "'Table 1' and characterisation output of every OHDSI study."
    ),
    sensitive=Sensitive(
        col(_ref(cid_measurement("hba1c"), measurement_name("hba1c"), 706, 3004410)),
        5.5, 12.0, "%", "HbA1c value (percent)", decimals=1, label="HbA1c",
    ),
    static=T2DM_NUMERIC,
    blocks=[],
    tail=T2DM_TAIL,
    extras=T2DM_FLAGS,
    sources=[
        ("OHDSI FeatureExtraction", FE),
        ("OMOP CDM v5.4", CDM),
        ("OHDSI vocabulary (concept lookup)", "https://athena.ohdsi.org/"),
    ],
    download_n=64,
    derive=fe_derive(cohort_conditions=("t2dm",)),
    column_order=fe_order(
        [col(cid_condition("t2dm"))] + _members(T2DM_FLAGS + T2DM_TAIL[2:] + T2DM_NUMERIC[1:])
        + [col(CHOL), col(cid_measurement("hba1c"))]
    ),
    extra_files=covariate_ref,
)


# ------------------------------------------------------ further cohorts

VISIT_COUNTS = [
    visits("inpatient", 2, 1, "inpatient visits"),
    visits("outpatient", 3, 3, "outpatient visits"),
    visits("er", 2, 1, "ER visits"),
]


def cohort(id, title, domain, summary, story, sensitive, numeric, flags, tail_flag,
           cohort_condition, sources_extra=()):
    """An OMOP/FeatureExtraction cohort template with the shared layout."""
    condition(cohort_condition, cohort_condition)  # constant 1, listed in covariate_ref
    return SchemaTemplate(
        id=id,
        category="healthcare",
        title=title,
        standard="OMOP CDM v5.4 · OHDSI FeatureExtraction",
        domain=domain,
        summary=summary,
        story=story,
        sensitive=sensitive,
        static=numeric,
        blocks=[],
        tail=[GENDER, CARE_SITE, tail_flag],
        extras=flags,
        sources=[
            ("OHDSI FeatureExtraction", FE),
            ("OMOP CDM v5.4", CDM),
            ("OHDSI vocabulary (concept lookup)", "https://athena.ohdsi.org/"),
            *sources_extra,
        ],
        download_n=64,
        derive=fe_derive(cohort_conditions=(cohort_condition,)),
        column_order=fe_order(
            [col(cid_condition(cohort_condition))]
            + _members(flags + [tail_flag] + [m for m in numeric if m.name != col(AGE)])
            + [col(CHOL), sensitive.name]
        ),
        extra_files=covariate_ref,
    )


HFRS = _ref(1926, "Hospital Frailty Risk Score (hfrs)", 926, 0)

OMOP_HIV = cohort(
    id="omop_hiv",
    title="HIV cohort",
    domain="Observational study of people living with HIV",
    summary=(
        "People living with HIV with the standard OHDSI FeatureExtraction covariates — "
        "comorbidities, drug classes, CD4 count, vital signs, labs and visit counts — "
        "one row per cohort subject."
    ),
    story=(
        "A network study reports mean viral load for cohort subgroups defined by CD4 "
        "bands, comorbidities, co-medication, age and care site."
    ),
    sensitive=Sensitive(
        col(_ref(cid_measurement("viral_load"), measurement_name("viral_load"), 706, 3010747)),
        20, 100000, "copies/mL", "HIV-1 viral load (copies per milliliter)", label="HIV viral load",
    ),
    numeric=[
        N(col(AGE), 3, 8, "years", "age in years", 18, 0, "age"),
        measurement("cd4", 3, 100, "cells/µL", "CD4 count", 100),
        measurement("bmi", 3, 2.5, "kg/m²", "BMI", 18, 1),
        measurement("sbp", 3, 8, "mmHg", "systolic BP", 105),
        measurement("dbp", 2, 7, "mmHg", "diastolic BP", 62),
        measurement("ldl", 3, 15, "mg/dL", "LDL cholesterol", 60),
        measurement("hdl", 2, 10, "mg/dL", "HDL cholesterol", 30),
        measurement("tg", 3, 25, "mg/dL", "triglycerides", 60),
        measurement("hgb", 2, 1, "g/dL", "haemoglobin", 12, 1),
        measurement("creat", 2, 0.2, "mg/dL", "creatinine", 0.6, 1),
        *VISIT_COUNTS,
    ],
    flags=[
        condition("htn", "hypertension"), condition("hyperlipidemia", "hyperlipidaemia"),
        condition("obesity", "obesity"), condition("ckd", "chronic kidney disease"),
        condition("hf", "heart failure"), condition("mi", "myocardial infarction"),
        condition("cvd", "cerebrovascular disease"), condition("pvd", "peripheral vascular disease"),
        condition("af", "atrial fibrillation"), condition("depression", "depression"),
        condition("copd", "COPD"), condition("liver", "chronic liver disease"),
        condition("aki", "acute kidney injury"), condition("dementia", "dementia"),
        condition("t2dm", "type 2 diabetes"),
        drug("lipid", "lipid-modifying drugs"), drug("antithrombotic", "antithrombotic drugs"),
        drug("ras", "RAS inhibitors"), drug("beta_blockers", "beta blockers"), drug("diuretics", "diuretics"),
        drug("psychoanaleptics", "antidepressants/psychoanaleptics"), drug("opioids", "opioids"),
        drug("corticosteroids", "systemic corticosteroids"), drug("antibacterials", "antibiotics"),
        drug("immunosuppressants", "immunosuppressants"), drug("glucose_lowering", "glucose-lowering drugs"),
        drug("insulins", "insulin"),
    ],
    tail_flag=drug("antivirals", "antiretroviral/antiviral therapy"),
    cohort_condition="hiv",
)

OMOP_COVID = cohort(
    id="omop_covid",
    title="COVID-19 hospitalisation cohort",
    domain="Network study of hospitalised COVID-19 patients",
    summary=(
        "Patients hospitalised with COVID-19, with the standard OHDSI FeatureExtraction "
        "covariates — comorbidities, drug classes, ventilation, vital signs, labs and "
        "visit counts — one row per cohort subject."
    ),
    story=(
        "A European network study on COVID-19 hospitalisations reports the mean "
        "Hospital Frailty Risk Score for subgroups defined by comorbidities, "
        "treatments, vital signs, lab values and care site — every group far above "
        "the usual minimum cell count of 5."
    ),
    sensitive=Sensitive(col(HFRS), 0, 30, "points", "Hospital Frailty Risk Score (frailty)", decimals=1,
                        label="frailty score"),
    numeric=[
        N(col(AGE), 3, 8, "years", "age in years", 30, 0, "age"),
        measurement("bmi", 3, 2.5, "kg/m²", "BMI", 20, 1),
        measurement("sbp", 3, 8, "mmHg", "systolic BP", 100),
        measurement("dbp", 2, 7, "mmHg", "diastolic BP", 60),
        measurement("spo2", 2, 2, "%", "oxygen saturation", 90),
        measurement("resp", 2, 4, "/min", "respiratory rate", 14),
        measurement("crp", 3, 20, "mg/L", "CRP"),
        measurement("hgb", 2, 1, "g/dL", "haemoglobin", 11, 1),
        measurement("creat", 2, 0.3, "mg/dL", "creatinine", 0.6, 1),
        *VISIT_COUNTS,
    ],
    flags=[
        condition("t2dm", "type 2 diabetes"), condition("htn", "hypertension"),
        condition("hf", "heart failure"), condition("copd", "COPD"),
        condition("ckd", "chronic kidney disease"), condition("mi", "myocardial infarction"),
        condition("cvd", "cerebrovascular disease"), condition("pvd", "peripheral vascular disease"),
        condition("af", "atrial fibrillation"), condition("dementia", "dementia"),
        condition("depression", "depression"), condition("obesity", "obesity"),
        condition("hyperlipidemia", "hyperlipidaemia"), condition("liver", "chronic liver disease"),
        condition("aki", "acute kidney injury"), condition("hiv", "HIV infection"),
        drug("diabetes_drugs", "diabetes drugs"), drug("insulins", "insulin"),
        drug("glucose_lowering", "glucose-lowering drugs"), drug("antithrombotic", "antithrombotic drugs"),
        drug("lipid", "lipid-modifying drugs"), drug("beta_blockers", "beta blockers"),
        drug("ras", "RAS inhibitors"), drug("diuretics", "diuretics"),
        drug("psychoanaleptics", "antidepressants/psychoanaleptics"), drug("opioids", "opioids"),
        drug("corticosteroids", "systemic corticosteroids"), drug("antibacterials", "antibiotics"),
        drug("immunosuppressants", "immunosuppressants"), drug("antivirals", "antivirals"),
        procedure(4230167, "Artificial ventilation", "artificial ventilation"),
    ],
    tail_flag=procedure(37158404, "Invasive mechanical ventilation", "invasive mechanical ventilation"),
    cohort_condition="covid",
)
