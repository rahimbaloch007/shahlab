import streamlit as st
from datetime import date, datetime
import base64, json, os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Circle, Rect, Line, Ellipse
from reportlab.graphics import renderPDF

st.set_page_config(page_title="Shah Lab", page_icon="🔬", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] { display:none!important; }
[data-testid="stToolbar"] { display:none!important; }
header { display:none!important; }
footer { display:none!important; }
#MainMenu { display:none!important; }
.main .block-container { padding-top:2rem; padding-bottom:2rem; max-width:800px; }
.step-bar { display:flex; align-items:center; justify-content:center; gap:0; margin-bottom:1.8rem; }
.step-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.step-circle { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.78rem; font-weight:600; }
.step-circle.done   { background:#16a34a; color:#fff; }
.step-circle.active { background:#1a1a2e; color:#fff; }
.step-circle.idle   { background:#e5e7eb; color:#9ca3af; }
.step-label { font-size:0.68rem; color:#6b7280; font-weight:500; }
.step-label.active { color:#1a1a2e; font-weight:600; }
.step-line { width:48px; height:2px; background:#e5e7eb; margin-bottom:16px; }
.step-line.done { background:#16a34a; }
.section-heading { font-size:1.35rem; font-weight:700; color:#1a1a2e; margin-bottom:4px; }
.section-sub { font-size:0.85rem; color:#6b7280; margin-bottom:1.4rem; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:8px 0; margin-bottom:8px; border-bottom:1px solid #e5e7eb; }
.topbar-title { font-size:1rem; font-weight:700; color:#1a1a2e; }
.topbar-user { font-size:0.8rem; color:#6b7280; }
@media print { .no-print,.stButton,.stRadio,[data-testid="stToolbar"]{ display:none!important; } }
</style>
""", unsafe_allow_html=True)

# ── Settings ───────────────────────────────────────────────────────────────────
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

def load_settings():
    try:
        with open(SETTINGS_PATH) as f:
            s = json.load(f)
    except:
        s = {}
    s.setdefault("lab_name",     "Shah Lab & Diagnostics")
    s.setdefault("lab_address",  "Golra Railway Pathak Chowk, Islamabad")
    s.setdefault("lab_phone",    "03413793007")
    s.setdefault("print_header", True)
    s.setdefault("custom_tests", {})
    return s

def save_settings(s):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2)

# ── Built-in catalog ───────────────────────────────────────────────────────────
BUILTIN_CATALOG = {
    "HEMATOLOGY": {
        "Complete Blood Count (CBC)": [
            {"name":"Haemoglobin (Hb)",          "unit":"g/dL",       "ref_low":"13.0","ref_high":"17.0","ref_text":"13.0–17.0 (M) / 12.0–15.0 (F)"},
            {"name":"Total RBC Count",            "unit":"×10⁶/µL",   "ref_low":"4.5", "ref_high":"5.5", "ref_text":"4.5–5.5 (M) / 3.8–4.8 (F)"},
            {"name":"Haematocrit (PCV)",          "unit":"%",          "ref_low":"40",  "ref_high":"52",  "ref_text":"40–52 (M) / 36–48 (F)"},
            {"name":"MCV",                        "unit":"fL",         "ref_low":"80",  "ref_high":"100", "ref_text":"80–100"},
            {"name":"MCH",                        "unit":"pg",         "ref_low":"27",  "ref_high":"32",  "ref_text":"27–32"},
            {"name":"MCHC",                       "unit":"g/dL",       "ref_low":"32",  "ref_high":"36",  "ref_text":"32–36"},
            {"name":"RDW",                        "unit":"%",          "ref_low":"11.5","ref_high":"14.5","ref_text":"11.5–14.5"},
            {"name":"Total WBC Count",            "unit":"×10³/µL",   "ref_low":"4.0", "ref_high":"11.0","ref_text":"4.0–11.0"},
            {"name":"Neutrophils",                "unit":"%",          "ref_low":"40",  "ref_high":"75",  "ref_text":"40–75"},
            {"name":"Lymphocytes",                "unit":"%",          "ref_low":"20",  "ref_high":"45",  "ref_text":"20–45"},
            {"name":"Monocytes",                  "unit":"%",          "ref_low":"2",   "ref_high":"10",  "ref_text":"2–10"},
            {"name":"Eosinophils",                "unit":"%",          "ref_low":"1",   "ref_high":"6",   "ref_text":"1–6"},
            {"name":"Basophils",                  "unit":"%",          "ref_low":"0",   "ref_high":"1",   "ref_text":"0–1"},
            {"name":"Platelet Count",             "unit":"×10³/µL",   "ref_low":"150", "ref_high":"400", "ref_text":"150–400"},
            {"name":"MPV",                        "unit":"fL",         "ref_low":"7.5", "ref_high":"12.5","ref_text":"7.5–12.5"},
        ],
        "ESR": [{"name":"ESR","unit":"mm/hr","ref_low":"","ref_high":"","ref_text":"0–15 (M) / 0–20 (F)"}],
        "Peripheral Blood Film": [
            {"name":"RBC Morphology",    "unit":"","ref_low":"","ref_high":"","ref_text":"Normocytic Normochromic"},
            {"name":"WBC Morphology",    "unit":"","ref_low":"","ref_high":"","ref_text":"Normal morphology"},
            {"name":"Platelet Morphology","unit":"","ref_low":"","ref_high":"","ref_text":"Adequate in number"},
            {"name":"Impression",        "unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
        "Reticulocyte Count":    [{"name":"Reticulocyte Count","unit":"%","ref_low":"0.5","ref_high":"1.5","ref_text":"0.5–1.5"}],
        "Blood Group & Rh Typing":[
            {"name":"Blood Group","unit":"","ref_low":"","ref_high":"","ref_text":"A / B / AB / O"},
            {"name":"Rh Factor",  "unit":"","ref_low":"","ref_high":"","ref_text":"Positive / Negative"},
        ],
    },
    "COAGULATION": {
        "Bleeding Time (BT)":  [{"name":"Bleeding Time","unit":"min","ref_low":"1","ref_high":"3","ref_text":"1–3 min"}],
        "Clotting Time (CT)":  [{"name":"Clotting Time","unit":"min","ref_low":"5","ref_high":"11","ref_text":"5–11 min"}],
        "Prothrombin Time (PT/INR)": [
            {"name":"Prothrombin Time (PT)","unit":"sec","ref_low":"11","ref_high":"14","ref_text":"11–14 sec"},
            {"name":"Control PT",           "unit":"sec","ref_low":"",  "ref_high":"",  "ref_text":""},
            {"name":"INR",                  "unit":"",   "ref_low":"0.8","ref_high":"1.2","ref_text":"0.8–1.2"},
        ],
        "APTT": [
            {"name":"APTT (Patient)","unit":"sec","ref_low":"25","ref_high":"35","ref_text":"25–35 sec"},
            {"name":"APTT (Control)","unit":"sec","ref_low":"",  "ref_high":"",  "ref_text":""},
        ],
    },
    "BIOCHEMISTRY": {
        "Random Blood Sugar (RBS)":      [{"name":"Blood Glucose (Random)","unit":"mg/dL","ref_low":"","ref_high":"140","ref_text":"< 140 mg/dL"}],
        "Fasting Blood Sugar (FBS)":     [{"name":"Blood Glucose (Fasting)","unit":"mg/dL","ref_low":"70","ref_high":"100","ref_text":"70–100 mg/dL"}],
        "2-hr Post Prandial (PPBS)":     [{"name":"Blood Glucose (2-hr PP)","unit":"mg/dL","ref_low":"","ref_high":"140","ref_text":"< 140 mg/dL"}],
        "HbA1c":                         [{"name":"HbA1c","unit":"%","ref_low":"","ref_high":"5.7","ref_text":"< 5.7% Normal / 5.7–6.4% Pre-DM / ≥6.5% DM"}],
        "Liver Function Tests (LFTs)": [
            {"name":"Total Bilirubin",           "unit":"mg/dL","ref_low":"0.2","ref_high":"1.2","ref_text":"0.2–1.2"},
            {"name":"Direct Bilirubin",          "unit":"mg/dL","ref_low":"0.0","ref_high":"0.3","ref_text":"0.0–0.3"},
            {"name":"Indirect Bilirubin",        "unit":"mg/dL","ref_low":"0.1","ref_high":"0.9","ref_text":"0.1–0.9"},
            {"name":"SGPT (ALT)",                "unit":"U/L",  "ref_low":"7",  "ref_high":"56", "ref_text":"7–56"},
            {"name":"SGOT (AST)",                "unit":"U/L",  "ref_low":"10", "ref_high":"40", "ref_text":"10–40"},
            {"name":"Alkaline Phosphatase (ALP)","unit":"U/L",  "ref_low":"44", "ref_high":"147","ref_text":"44–147"},
            {"name":"GGT",                       "unit":"U/L",  "ref_low":"9",  "ref_high":"48", "ref_text":"9–48"},
            {"name":"Total Protein",             "unit":"g/dL", "ref_low":"6.0","ref_high":"8.3","ref_text":"6.0–8.3"},
            {"name":"Albumin",                   "unit":"g/dL", "ref_low":"3.5","ref_high":"5.0","ref_text":"3.5–5.0"},
            {"name":"Globulin",                  "unit":"g/dL", "ref_low":"2.0","ref_high":"3.5","ref_text":"2.0–3.5"},
            {"name":"A/G Ratio",                 "unit":"",     "ref_low":"1.0","ref_high":"2.2","ref_text":"1.0–2.2"},
        ],
        "Kidney Function Tests (KFTs)": [
            {"name":"Serum Urea",               "unit":"mg/dL",        "ref_low":"15", "ref_high":"45",  "ref_text":"15–45"},
            {"name":"BUN",                      "unit":"mg/dL",        "ref_low":"7",  "ref_high":"20",  "ref_text":"7–20"},
            {"name":"Serum Creatinine",         "unit":"mg/dL",        "ref_low":"0.7","ref_high":"1.2", "ref_text":"0.7–1.2 (M) / 0.5–1.0 (F)"},
            {"name":"eGFR",                     "unit":"mL/min/1.73m²","ref_low":"90", "ref_high":"",    "ref_text":"> 90 Normal"},
            {"name":"Serum Uric Acid",          "unit":"mg/dL",        "ref_low":"2.4","ref_high":"7.0", "ref_text":"3.5–7.2 (M) / 2.4–6.1 (F)"},
            {"name":"Serum Sodium (Na+)",       "unit":"mEq/L",        "ref_low":"136","ref_high":"145", "ref_text":"136–145"},
            {"name":"Serum Potassium (K+)",     "unit":"mEq/L",        "ref_low":"3.5","ref_high":"5.1", "ref_text":"3.5–5.1"},
            {"name":"Serum Chloride (Cl-)",     "unit":"mEq/L",        "ref_low":"98", "ref_high":"107", "ref_text":"98–107"},
            {"name":"Serum Bicarbonate (HCO3)", "unit":"mEq/L",        "ref_low":"22", "ref_high":"29",  "ref_text":"22–29"},
            {"name":"Serum Calcium (Ca2+)",     "unit":"mg/dL",        "ref_low":"8.5","ref_high":"10.5","ref_text":"8.5–10.5"},
            {"name":"Serum Phosphorus",         "unit":"mg/dL",        "ref_low":"2.5","ref_high":"4.5", "ref_text":"2.5–4.5"},
            {"name":"Serum Magnesium",          "unit":"mg/dL",        "ref_low":"1.7","ref_high":"2.2", "ref_text":"1.7–2.2"},
        ],
        "Lipid Profile": [
            {"name":"Total Cholesterol",           "unit":"mg/dL","ref_low":"",  "ref_high":"200","ref_text":"Desirable < 200"},
            {"name":"Triglycerides",               "unit":"mg/dL","ref_low":"",  "ref_high":"150","ref_text":"Normal < 150"},
            {"name":"HDL Cholesterol",             "unit":"mg/dL","ref_low":"40","ref_high":"",   "ref_text":"> 40 (M) / > 50 (F)"},
            {"name":"LDL Cholesterol",             "unit":"mg/dL","ref_low":"",  "ref_high":"100","ref_text":"Optimal < 100"},
            {"name":"VLDL",                        "unit":"mg/dL","ref_low":"5", "ref_high":"40", "ref_text":"5–40"},
            {"name":"Total Cholesterol/HDL Ratio", "unit":"",     "ref_low":"",  "ref_high":"5.0","ref_text":"< 5.0"},
        ],
        "Serum Amylase": [{"name":"Serum Amylase","unit":"U/L","ref_low":"28","ref_high":"100","ref_text":"28–100"}],
        "Serum Lipase":  [{"name":"Serum Lipase", "unit":"U/L","ref_low":"10","ref_high":"140","ref_text":"10–140"}],
        "Serum LDH":     [{"name":"LDH",          "unit":"U/L","ref_low":"140","ref_high":"280","ref_text":"140–280"}],
    },
    "CARDIAC MARKERS": {
        "Troponin I": [{"name":"Troponin I","unit":"ng/mL","ref_low":"","ref_high":"0.04","ref_text":"< 0.04 ng/mL"}],
        "Troponin T": [{"name":"Troponin T","unit":"ng/mL","ref_low":"","ref_high":"0.01","ref_text":"< 0.01 ng/mL"}],
        "CK-MB":      [{"name":"CK-MB",     "unit":"U/L",  "ref_low":"","ref_high":"25",  "ref_text":"< 25 U/L"}],
        "BNP":        [{"name":"BNP",       "unit":"pg/mL","ref_low":"","ref_high":"100", "ref_text":"< 100 pg/mL"}],
        "NT-proBNP":  [{"name":"NT-proBNP", "unit":"pg/mL","ref_low":"","ref_high":"125", "ref_text":"< 125 pg/mL"}],
    },
    "THYROID FUNCTION": {
        "Thyroid Function Tests (TFTs)": [
            {"name":"TSH",          "unit":"µIU/mL","ref_low":"0.4", "ref_high":"4.0", "ref_text":"0.4–4.0"},
            {"name":"Free T3 (fT3)","unit":"pg/mL", "ref_low":"2.3", "ref_high":"4.2", "ref_text":"2.3–4.2"},
            {"name":"Free T4 (fT4)","unit":"ng/dL", "ref_low":"0.89","ref_high":"1.76","ref_text":"0.89–1.76"},
            {"name":"Total T3",     "unit":"ng/dL", "ref_low":"80",  "ref_high":"200", "ref_text":"80–200"},
            {"name":"Total T4",     "unit":"µg/dL", "ref_low":"5.0", "ref_high":"12.0","ref_text":"5.0–12.0"},
        ],
        "Anti-TPO Antibodies":         [{"name":"Anti-TPO",           "unit":"IU/mL","ref_low":"","ref_high":"35", "ref_text":"< 35 IU/mL"}],
        "Anti-Thyroglobulin (Anti-TG)":[{"name":"Anti-Thyroglobulin", "unit":"IU/mL","ref_low":"","ref_high":"115","ref_text":"< 115 IU/mL"}],
    },
    "HORMONES": {
        "FSH & LH": [
            {"name":"FSH","unit":"mIU/mL","ref_low":"","ref_high":"","ref_text":"M:1.5–12.4 / F(Foll):3.5–12.5"},
            {"name":"LH", "unit":"mIU/mL","ref_low":"","ref_high":"","ref_text":"M:1.7–8.6 / F(Foll):2.4–12.6"},
        ],
        "Prolactin":               [{"name":"Prolactin",        "unit":"ng/mL", "ref_low":"","ref_high":"","ref_text":"M:2–18 / F:2–29"}],
        "Testosterone":            [{"name":"Total Testosterone","unit":"ng/dL", "ref_low":"","ref_high":"","ref_text":"M:270–1070 / F:15–70"}],
        "Oestradiol (E2)":         [{"name":"Oestradiol (E2)",  "unit":"pg/mL", "ref_low":"","ref_high":"","ref_text":"F(Foll):19–144 / M:10–40"}],
        "Progesterone":            [{"name":"Progesterone",     "unit":"ng/mL", "ref_low":"","ref_high":"","ref_text":"Luteal:1.8–24.0 / Follicular:0.1–0.9"}],
        "DHEA-S":                  [{"name":"DHEA-Sulphate",    "unit":"µg/dL", "ref_low":"","ref_high":"","ref_text":"M(19-29yr):280–640 / F:65–380"}],
        "Cortisol":                [{"name":"Cortisol (AM)",    "unit":"µg/dL", "ref_low":"6.2","ref_high":"19.4","ref_text":"6.2–19.4 (AM)"}],
        "Insulin":                 [{"name":"Fasting Insulin",  "unit":"µIU/mL","ref_low":"2.6","ref_high":"24.9","ref_text":"2.6–24.9"}],
        "Beta-hCG (Quantitative)": [{"name":"Beta-hCG",        "unit":"mIU/mL","ref_low":"","ref_high":"5","ref_text":"< 5 (Non-pregnant)"}],
    },
    "VITAMINS & MINERALS": {
        "Vitamin D (25-OH)": [{"name":"25-OH Vitamin D",    "unit":"ng/mL","ref_low":"30","ref_high":"100","ref_text":"Sufficient:30–100 / Deficient:< 20"}],
        "Vitamin B12":       [{"name":"Vitamin B12",        "unit":"pg/mL","ref_low":"200","ref_high":"900","ref_text":"200–900"}],
        "Folate":            [{"name":"Serum Folate",       "unit":"ng/mL","ref_low":"2.7","ref_high":"17.0","ref_text":"2.7–17.0"}],
        "Iron Studies": [
            {"name":"Serum Iron",            "unit":"µg/dL","ref_low":"60","ref_high":"170","ref_text":"60–170 (M) / 50–170 (F)"},
            {"name":"TIBC",                  "unit":"µg/dL","ref_low":"240","ref_high":"450","ref_text":"240–450"},
            {"name":"Transferrin Saturation","unit":"%",    "ref_low":"20","ref_high":"50", "ref_text":"20–50"},
        ],
        "Serum Ferritin": [{"name":"Serum Ferritin","unit":"ng/mL","ref_low":"","ref_high":"","ref_text":"M:24–336 / F:11–307"}],
        "Zinc":           [{"name":"Serum Zinc",   "unit":"µg/dL","ref_low":"70","ref_high":"120","ref_text":"70–120"}],
    },
    "SEROLOGY / IMMUNOLOGY": {
        "HBsAg":               [{"name":"HBsAg",             "unit":"","ref_low":"","ref_high":"","ref_text":"Non-Reactive"}],
        "Anti-HCV":            [{"name":"Anti-HCV",          "unit":"","ref_low":"","ref_high":"","ref_text":"Non-Reactive"}],
        "Anti-HAV IgM":        [{"name":"Anti-HAV IgM",      "unit":"","ref_low":"","ref_high":"","ref_text":"Non-Reactive"}],
        "HIV 1 & 2":           [{"name":"HIV 1 & 2 Ab",      "unit":"","ref_low":"","ref_high":"","ref_text":"Non-Reactive"}],
        "VDRL (Syphilis)":     [{"name":"VDRL",              "unit":"","ref_low":"","ref_high":"","ref_text":"Non-Reactive"}],
        "Widal Test": [
            {"name":"S. typhi O",     "unit":"","ref_low":"","ref_high":"","ref_text":"< 1:40"},
            {"name":"S. typhi H",     "unit":"","ref_low":"","ref_high":"","ref_text":"< 1:40"},
            {"name":"S. paratyphi AO","unit":"","ref_low":"","ref_high":"","ref_text":"< 1:40"},
            {"name":"S. paratyphi BH","unit":"","ref_low":"","ref_high":"","ref_text":"< 1:40"},
        ],
        "Typhidot": [
            {"name":"Typhidot IgM","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
            {"name":"Typhidot IgG","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
        ],
        "CRP":               [{"name":"CRP",             "unit":"mg/L","ref_low":"","ref_high":"6.0","ref_text":"< 6.0 mg/L"}],
        "hs-CRP":            [{"name":"hs-CRP",          "unit":"mg/L","ref_low":"","ref_high":"1.0","ref_text":"Low risk < 1.0 / High risk > 3.0"}],
        "ASO Titre":         [{"name":"ASO Titre",       "unit":"IU/mL","ref_low":"","ref_high":"200","ref_text":"< 200 IU/mL"}],
        "Rheumatoid Factor": [{"name":"Rheumatoid Factor","unit":"IU/mL","ref_low":"","ref_high":"14","ref_text":"< 14 IU/mL"}],
        "ANA":               [{"name":"ANA",             "unit":"","ref_low":"","ref_high":"","ref_text":"Negative"}],
        "Anti-dsDNA":        [{"name":"Anti-dsDNA",      "unit":"IU/mL","ref_low":"","ref_high":"30","ref_text":"< 30 IU/mL"}],
        "Dengue NS1 Antigen":[{"name":"Dengue NS1 Ag",   "unit":"","ref_low":"","ref_high":"","ref_text":"Negative"}],
        "Dengue IgM / IgG": [
            {"name":"Dengue IgM","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
            {"name":"Dengue IgG","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
        ],
        "Malaria Antigen (RDT)": [
            {"name":"P. falciparum Ag","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
            {"name":"P. vivax Ag",     "unit":"","ref_low":"","ref_high":"","ref_text":"Negative"},
        ],
        "COVID-19 Antigen":  [{"name":"SARS-CoV-2 Ag",  "unit":"","ref_low":"","ref_high":"","ref_text":"Negative"}],
        "H. pylori Antigen": [{"name":"H. pylori Stool Ag","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"}],
    },
    "URINE ANALYSIS": {
        "Urine Routine Examination (Urine RE)": [
            {"name":"Colour",            "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Pale Yellow"},
            {"name":"Appearance",        "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Clear"},
            {"name":"pH",                "unit":"",      "ref_low":"4.5",  "ref_high":"8.0",  "ref_text":"4.5–8.0"},
            {"name":"Specific Gravity",  "unit":"",      "ref_low":"1.005","ref_high":"1.030","ref_text":"1.005–1.030"},
            {"name":"Protein",           "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Glucose",           "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Ketones",           "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Blood",             "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Bilirubin",         "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Urobilinogen",      "unit":"EU/dL", "ref_low":"0.1",  "ref_high":"1.0",  "ref_text":"0.1–1.0"},
            {"name":"Nitrite",           "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"Leucocyte Esterase","unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Negative"},
            {"name":"WBCs (Pus Cells)",  "unit":"/HPF",  "ref_low":"0",    "ref_high":"5",    "ref_text":"0–5 /HPF"},
            {"name":"RBCs",              "unit":"/HPF",  "ref_low":"0",    "ref_high":"2",    "ref_text":"0–2 /HPF"},
            {"name":"Epithelial Cells",  "unit":"/HPF",  "ref_low":"",     "ref_high":"",     "ref_text":"Occasional"},
            {"name":"Casts",             "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Nil"},
            {"name":"Crystals",          "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Nil"},
            {"name":"Bacteria",          "unit":"",      "ref_low":"",     "ref_high":"",     "ref_text":"Nil"},
        ],
        "Urine Culture & Sensitivity (C/S)": [
            {"name":"Culture Result",    "unit":"",      "ref_low":"","ref_high":"","ref_text":"No Growth"},
            {"name":"Colony Count",      "unit":"CFU/mL","ref_low":"","ref_high":"","ref_text":"< 10^5 (Insignificant)"},
            {"name":"Organism Identified","unit":"",     "ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"",     "ref_low":"","ref_high":"","ref_text":""},
        ],
        "Urine Microalbumin": [{"name":"Microalbumin (Spot)","unit":"mg/L","ref_low":"","ref_high":"30","ref_text":"< 30 mg/L"}],
    },
    "STOOL ANALYSIS": {
        "Stool Routine Examination (Stool RE)": [
            {"name":"Colour",           "unit":"",    "ref_low":"","ref_high":"","ref_text":"Brown"},
            {"name":"Consistency",      "unit":"",    "ref_low":"","ref_high":"","ref_text":"Formed"},
            {"name":"Blood",            "unit":"",    "ref_low":"","ref_high":"","ref_text":"Absent"},
            {"name":"Mucus",            "unit":"",    "ref_low":"","ref_high":"","ref_text":"Absent"},
            {"name":"Pus Cells (WBCs)", "unit":"/HPF","ref_low":"","ref_high":"","ref_text":"Nil"},
            {"name":"RBCs",             "unit":"/HPF","ref_low":"","ref_high":"","ref_text":"Nil"},
            {"name":"Ova / Cysts",      "unit":"",    "ref_low":"","ref_high":"","ref_text":"Not seen"},
            {"name":"Trophozoites",     "unit":"",    "ref_low":"","ref_high":"","ref_text":"Not seen"},
        ],
        "Stool Occult Blood":         [{"name":"Faecal Occult Blood","unit":"","ref_low":"","ref_high":"","ref_text":"Negative"}],
        "Stool Culture & Sensitivity":[
            {"name":"Culture Result",    "unit":"","ref_low":"","ref_high":"","ref_text":"No Pathogenic Growth"},
            {"name":"Organism Identified","unit":"","ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
    },
    "MICROBIOLOGY": {
        "Sputum Culture & Sensitivity":[
            {"name":"Gram Stain",        "unit":"","ref_low":"","ref_high":"","ref_text":""},
            {"name":"Culture Result",    "unit":"","ref_low":"","ref_high":"","ref_text":"No Growth"},
            {"name":"Organism Identified","unit":"","ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
        "Blood Culture & Sensitivity":[
            {"name":"Culture Result",    "unit":"","ref_low":"","ref_high":"","ref_text":"No Growth (after 5 days)"},
            {"name":"Organism Identified","unit":"","ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
        "AFB Smear (Sputum for TB)":[
            {"name":"ZN Stain — Smear 1","unit":"","ref_low":"","ref_high":"","ref_text":"No AFB seen"},
            {"name":"ZN Stain — Smear 2","unit":"","ref_low":"","ref_high":"","ref_text":"No AFB seen"},
            {"name":"ZN Stain — Smear 3","unit":"","ref_low":"","ref_high":"","ref_text":"No AFB seen"},
        ],
        "Throat Swab Culture":[
            {"name":"Culture Result",    "unit":"","ref_low":"","ref_high":"","ref_text":"No Pathogenic Growth"},
            {"name":"Organism Identified","unit":"","ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
        "Wound Swab Culture":[
            {"name":"Gram Stain",        "unit":"","ref_low":"","ref_high":"","ref_text":""},
            {"name":"Culture Result",    "unit":"","ref_low":"","ref_high":"","ref_text":"No Pathogenic Growth"},
            {"name":"Organism Identified","unit":"","ref_low":"","ref_high":"","ref_text":"None"},
            {"name":"Sensitivity Pattern","unit":"","ref_low":"","ref_high":"","ref_text":""},
        ],
    },
    "TUMOUR MARKERS": {
        "PSA (Prostate Specific Antigen)":[
            {"name":"Total PSA",          "unit":"ng/mL","ref_low":"","ref_high":"4.0","ref_text":"< 4.0 ng/mL"},
            {"name":"Free PSA",           "unit":"ng/mL","ref_low":"","ref_high":"",   "ref_text":""},
            {"name":"Free/Total PSA Ratio","unit":"%",   "ref_low":"25","ref_high":"", "ref_text":"> 25% Low cancer risk"},
        ],
        "CEA":    [{"name":"CEA",   "unit":"ng/mL","ref_low":"","ref_high":"5.0","ref_text":"< 5.0 Non-smoker / < 10.0 Smoker"}],
        "AFP":    [{"name":"AFP",   "unit":"ng/mL","ref_low":"","ref_high":"8.1","ref_text":"< 8.1 ng/mL"}],
        "CA-125": [{"name":"CA-125","unit":"U/mL", "ref_low":"","ref_high":"35", "ref_text":"< 35 U/mL"}],
        "CA 19-9":[{"name":"CA 19-9","unit":"U/mL","ref_low":"","ref_high":"37", "ref_text":"< 37 U/mL"}],
        "CA 15-3":[{"name":"CA 15-3","unit":"U/mL","ref_low":"","ref_high":"30", "ref_text":"< 30 U/mL"}],
    },
    "SEMEN ANALYSIS": {
        "Semen Analysis":[
            {"name":"Volume",               "unit":"mL",      "ref_low":"1.5","ref_high":"",   "ref_text":"≥ 1.5 mL"},
            {"name":"Colour",               "unit":"",        "ref_low":"",   "ref_high":"",   "ref_text":"Greyish-White / Opalescent"},
            {"name":"Viscosity",            "unit":"",        "ref_low":"",   "ref_high":"",   "ref_text":"Liquefied within 60 min"},
            {"name":"pH",                   "unit":"",        "ref_low":"7.2","ref_high":"8.0","ref_text":"7.2–8.0"},
            {"name":"Sperm Concentration",  "unit":"×10^6/mL","ref_low":"16", "ref_high":"",   "ref_text":"≥ 16 ×10^6/mL"},
            {"name":"Total Sperm Count",    "unit":"×10^6",   "ref_low":"39", "ref_high":"",   "ref_text":"≥ 39 ×10^6"},
            {"name":"Total Motility (PR+NP)","unit":"%",      "ref_low":"42", "ref_high":"",   "ref_text":"≥ 42%"},
            {"name":"Progressive Motility", "unit":"%",       "ref_low":"30", "ref_high":"",   "ref_text":"≥ 30%"},
            {"name":"Immotile",             "unit":"%",       "ref_low":"",   "ref_high":"58", "ref_text":"≤ 58%"},
            {"name":"Normal Morphology",    "unit":"%",       "ref_low":"4",  "ref_high":"",   "ref_text":"≥ 4% (Kruger strict)"},
            {"name":"WBCs (Leukocytes)",    "unit":"×10^6/mL","ref_low":"",   "ref_high":"1.0","ref_text":"< 1.0 ×10^6/mL"},
            {"name":"Impression",           "unit":"",        "ref_low":"",   "ref_high":"",   "ref_text":""},
        ],
    },
}


def get_full_catalog():
    s = load_settings()
    catalog = {g: dict(t) for g, t in BUILTIN_CATALOG.items()}
    for group, tests in s.get("custom_tests", {}).items():
        catalog.setdefault(group, {}).update(tests)
    return catalog


def compute_flag(result_str, ref_low, ref_high):
    try:
        v = float(result_str)
        lo = float(ref_low)  if ref_low  else None
        hi = float(ref_high) if ref_high else None
        if lo is not None and v < lo: return "L"
        if hi is not None and v > hi: return "H"
        return ""
    except: return ""


def step_bar(current):
    steps = ["Patient","Tests","Results","Report"]
    html = '<div class="step-bar">'
    for i,s in enumerate(steps):
        n = i+1
        if n < current:   cls,lc,icon = "done","done","✓"
        elif n == current: cls,lc,icon = "active","active",str(n)
        else:              cls,lc,icon = "idle","",str(n)
        html += f'<div class="step-item"><div class="step-circle {cls}">{icon}</div><div class="step-label {lc}">{s}</div></div>'
        if i < len(steps)-1:
            ll = "done" if n < current else ""
            html += f'<div class="step-line {ll}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def top_bar(title=""):
    s = load_settings()
    c1,c2,c3 = st.columns([3,1,1])
    with c1:
        st.markdown(f'<div style="font-weight:700;color:#1a1a2e;font-size:1rem;">🔬 {s["lab_name"]}</div>', unsafe_allow_html=True)
    with c2:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.prev_step = st.session_state.step
            st.session_state.step = "settings"
            st.rerun()
    with c3:
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    st.markdown('<hr style="border:none;border-top:1px solid #e5e7eb;margin:6px 0 16px 0;">', unsafe_allow_html=True)


# ── PDF ────────────────────────────────────────────────────────────────────────
def generate_pdf(patient, report_rows, report_no, s):
    buf   = BytesIO()
    NAVY  = colors.HexColor("#1a1a2e")
    BLACK = colors.HexColor("#111827")
    LGRAY = colors.HexColor("#f3f4f6")
    WHITE = colors.white
    print_header = s.get("print_header", True)
    lab_name     = s.get("lab_name",    "Shah Lab & Diagnostics")
    lab_address  = s.get("lab_address", "")
    lab_phone    = s.get("lab_phone",   "")

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=0.6*cm,  bottomMargin=1.5*cm)
    W = A4[0] - 3.6*cm
    story = []

    # Header
    if print_header:
        name_style = ParagraphStyle("ln", fontName="Helvetica-Bold", fontSize=16,
                                    textColor=NAVY, alignment=TA_RIGHT, leading=20)
        sub_style  = ParagraphStyle("ls", fontName="Helvetica", fontSize=8,
                                    textColor=colors.HexColor("#374151"), alignment=TA_RIGHT, leading=12)

        # Drawn microscope logo
        def make_microscope(size=52):
            d = Drawing(size, size)
            nc = colors.HexColor("#1a1a2e")
            # Base
            d.add(Rect(size*0.25, size*0.04, size*0.50, size*0.08, fillColor=nc, strokeColor=None))
            # Stand pole
            d.add(Rect(size*0.44, size*0.12, size*0.12, size*0.30, fillColor=nc, strokeColor=None))
            # Arm
            d.add(Rect(size*0.28, size*0.38, size*0.44, size*0.09, fillColor=nc, strokeColor=None))
            # Body tube (vertical)
            d.add(Rect(size*0.38, size*0.46, size*0.14, size*0.28, fillColor=nc, strokeColor=None))
            # Eyepiece (top)
            d.add(Rect(size*0.34, size*0.74, size*0.22, size*0.08, fillColor=nc, strokeColor=None))
            d.add(Rect(size*0.40, size*0.82, size*0.10, size*0.10, fillColor=nc, strokeColor=None))
            # Objective lens (bottom)
            d.add(Ellipse(size*0.45, size*0.42, size*0.12, size*0.06, fillColor=nc, strokeColor=None))
            # Stage (horizontal plate)
            d.add(Rect(size*0.18, size*0.34, size*0.54, size*0.06, fillColor=nc, strokeColor=None))
            return d

        logo_drawing = make_microscope(52)

        right_col = [Paragraph(lab_name, name_style)]
        if lab_address: right_col.append(Paragraph(lab_address, sub_style))
        if lab_phone:   right_col.append(Paragraph(f"Tel: {lab_phone}", sub_style))

        hdr = Table([[logo_drawing, right_col]], colWidths=[W*0.13, W*0.87])
        hdr.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(hdr)
        story.append(HRFlowable(width=W, thickness=2, color=NAVY))
        story.append(Spacer(1, 0.3*cm))
    else:
        story.append(Table([[""]], colWidths=[W], rowHeights=[3.8*cm]))
        story.append(Spacer(1, 0.3*cm))

    # Patient info
    def lbl(t): return Paragraph(f'<font name="Helvetica-Bold" size="8">{t}</font>', ParagraphStyle("l",leading=13))
    def val(t): return Paragraph(f'<font name="Helvetica" size="9">{t or "—"}</font>', ParagraphStyle("v",leading=13))
    info = [
        [lbl("Patient Name:"), val(patient["name"]),   lbl("Age / Gender:"), val(f"{patient['age']} / {patient['gender']}")],
        [lbl("Ref. Doctor:"),  val(patient["doctor"]), lbl("Contact:"),       val(patient["contact"])],
        [lbl("Sample Date:"),  val(patient["sample"]), lbl("Report Date:"),   val(patient["rdate"])],
        [lbl("Report No.:"),   val(report_no),          lbl(""),               val("")],
    ]
    it = Table(info, colWidths=[W*0.18,W*0.32,W*0.18,W*0.32])
    it.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),3),
                            ("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),0)]))
    story.append(it)
    story.append(Spacer(1,0.2*cm))
    story.append(HRFlowable(width=W,thickness=2,color=NAVY))
    story.append(Spacer(1,0.3*cm))

    # Results
    col_w = [W*0.37,W*0.18,W*0.13,W*0.32]
    def th(t): return Paragraph(f'<font name="Helvetica-Bold" size="8.5" color="#1a1a2e">{t}</font>', ParagraphStyle("th",alignment=TA_LEFT))
    def cell(t,bold=False,color="#111827"):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        return Paragraph(f'<font name="{fn}" size="8" color="{color}">{t}</font>', ParagraphStyle("c",alignment=TA_LEFT,leading=11))

    rows   = [[th("Parameter"),th("Result"),th("Unit"),th("Reference Range")]]
    styles = []
    ri     = 1
    groups = {}
    for row in report_rows:
        groups.setdefault((row["test_group"],row["test_name"]),[]).append(row)

    for (group,tname),params in groups.items():
        rows.append([Paragraph(f'<font name="Helvetica-Bold" size="8" color="#ffffff">{group} — {tname}</font>',
                               ParagraphStyle("sh",alignment=TA_LEFT)),"","",""])
        styles += [("SPAN",(0,ri),(3,ri)),("BACKGROUND",(0,ri),(3,ri),NAVY),
                   ("TOPPADDING",(0,ri),(3,ri),5),("BOTTOMPADDING",(0,ri),(3,ri),5)]
        ri += 1
        for p in params:
            flag = p["flag"]; rv = p["result"] or "—"
            if   flag=="H": rc=cell(f"{rv} H",bold=True,color="#dc2626"); pc=cell(p["parameter"],bold=True)
            elif flag=="L": rc=cell(f"{rv} L",bold=True,color="#2563eb"); pc=cell(p["parameter"],bold=True)
            else:           rc=cell(rv);                                    pc=cell(p["parameter"])
            rows.append([pc,rc,cell(p["unit"]),cell(p["ref_text"])])
            bg = colors.HexColor("#f9fafb") if ri%2==0 else WHITE
            styles += [("BACKGROUND",(0,ri),(3,ri),bg),("TOPPADDING",(0,ri),(3,ri),4),("BOTTOMPADDING",(0,ri),(3,ri),4)]
            ri += 1

    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,0),(-1,0),LGRAY),
        ("LINEBELOW",(0,0),(-1,0),2,NAVY),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#e5e7eb")),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
    ]+styles))
    story.append(tbl)
    story.append(Spacer(1,0.8*cm))

    # Signatures
    sig = ParagraphStyle("sig",fontName="Helvetica",fontSize=8,textColor=BLACK,alignment=TA_CENTER)
    st2 = Table([[
        Paragraph("______________________<br/>Lab Technologist Signature",sig),
        Paragraph("",sig),
        Paragraph("______________________<br/>Pathologist / In-charge Stamp",sig),
    ]], colWidths=[W*0.36,W*0.28,W*0.36])
    st2.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"BOTTOM"),("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story.append(st2)
    story.append(Spacer(1,0.3*cm))
    story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#d1d5db")))
    story.append(Spacer(1,0.15*cm))
    story.append(Paragraph(
        f'<font name="Helvetica" size="7" color="#9ca3af">Report No. {report_no} | {patient["rdate"]} | {lab_name}</font>',
        ParagraphStyle("ft",alignment=TA_CENTER)))
    doc.build(story)
    return buf.getvalue()


# ── Session init ───────────────────────────────────────────────────────────────
for k,v in [("step","login"),("patient",{}),("selected_tests",[]),
            ("report_rows",[]),("report_counter",1),("prev_step","patient"),
            ("new_params",[])]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "login":
    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1.4,1])
    with c2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:28px;">
          <div style="font-size:2.8rem;">🔬</div>
          <div style="font-size:1.5rem;font-weight:700;color:#1a1a2e;">Shah Lab & Diagnostics</div>
          <div style="font-size:0.82rem;color:#6b7280;margin-top:4px;">Laboratory Management System</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### Sign In")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if username == "admin" and password == "shahlab2024":
                    st.session_state.step = "patient"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "settings":
    s = load_settings()
    hc1,hc2 = st.columns([5,1])
    with hc1:
        st.markdown('<div class="section-heading">⚙️ Settings</div>', unsafe_allow_html=True)
    with hc2:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = st.session_state.get("prev_step","patient")
            st.rerun()

    tab1, tab2 = st.tabs(["🏥 General", "🧪 Test Catalog"])

    # ── General ────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### Lab Information")
        lab_name    = st.text_input("Lab Name",    value=s["lab_name"])
        lab_address = st.text_input("Address",     value=s.get("lab_address",""))
        lab_phone   = st.text_input("Phone",       value=s.get("lab_phone",""))

        st.markdown("#### Default Print Mode")
        print_header = st.radio(
            "Default print mode",
            options=["🔬 With Header (logo + lab name + address + phone)",
                     "📄 Without Header (blank space for pre-printed letterhead)"],
            index=0 if s["print_header"] else 1,
            label_visibility="collapsed",
        )
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            s["lab_name"]     = lab_name.strip() or "Shah Lab & Diagnostics"
            s["lab_address"]  = lab_address.strip()
            s["lab_phone"]    = lab_phone.strip()
            s["print_header"] = print_header.startswith("🔬")
            save_settings(s)
            st.success("✅ Settings saved!")

    # ── Test Catalog ────────────────────────────────────────────────────────────
    with tab2:
        custom = s.get("custom_tests", {})

        # ADD NEW TEST
        st.markdown("#### ➕ Add New Test")
        with st.container(border=True):
            all_groups = list(BUILTIN_CATALOG.keys())
            custom_groups = [g for g in custom if g not in BUILTIN_CATALOG]
            group_options = all_groups + custom_groups + ["➕ Create New Group"]

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                selected_group = st.selectbox("Test Group", group_options, key="sel_group")
            with col_g2:
                new_group_name = ""
                if selected_group == "➕ Create New Group":
                    new_group_name = st.text_input("New Group Name", placeholder="e.g. ALLERGY TESTS", key="new_grp_name")

            test_name_input = st.text_input("Test Name *", placeholder="e.g. Vitamin C Level", key="new_test_name")

            st.markdown("**Add Parameters:**")
            p1,p2,p3,p4,p5 = st.columns([3,1.5,1,1,2])
            pname = p1.text_input("Parameter Name *", key="add_pname", label_visibility="collapsed", placeholder="Parameter name")
            punit = p2.text_input("Unit",             key="add_punit", label_visibility="collapsed", placeholder="Unit")
            plow  = p3.text_input("Low",              key="add_plow",  label_visibility="collapsed", placeholder="Low")
            phigh = p4.text_input("High",             key="add_phigh", label_visibility="collapsed", placeholder="High")
            pref  = p5.text_input("Reference Text",   key="add_pref",  label_visibility="collapsed", placeholder="Reference text")

            ba, bb = st.columns([1,3])
            with ba:
                if st.button("+ Add Parameter", use_container_width=True):
                    if pname.strip():
                        st.session_state.new_params.append({
                            "name":pname.strip(),"unit":punit.strip(),
                            "ref_low":plow.strip(),"ref_high":phigh.strip(),
                            "ref_text":pref.strip()
                        })
                        st.rerun()
                    else:
                        st.warning("Parameter name is required.")

            if st.session_state.new_params:
                st.markdown("**Parameters to be saved:**")
                for i,p in enumerate(st.session_state.new_params):
                    rc1,rc2 = st.columns([6,1])
                    rc1.markdown(f"`{i+1}.` **{p['name']}** | {p['unit']} | {p['ref_low']}–{p['ref_high']} | _{p['ref_text']}_")
                    if rc2.button("✕", key=f"rm_{i}", use_container_width=True):
                        st.session_state.new_params.pop(i)
                        st.rerun()

            st.markdown("")
            if st.button("💾 Save This Test", type="primary", use_container_width=True):
                final_group = new_group_name.strip().upper() if selected_group == "➕ Create New Group" else selected_group
                if not test_name_input.strip():
                    st.error("Test name is required.")
                elif not final_group:
                    st.error("Please select or create a group.")
                elif not st.session_state.new_params:
                    st.error("Add at least one parameter.")
                else:
                    custom.setdefault(final_group, {})
                    custom[final_group][test_name_input.strip()] = st.session_state.new_params
                    s["custom_tests"] = custom
                    save_settings(s)
                    st.session_state.new_params = []
                    st.success(f"✅ Test '{test_name_input.strip()}' saved to '{final_group}'!")
                    st.rerun()

        # EDIT / DELETE CUSTOM TESTS
        if custom:
            st.markdown("---")
            st.markdown("#### ✏️ Edit / Delete Custom Tests")
            for group, tests in list(custom.items()):
                st.markdown(f"**{group}**")
                for test_name, params in list(tests.items()):
                    with st.expander(f"📋 {test_name} ({len(params)} parameters)"):
                        updated_params = []
                        for i,p in enumerate(params):
                            st.markdown(f"**Parameter {i+1}**")
                            ec1,ec2,ec3,ec4,ec5 = st.columns([3,1.5,1,1,2])
                            upname = ec1.text_input("Name",  value=p["name"],     key=f"e_n_{group}_{test_name}_{i}", label_visibility="collapsed")
                            upunit = ec2.text_input("Unit",  value=p["unit"],     key=f"e_u_{group}_{test_name}_{i}", label_visibility="collapsed")
                            uplow  = ec3.text_input("Low",   value=p["ref_low"],  key=f"e_l_{group}_{test_name}_{i}", label_visibility="collapsed")
                            uphigh = ec4.text_input("High",  value=p["ref_high"], key=f"e_h_{group}_{test_name}_{i}", label_visibility="collapsed")
                            upref  = ec5.text_input("Ref",   value=p["ref_text"], key=f"e_r_{group}_{test_name}_{i}", label_visibility="collapsed")
                            updated_params.append({
                                "name":upname,"unit":upunit,
                                "ref_low":uplow,"ref_high":uphigh,"ref_text":upref
                            })

                        cs1,cs2 = st.columns(2)
                        with cs1:
                            if st.button("💾 Save Changes", key=f"sv_{group}_{test_name}", use_container_width=True, type="primary"):
                                custom[group][test_name] = updated_params
                                s["custom_tests"] = custom
                                save_settings(s)
                                st.success("✅ Changes saved!")
                        with cs2:
                            if st.button("🗑️ Delete Test", key=f"dl_{group}_{test_name}", use_container_width=True):
                                del custom[group][test_name]
                                if not custom[group]:
                                    del custom[group]
                                s["custom_tests"] = custom
                                save_settings(s)
                                st.warning(f"Deleted '{test_name}'")
                                st.rerun()
        else:
            st.info("No custom tests yet. Add one above.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — PATIENT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "patient":
    top_bar()
    step_bar(1)
    st.markdown('<div class="section-heading">Patient Details</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Enter patient information before selecting tests</div>', unsafe_allow_html=True)

    with st.form("patient_form"):
        c1,c2 = st.columns(2)
        name   = c1.text_input("Full Name *",      placeholder="e.g. Muhammad Imran")
        gender = c2.selectbox("Gender *",          ["Male","Female","Other"])
        c3,c4  = st.columns(2)
        age    = c3.text_input("Age *",            placeholder="e.g. 35 / 6 months")
        contact= c4.text_input("Contact",          placeholder="e.g. 0300-1234567")
        c5,c6  = st.columns(2)
        doctor = c5.text_input("Referring Doctor", placeholder="e.g. Dr. Ayesha Khan")
        sample = c6.date_input("Sample Date",      value=date.today())
        st.markdown("")
        go = st.form_submit_button("Next — Select Tests →", type="primary", use_container_width=True)

    if go:
        if not name.strip() or not age.strip():
            st.error("Name and Age are required.")
        else:
            st.session_state.patient = {
                "name":name.strip(),"age":age.strip(),"gender":gender,
                "contact":contact.strip(),"doctor":doctor.strip(),
                "sample":sample.isoformat(),"rdate":datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.step = "tests"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — TESTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "tests":
    top_bar()
    step_bar(2)
    st.markdown('<div class="section-heading">Select Tests</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Search and choose one or more tests</div>', unsafe_allow_html=True)

    p = st.session_state.patient
    with st.container(border=True):
        c1,c2,c3 = st.columns(3)
        c1.markdown(f"**{p['name']}**")
        c2.markdown(f"{p['age']} / {p['gender']}")
        c3.markdown(f"Dr. {p['doctor'] or '—'}")

    catalog   = get_full_catalog()
    all_tests = []
    group_map = {}
    for group,tests in catalog.items():
        for t in tests:
            all_tests.append(t)
            group_map[t] = group

    selected = st.multiselect("Search tests", options=all_tests,
                               default=st.session_state.selected_tests,
                               placeholder="Type to search — CBC, LFT, TSH, Urine RE...")
    st.markdown("")
    cb,cn = st.columns([1,2])
    with cb:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "patient"; st.rerun()
    with cn:
        if st.button("Next — Enter Results →", type="primary",
                     use_container_width=True, disabled=len(selected)==0):
            st.session_state.selected_tests = selected
            st.session_state.group_map      = group_map
            st.session_state.catalog        = catalog
            st.session_state.step           = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "results":
    top_bar()
    step_bar(3)
    st.markdown('<div class="section-heading">Enter Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Fill in values — abnormal results are flagged automatically</div>', unsafe_allow_html=True)

    p = st.session_state.patient
    with st.container(border=True):
        c1,c2,c3 = st.columns(3)
        c1.markdown(f"**{p['name']}**")
        c2.markdown(f"{p['age']} / {p['gender']}")
        c3.markdown(f"Dr. {p['doctor'] or '—'}")

    st.markdown("---")
    all_rows  = []
    catalog   = st.session_state.get("catalog", get_full_catalog())
    group_map = st.session_state.get("group_map", {})

    for test_name in st.session_state.selected_tests:
        group  = group_map.get(test_name,"")
        params = catalog.get(group,{}).get(test_name,[])
        st.markdown(f"<span style='font-weight:600;color:#1a1a2e;'>{test_name}</span>&nbsp;<span style='color:#6b7280;font-size:0.8rem;'>{group}</span>", unsafe_allow_html=True)

        hc = st.columns([3,2,1.5,3])
        hc[0].markdown("<small><b>Parameter</b></small>",       unsafe_allow_html=True)
        hc[1].markdown("<small><b>Result</b></small>",          unsafe_allow_html=True)
        hc[2].markdown("<small><b>Unit</b></small>",            unsafe_allow_html=True)
        hc[3].markdown("<small><b>Reference Range</b></small>", unsafe_allow_html=True)

        for param in params:
            key = f"r__{test_name}__{param['name']}"
            pc  = st.columns([3,2,1.5,3])
            pc[0].markdown(f"<small>{param['name']}</small>", unsafe_allow_html=True)
            result = pc[1].text_input(param["name"], key=key, label_visibility="collapsed", placeholder="—")
            pc[2].markdown(f"<small>{param['unit']}</small>",     unsafe_allow_html=True)
            pc[3].markdown(f"<small>{param['ref_text']}</small>", unsafe_allow_html=True)
            flag = compute_flag(result, param["ref_low"], param["ref_high"])
            if   flag=="H": pc[1].markdown("<small style='color:#dc2626;'>▲ High</small>", unsafe_allow_html=True)
            elif flag=="L": pc[1].markdown("<small style='color:#2563eb;'>▼ Low</small>",  unsafe_allow_html=True)
            all_rows.append({"test_group":group,"test_name":test_name,"parameter":param["name"],
                             "result":result,"unit":param["unit"],"ref_low":param["ref_low"],
                             "ref_high":param["ref_high"],"ref_text":param["ref_text"],"flag":flag})
        st.markdown("---")

    cb,cs = st.columns([1,2])
    with cb:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = "tests"; st.rerun()
    with cs:
        if st.button("Preview & Download Report →", type="primary", use_container_width=True):
            filled = [r for r in all_rows if r["result"].strip()]
            if not filled: st.error("Enter at least one result value.")
            else:
                st.session_state.report_rows = filled
                st.session_state.step        = "report"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "report":
    top_bar()
    step_bar(4)
    st.markdown('<div class="section-heading">Report Preview</div>', unsafe_allow_html=True)

    s         = load_settings()
    p         = st.session_state.patient
    rows      = st.session_state.report_rows
    report_no = f"SL-{st.session_state.report_counter:05d}"

    hdr_choice = st.radio(
        "Print mode",
        options=["🔬 With Header","📄 Without Header (pre-printed letterhead)"],
        index=0 if s["print_header"] else 1,
        horizontal=True, label_visibility="collapsed",
    )
    s["print_header"] = hdr_choice.startswith("🔬")

    st.markdown("")
    ca,cb,cc = st.columns([1.5,1.5,2])
    with ca:
        pdf_bytes = generate_pdf(p, rows, report_no, s)
        b64  = base64.b64encode(pdf_bytes).decode()
        fname = f"ShahLab_{p['name'].replace(' ','_')}_{report_no}.pdf"
        st.markdown(
            f'<a href="data:application/pdf;base64,{b64}" download="{fname}">'
            f'<button style="width:100%;padding:10px 0;background:#1a1a2e;color:#fff;'
            f'border:none;border-radius:8px;cursor:pointer;font-size:0.9rem;font-weight:600;">'
            f'📥 Download PDF</button></a>', unsafe_allow_html=True)
    with cb:
        if st.button("🖨️ Print", use_container_width=True):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    with cc:
        if st.button("➕ New Patient Report", type="primary", use_container_width=True):
            st.session_state.report_counter += 1
            st.session_state.step           = "patient"
            st.session_state.patient        = {}
            st.session_state.selected_tests = []
            st.session_state.report_rows    = []
            st.rerun()

    st.markdown("---")
    st.markdown('<style>@media print{.no-print,.stButton,.stRadio,[data-testid="stToolbar"]{display:none!important;}}</style>', unsafe_allow_html=True)

    # On-screen preview
    groups = {}
    for row in rows:
        groups.setdefault((row["test_group"],row["test_name"]),[]).append(row)

    tbody = ""
    for (group,tname),params in groups.items():
        tbody += f'<tr><td colspan="4" style="background:#1a1a2e;color:#fff;font-weight:600;padding:7px 12px;font-size:0.82rem;">{group} — {tname}</td></tr>'
        for param in params:
            flag=param["flag"]; bold="font-weight:700;" if flag in("H","L") else ""
            rv=param["result"] or "—"
            fh = ' <span style="color:#dc2626;font-weight:700;">▲H</span>' if flag=="H" else \
                 ' <span style="color:#2563eb;font-weight:700;">▼L</span>' if flag=="L" else ""
            tbody += f'<tr><td style="padding:6px 12px;">{param["parameter"]}</td><td style="padding:6px 12px;{bold}">{rv}{fh}</td><td style="padding:6px 12px;color:#6b7280;">{param["unit"]}</td><td style="padding:6px 12px;">{param["ref_text"]}</td></tr>'

    if s["print_header"]:
        header_html = f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
          <div style="font-size:2.4rem;">🔬</div>
          <div style="text-align:right;">
            <div style="font-size:1.25rem;font-weight:700;color:#1a1a2e;">{s['lab_name']}</div>
            <div style="font-size:0.78rem;color:#374151;">{s.get('lab_address','')}</div>
            <div style="font-size:0.78rem;color:#374151;">Tel: {s.get('lab_phone','')}</div>
          </div>
        </div>
        <hr style="border:none;border-top:2px solid #1a1a2e;margin:0 0 14px 0;">"""
    else:
        header_html = '<div style="height:120px;margin-bottom:20px;"></div>'

    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
        padding:36px 44px;max-width:780px;margin:0 auto;
        font-family:'Inter',Arial,sans-serif;font-size:0.88rem;color:#111827;
        box-shadow:0 2px 16px rgba(0,0,0,0.06);">
      {header_html}
      <table style="width:100%;border-collapse:collapse;margin-bottom:14px;">
        <tr>
          <td style="width:50%;padding:3px 0;"><b>Patient Name:</b> {p['name']}</td>
          <td style="width:50%;padding:3px 0;"><b>Age / Gender:</b> {p['age']} / {p['gender']}</td>
        </tr>
        <tr>
          <td style="padding:3px 0;"><b>Referring Doctor:</b> {p['doctor'] or '—'}</td>
          <td style="padding:3px 0;"><b>Contact:</b> {p['contact'] or '—'}</td>
        </tr>
        <tr>
          <td style="padding:3px 0;"><b>Sample Date:</b> {p['sample']}</td>
          <td style="padding:3px 0;"><b>Report Date:</b> {p['rdate']}</td>
        </tr>
        <tr>
          <td style="padding:3px 0;"><b>Report No.:</b> {report_no}</td>
          <td></td>
        </tr>
      </table>
      <hr style="border:none;border-top:2px solid #1a1a2e;margin:12px 0 16px 0;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#f3f4f6;">
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #1a1a2e;width:35%;">Parameter</th>
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #1a1a2e;width:18%;">Result</th>
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #1a1a2e;width:12%;">Unit</th>
            <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #1a1a2e;">Reference Range</th>
          </tr>
        </thead>
        <tbody>{tbody}</tbody>
      </table>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0 18px 0;">
      <div style="display:flex;justify-content:space-between;margin-top:40px;">
        <div style="text-align:center;width:38%;">
          <div style="border-top:1px solid #374151;padding-top:6px;font-size:0.8rem;color:#374151;">Lab Technologist Signature</div>
        </div>
        <div style="text-align:center;width:38%;">
          <div style="border-top:1px solid #374151;padding-top:6px;font-size:0.8rem;color:#374151;">Pathologist / In-charge Stamp</div>
        </div>
      </div>
      <div style="text-align:center;margin-top:24px;color:#9ca3af;font-size:0.75rem;">
        {report_no} &nbsp;|&nbsp; {p['rdate']} &nbsp;|&nbsp; <b style="color:#1a1a2e;">{s['lab_name']}</b>
      </div>
    </div>
    """, unsafe_allow_html=True)