"""
Swedish register extracts, one row per person.

* RIKS-HIA (SWEDEHEART): column names are the official "Variabeltext" labels
  from SWEDEHEART's RIKS-HIA variable list, made SQL-safe (spaces and hyphens
  as underscores, parenthesised qualifiers dropped: "Längd (cm)" -> Längd);
  codes from the 2026 registration forms (start, care, discharge).
* NDR: field names and codes from NDR's public variable metadata
  (ndr.registercentrum.se, form "Rapport/Komplettera"); eGFR by MDRD and LDL by
  Friedewald, as NDR computes them.
* LISA (SCB): variable names, codes and units (amounts in hundreds of SEK)
  from "LISA – bakgrundsfakta 1990–2017"; one row per person and year.

Where a register derives a variable (BMI, eGFR, LDL, age groups, municipality
from county, ...), it is derived here the same way, never drawn
independently. Nothing is ever derived from the hidden attribute.
"""
from __future__ import annotations

import datetime as dt

from ..schemas import Categorical, N, SchemaTemplate, Sensitive

RIKSHIA_LIST = "https://www.ucr.uu.se/swedeheart/dokument-sh/variabellista/variabellista-swedeheart-riks-hia"
RIKSHIA_FORMS = "https://www.ucr.uu.se/swedeheart/dokument-rikshia/formular-rikshia"
NDR_VARS = "https://ndr.registercentrum.se/om-diabetesregistret/variabellista/p/SJ2gEjMGh"
LISA_DOC = "https://www.scb.se/contentassets/0521204f13e649299dec73f091e691e0/lisa-bakgrundsfakta-1990-2017.pdf"


def yes_no(name, description, label, yes="1", no="0"):
    return Categorical(name, {"1": yes, "0": no, "2": no, "3": no}, description, label)


# ------------------------------------------------------------- RIKS-HIA

def rikshia_derive(r, rng, i, is_decoy):
    age = int(float(r["Ålder"]))
    arrival = dt.datetime(2023, 1, 1, 0, 0) + dt.timedelta(minutes=rng.randint(0, 3 * 365 * 24 * 60))
    onset = arrival - dt.timedelta(minutes=rng.randint(30, 12 * 60))
    born = arrival.date() - dt.timedelta(days=round((age + rng.random()) * 365.25))
    out = {
        "Registreringsnummer": 500001 + i,
        "Födelsedatum": born.isoformat(),
        "Symtomdebut_datum": onset.date().isoformat(),
        "Symtomdebut_tid": onset.strftime("%H:%M"),
        "Ankomst_till_akuten_datum": arrival.date().isoformat(),
        "Ankomst_till_akuten_tid": arrival.strftime("%H:%M"),
        "Infarktmarkör": "5",  # HS Trop T (ng/L)
        "Avliden": "1" if rng.random() < 0.04 else "0",
    }
    for name in ("Längd", "Vikt"):
        if name not in r:
            out[name] = ""
    return out


RIKSHIA_NUMERIC = [
    N("Ålder", 3, 8, "år", "Ålder vid ankomst (från personnummer)", 35, 0, "age"),
    N("Längd", 2, 8, "cm", "Längd (cm)", 158, 0, "height"),
    N("Vikt", 3, 6, "kg", "Vikt (kg)", 55, 0, "weight"),
    N("Systoliskt_blodtryck", 3, 10, "mmHg", "Systoliskt blodtryck", 110, 0, "systolic BP"),
    N("Diastoliskt_blodtryck", 2, 10, "mmHg", "Diastoliskt blodtryck", 55, 0, "diastolic BP"),
    N("Hjärtfrekvens", 3, 10, "/min", "Hjärtfrekvens", 45, 0, "heart rate"),
    N("Kolesterol", 2, 1, "mmol/L", "Kolesterol", 3, 1, "cholesterol"),
    N("Triglycerider", 2, 0.5, "mmol/L", "Triglycerider", 0.6, 1, "triglycerides"),
    N("HDL", 2, 0.4, "mmol/L", "HDL", 0.8, 1, "HDL"),
    N("P_Glukos", 2, 2, "mmol/L", "P-Glukos", 4.5, 1, "glucose"),
    N("ApoB", 2, 0.3, "g/L", "ApoB", 0.5, 2, "ApoB"),
    N("ApoA1", 2, 0.25, "g/L", "ApoA1", 1.0, 2, "ApoA1"),
    N("HbA1c", 3, 8, "mmol/mol", "HbA1c", 32, 0, "HbA1c"),
]
RIKSHIA_CATEGORICAL = [
    Categorical("Rökning", {"1": "2", "0": "0", "2": "1", "3": "0"}, "Rökning (0 aldrig, 1 ex-rökare >1 mån, 2 rökare)", "smoking"),
    Categorical("Snusning", {"1": "2", "0": "0", "2": "1", "3": "0"}, "Snusning (0 aldrig, 1 före detta, 2 snusare)", "snus"),
    yes_no("Tidigare_stroke_ej_TIA", "Tidigare stroke (ej TIA)", "previous stroke"),
    yes_no("Tidigare_hjärtinfarkt", "Tidigare hjärtinfarkt", "previous heart attack"),
    yes_no("Tidigare_PCI", "Tidigare PCI", "previous PCI"),
    Categorical("Tidigare_hjärtkirurgi", {"1": "1", "0": "0", "2": "2", "3": "0"},
                "Tidigare hjärtkirurgi (0 nej, 1 CABG, 2 annan)", "previous heart surgery"),
    Categorical("Känd_nedsatt_vänsterkammarfunktion", {"1": "2", "0": "0", "2": "3", "3": "4"},
                "Känd nedsatt vänsterkammarfunktion (0 nej, 2 lätt, 3 måttlig, 4 uttalad)", "known reduced LV function"),
    Categorical("Sysselsättning", {"1": "4", "0": "1", "2": "2", "3": "3"},
                "Sysselsättning (1 arbetar, 2 sjukskriven, 3 arbetslös, 4 pensionär)", "occupation"),
    Categorical("Lungrassel", {"1": "1", "0": "0", "2": "0", "3": "2"}, "Lungrassel (0 nej, 1 basala, 2 >halva lungorna)", "lung crackles"),
    yes_no("Cardiogen_chock_vid_ankomst", "Cardiogen chock vid ankomst", "cardiogenic shock on arrival"),
    Categorical("EKG_rytm", {"1": "2", "0": "1", "2": "1", "3": "8"}, "EKG rytm (1 sinus, 2 FF/fladder, 8 annan)", "ECG rhythm"),
    Categorical("EKG_STT", {"1": "2", "0": "1", "2": "3", "3": "4"}, "EKG STT (1 normal, 2 ST-höjning, 3 ST-sänkning, 4 patologisk T)", "ECG ST-T"),
    yes_no("HLR_före_sjukhus", "HLR före sjukhus", "CPR before hospital"),
    Categorical("Ambulans", {"1": "1", "0": "0", "2": "2", "3": "0"}, "Ambulans (0 nej, 1 till akuten, 2 direkt till HIA/PCI-lab)", "ambulance"),
    Categorical("Reperfusionsbehandling", {"1": "2", "0": "0", "2": "4", "3": "0"},
                "Reperfusionsbehandling (0 nej, 1 trombolys, 2 primär PCI, 4 akut angio)", "reperfusion"),
    yes_no("Reinfarkt_under_vårdtillfället", "Reinfarkt under vårdtillfället", "reinfarction"),
    yes_no("Nytt_förmaksflimmer", "Nytt förmaksflimmer", "new atrial fibrillation"),
    yes_no("AV_block", "AV-block (0 inget/AV I, 1 AV II/III)", "AV block"),
    Categorical("Vänsterkammarfunktion", {"1": "1", "0": "2", "2": "3", "3": "4"},
                "Vänsterkammarfunktion (1 normal ≥50%, 2 lätt 40–49%, 3 måttlig 30–39%, 4 uttalad <30%)", "LV function"),
    Categorical("Infarkttyp", {"1": "1", "0": "2", "2": "2", "3": "0"}, "Infarkttyp (0 ej infarkt, 1 STEMI, 2 NSTEMI)", "infarct type"),
    yes_no("ASA", "ASA vid utskrivning", "aspirin at discharge"),
    yes_no("Betablockerare", "Betablockerare vid utskrivning", "beta blocker at discharge"),
    yes_no("Statiner", "Statiner vid utskrivning", "statin at discharge"),
    yes_no("ACE_hämmare", "ACE-hämmare vid utskrivning", "ACE inhibitor at discharge"),
    Categorical("Övriga_trombocythämmare", {"1": "4", "0": "0", "2": "1", "3": "3"},
                "Övriga trombocythämmare (0 nej, 1 klopidogrel, 3 prasugrel, 4 tikagrelor)", "P2Y12 inhibitor"),
    yes_no("Diuretika", "Diuretika vid utskrivning", "diuretic at discharge"),
    Categorical("Aldosteronblockad", {"1": "1", "0": "0", "2": "2", "3": "0"},
                "Aldosteronblockad (0 nej, 1 spironolakton, 2 eplerenon)", "aldosterone blocker"),
    Categorical("Antikoagulantia", {"1": "5", "0": "0", "2": "1", "3": "4"},
                "Antikoagulantia (0 nej, 1 warfarin, 4 rivaroxaban, 5 apixaban)", "anticoagulant"),
    yes_no("Ca_hämmare", "Ca-hämmare vid utskrivning", "calcium channel blocker"),
]
RIKSHIA = SchemaTemplate(
    id="se_rikshia",
    category="public",
    title="Heart attack register",
    standard="SWEDEHEART · RIKS-HIA",
    domain="Coronary care units, all Swedish hospitals",
    summary=(
        "One record per admission for acute coronary syndrome, using RIKS-HIA's "
        "official variable names and codes: history, admission findings, ECG, labs, "
        "reperfusion, complications and discharge medication."
    ),
    story=(
        "Hospital comparisons report the average peak troponin — a measure of how much "
        "heart muscle was lost — for patient groups defined by risk factors, admission "
        "findings, treatment and discharge medication."
    ),
    sensitive=Sensitive("Maxvärde_markör", 20, 20000, "ng/L",
                        "Maxvärde markör — peak high-sensitivity troponin T (infarct size)"),
    static=RIKSHIA_NUMERIC,
    blocks=[],
    tail=[
        Categorical("Kön", {"1": "Man", "0": "Kvinna", "2": "Kvinna", "3": "Kvinna"}, "Kön", "sex"),
        Categorical("Diabetes", {"1": "2", "0": "0", "2": "3", "3": "4"},
                    "Diabetes (0 nej, 2 typ II, 3 typ I, 4 oklar typ)", "diabetes"),
        yes_no("Hypertoni", "Hypertoni", "hypertension"),
    ],
    extras=RIKSHIA_CATEGORICAL,
    sources=[
        ("SWEDEHEART — RIKS-HIA variable list", RIKSHIA_LIST),
        ("RIKS-HIA registration forms 2026", RIKSHIA_FORMS),
    ],
    download_n=64,
    derive=rikshia_derive,
    column_order=(
        ["Registreringsnummer", "Kön", "Födelsedatum", "Ålder", "Avliden", "Längd", "Vikt",
         "Sysselsättning", "Diabetes", "Tidigare_stroke_ej_TIA", "Systoliskt_blodtryck",
         "Diastoliskt_blodtryck", "Lungrassel", "Cardiogen_chock_vid_ankomst", "EKG_rytm", "EKG_STT",
         "Hjärtfrekvens", "Ankomst_till_akuten_datum", "Ankomst_till_akuten_tid", "Symtomdebut_datum",
         "Symtomdebut_tid", "Ambulans", "HLR_före_sjukhus", "Tidigare_hjärtinfarkt",
         "Känd_nedsatt_vänsterkammarfunktion", "Tidigare_PCI", "Tidigare_hjärtkirurgi",
         "Rökning", "Snusning", "Hypertoni", "Reperfusionsbehandling", "Reinfarkt_under_vårdtillfället",
         "AV_block", "Nytt_förmaksflimmer", "Vänsterkammarfunktion", "Infarktmarkör", "Maxvärde_markör",
         "Kolesterol", "Triglycerider", "HDL", "ApoB", "ApoA1", "P_Glukos", "HbA1c",
         "ACE_hämmare", "Antikoagulantia", "Övriga_trombocythämmare", "ASA", "Betablockerare",
         "Ca_hämmare", "Diuretika", "Aldosteronblockad", "Statiner", "Infarkttyp"]
    ),
)

# ------------------------------------------------------------------ NDR

COUNTY_CODES = {"01": "Stockholm", "03": "Uppsala", "12": "Skåne", "14": "Västra Götaland"}


def ndr_derive(r, rng, i, is_decoy):
    age = int(float(r["R_Age"]))
    height = float(r["R_Height"]) if r.get("R_Height") else rng.uniform(155, 190)
    weight = float(r["R_Weight"])
    female = r["R_Gender"] == "2"
    creat = float(r["R_Creatinine"]) if r.get("R_Creatinine") else rng.uniform(55, 110)
    # MDRD (IDMS-traceable), creatinine in µmol/L -> mg/dL.
    gfr = 175 * (creat / 88.4) ** -1.154 * max(age, 18) ** -0.203 * (0.742 if female else 1)
    chol = float(r.get("R_Cholesterol") or rng.uniform(3.5, 6.5))
    hdl = float(r.get("R_HDL") or rng.uniform(0.8, 2.0))
    tg = float(r.get("R_Triglyceride") or rng.uniform(0.6, 3.0))
    ldl = chol - hdl - tg / 2.2  # Friedewald (mmol/L)
    uacr = r.get("R_UAlbCreatinine")
    contact = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randint(0, 365))
    out = {
        "LopNr": 700001 + i,
        "R_ContactDate": contact.isoformat(),
        "R_BMI": f"{weight / (height / 100) ** 2:.1f}",
        "R_GFR": round(gfr),
        "R_LDL": f"{max(ldl, 0.3):.1f}",
    }
    if uacr:
        u = float(uacr)
        out["R_Albuminuria"] = "0" if u < 3 else ("2" if u < 30 else "3")
    for name, make in (("R_Height", lambda: f"{height:.0f}"),):
        if name not in r:
            out[name] = make()
    return out


NDR = SchemaTemplate(
    id="se_ndr",
    category="public",
    title="Diabetes register",
    standard="Nationella Diabetesregistret (NDR)",
    domain="Primary care and hospital clinics",
    summary=(
        "Each patient's latest yearly registration in the National Diabetes Register, "
        "with NDR's own field names and codes; BMI, eGFR (MDRD) and LDL (Friedewald) "
        "computed as NDR does."
    ),
    story=(
        "NDR-style reports show the average HbA1c per region and patient group — by "
        "blood-pressure band, lipids, kidney function, treatment and lifestyle — to "
        "compare the quality of diabetes care."
    ),
    sensitive=Sensitive("R_HbA1c", 31, 108, "mmol/mol", "HbA1c (mmol/mol) — glycaemic control"),
    static=[
        N("R_Age", 3, 8, "år", "Ålder (beräknad)", 30, 0, "age"),
        N("R_Weight", 3, 7, "kg", "Vikt (kg)", 55, 1, "weight"),
        N("R_BpSystolic", 3, 8, "mm Hg", "Blodtryck systoliskt", 112, 0, "systolic BP"),
        N("R_YearOfOnset", 3, 6, "år", "Diagnosår", 1975, 0, "year of diagnosis"),
        N("R_Height", 2, 8, "cm", "Längd (cm)", 158, 0, "height"),
        N("R_BpDiastolic", 2, 7, "mm Hg", "Blodtryck diastoliskt", 62, 0, "diastolic BP"),
        N("R_Cholesterol", 2, 0.8, "mmol/l", "Kolesterol", 3.8, 1, "cholesterol"),
        N("R_HDL", 2, 0.4, "mmol/l", "HDL", 0.8, 1, "HDL"),
        N("R_Triglyceride", 2, 0.6, "mmol/l", "Triglycerider", 0.6, 1, "triglycerides"),
        N("R_Creatinine", 3, 12, "µmol/l", "P/S-kreatinin", 50, 0, "creatinine"),
        N("R_UAlbCreatinine", 2, 1.5, "mg/mmol", "U-Albumin/Kreatinin", 0, 1, "urine albumin/creatinine"),
    ],
    blocks=[],
    tail=[
        Categorical("R_Gender", {"1": "1", "0": "2", "2": "2", "3": "2"}, "Kön (1 man, 2 kvinna)", "sex"),
        Categorical("R_County", {"1": "01", "0": "14", "2": "12", "3": "03"}, "Region (SCB länskod)", "region"),
        yes_no("R_Insulin", "Insulin", "insulin"),
    ],
    extras=[
        Categorical("R_DiabetesType", {"1": "2", "0": "1", "2": "1", "3": "5"},
                    "Diabetestyp (1 typ 1, 2 typ 2, 5 oklar)", "diabetes type"),
        yes_no("R_Metformin", "Metformin", "metformin"),
        yes_no("R_GLP1", "GLP-1-analog", "GLP-1"),
        yes_no("R_SGLT2", "SGLT2-hämmare", "SGLT2 inhibitor"),
        yes_no("R_Antihypertensives", "Blodtryckssänkande läkemedel", "blood-pressure drugs"),
        yes_no("R_LipidLoweringDrugs", "Blodfettssänkande läkemedel", "lipid-lowering drugs"),
        yes_no("R_ThromAggInhib", "ASA/trombocythämmare", "antiplatelet"),
        yes_no("R_DiabeticRetinopathy", "Diabetesretinopati", "retinopathy"),
        yes_no("R_IschemicHeartDisease", "Ischemisk hjärtsjukdom", "ischaemic heart disease"),
        yes_no("R_CerebrovascularDisease", "Cerebrovaskulär sjukdom", "cerebrovascular disease"),
        Categorical("R_SmokingHabit", {"1": "2", "0": "1", "2": "4", "3": "3"},
                    "Rökvanor (1 aldrig, 2 dagligen, 3 ej dagligen, 4 slutat)", "smoking"),
        yes_no("R_CGM", "Kontinuerlig glukosmätning (CGM)", "CGM"),
        Categorical("R_FootRiscCategory", {"1": "2", "0": "1", "2": "1", "3": "3"},
                    "Fotriskkategori (1 frisk fot, 2 neuropati/angiopati, 3 tidigare sår)", "foot risk"),
        yes_no("R_DPP4", "DPP-4-hämmare", "DPP-4 inhibitor"),
    ],
    sources=[
        ("NDR — variable list (public metadata)", NDR_VARS),
        ("Nationella Diabetesregistret", "https://ndr.registercentrum.se/"),
    ],
    download_n=32,
    derive=ndr_derive,
    column_order=[
        "LopNr", "R_ContactDate", "R_Gender", "R_Age", "R_County", "R_DiabetesType", "R_YearOfOnset",
        "R_HbA1c", "R_Height", "R_Weight", "R_BMI", "R_BpSystolic", "R_BpDiastolic", "R_Cholesterol",
        "R_HDL", "R_Triglyceride", "R_LDL", "R_Creatinine", "R_GFR", "R_UAlbCreatinine", "R_Albuminuria",
        "R_Insulin", "R_Metformin", "R_GLP1", "R_SGLT2", "R_DPP4", "R_CGM", "R_Antihypertensives",
        "R_LipidLoweringDrugs", "R_ThromAggInhib", "R_DiabeticRetinopathy", "R_FootRiscCategory",
        "R_IschemicHeartDisease", "R_CerebrovascularDisease", "R_SmokingHabit",
    ],
)

# ----------------------------------------------------------------- LISA

KOMMUNER = {"01": ["0180", "0182", "0184", "0162"], "03": ["0380", "0381", "0305"],
            "12": ["1280", "1281", "1283", "1290"], "14": ["1480", "1484", "1490", "1485"]}


def lisa_derive(r, rng, i, is_decoy):
    age = int(float(r["Alder"]))
    lon = float(r["LoneInk"])
    alos = float(r.get("ALosDag") or 0)
    fp = float(r.get("ForPeng_Ndag_MiDAS") or 0)
    out = {
        "LopNr": 900001 + i,
        "Ar": 2023,
        "FodelseAr": 2023 - age,
        "Kommun": rng.choice(KOMMUNER[r["Lan"]]),
        "ForvInk": round(lon + (rng.uniform(0, 400) if rng.random() < 0.1 else 0)),
        "ArbLos": round(alos * rng.uniform(6, 9)),  # hundreds of SEK, ~600-900 SEK/day
        "ForLed": round(fp * rng.uniform(5, 9)),
        "AldPens": round(rng.uniform(1200, 2600)) if age >= 65 else 0,
        "Raks_Huvudanknytning": "7" if r.get("SyssStat11") == "6" else rng.choice(["1", "1", "1", "4", "6"]),
    }
    return out


LISA = SchemaTemplate(
    id="se_lisa",
    category="public",
    title="Income, work and sickness",
    standard="SCB · LISA",
    domain="Register-based labour-market and health research",
    summary=(
        "A LISA extract for one year, one row per person, with SCB's variable names, "
        "codes and units (amounts in hundreds of SEK): demographics, region, "
        "education, employment, incomes and social-insurance benefits."
    ),
    story=(
        "A register study publishes the average number of sickness-benefit days for "
        "groups defined by income bands, unemployment, parental leave, education, "
        "region and sex — the standard breakdowns of Swedish register statistics."
    ),
    sensitive=Sensitive("SjukP_Ndag_MiDAS", 0, 365, "nettodagar",
                        "Sjukpenning, antal nettodagar (MiDAS) — days on sick leave"),
    static=[
        N("Alder", 3, 7, "år", "Ålder 31 december", 18, 0, "age"),
        N("LoneInk", 3, 1000, "hundratals kr", "Kontant bruttolön", 0, 0, "salary"),
        N("DispInk04", 3, 800, "hundratals kr", "Individens disponibla inkomst", 0, 0, "disposable income"),
        N("DispInkKE04", 2, 1000, "hundratals kr", "Disponibel inkomst per konsumtionsenhet (familj)", 0, 0, "family disposable income"),
        N("ALosDag", 3, 30, "dagar", "Antal dagar öppet arbetslös", 0, 0, "unemployment days"),
        N("SocBidrFam", 3, 100, "hundratals kr", "Ekonomiskt bistånd (familj)", 0, 0, "social assistance"),
        N("ForPeng_Ndag_MiDAS", 2, 60, "nettodagar", "Föräldrapenning, nettodagar", 0, 0, "parental-benefit days"),
        N("TfForPeng_Ndag", 2, 10, "nettodagar", "Tillfällig föräldrapenning, nettodagar", 0, 0, "care-of-sick-child days"),
        N("SjukErs", 2, 400, "hundratals kr", "Sjukersättning", 0, 0, "sickness compensation"),
        N("AmPol", 2, 200, "hundratals kr", "Arbetsmarknadspolitiska åtgärder", 0, 0, "labour-market programmes"),
    ],
    blocks=[],
    tail=[
        Categorical("Kon", {"1": "1", "0": "2", "2": "2", "3": "2"}, "Kön (1 man, 2 kvinna)", "sex"),
        Categorical("Lan", {"1": "01", "0": "14", "2": "12", "3": "03"}, "Län (bostadslän, kod)", "county"),
        Categorical("UtlSvBakg", {"1": "22", "0": "11", "2": "12", "3": "21"},
                    "Utländsk/svensk bakgrund (11 utrikes född, 12/21 en eller två utrikes födda föräldrar, 22 svensk bakgrund)",
                    "Swedish/foreign background"),
    ],
    extras=[
        Categorical("Civil", {"1": "G", "0": "OG", "2": "S", "3": "Ä"}, "Civilstånd (OG ogift, G gift, S skild, Ä änka/änkling)", "marital status"),
        Categorical("Sun2000niva_old", {"1": "4", "0": "3", "2": "6", "3": "2"},
                    "Utbildningsnivå, 7 nivåer (2 grundskola 9 år … 6 eftergymnasial ≥3 år)", "education level"),
        Categorical("SyssStat11", {"1": "1", "0": "6", "2": "5", "3": "6"},
                    "Sysselsättningsstatus (1 förvärvsarbetande, 5/6 ej förvärvsarbetande)", "employment status"),
        Categorical("Sun2000Inr", {"1": "3", "0": "2", "2": "5", "3": "7"},
                    "Utbildningens inriktning (första siffran: 2 humaniora, 3 samhällsvetenskap, 5 teknik, 7 vård)",
                    "field of education"),
    ],
    sources=[
        ("SCB — LISA bakgrundsfakta 1990–2017", LISA_DOC),
        ("SCB — LISA", "https://www.scb.se/lisa"),
    ],
    download_n=32,
    derive=lisa_derive,
    column_order=[
        "LopNr", "Ar", "FodelseAr", "Alder", "Kon", "Civil", "UtlSvBakg", "Lan", "Kommun",
        "Sun2000niva_old", "Sun2000Inr", "SyssStat11", "Raks_Huvudanknytning", "LoneInk", "ForvInk",
        "DispInk04", "DispInkKE04", "AldPens", "ArbLos", "ALosDag", "AmPol", "ForLed",
        "ForPeng_Ndag_MiDAS", "TfForPeng_Ndag", "SjukP_Ndag_MiDAS", "SjukErs", "SocBidrFam",
    ],
)
