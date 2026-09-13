import os
import json
import re
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Indic & Bengali Enterprise Gender Engine")

DB_MALE = set()
DB_FEMALE = set()

# Server start hote hi local 38K+ names_db.json load karega
@app.on_event("startup")
def load_database():
    global DB_MALE, DB_FEMALE
    json_path = "names_db.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                DB_MALE = set(data.get("male", []))
                DB_FEMALE = set(data.get("female", []))
            print(f"Loaded {len(DB_MALE)} Male and {len(DB_FEMALE)} Female names from {json_path}")
        except Exception as e:
            print(f"Error loading {json_path}: {e}")

    # Core explicit overrides taaki edge-cases hamesha 100% accurate rahein
    DB_MALE.update([
        "sudhansu", "raju", "bablu", "bismu", "bishu", "desbandhu", "desbondhu", "laltu", "nuru",
        "pinku", "mintu", "titu", "pintu", "dukha", "sarabindu", "somu", "shanu", "suvendu",
        "pappu", "sonu", "santanu", "arnab", "mantu", "anjisnu", "batul", "priyansu", "nintu",
        "sirsendu", "diglu", "saju", "nihar", "sukhendu", "gullu", "soumendu", "dibyatanu",
        "abhimanyu", "ribhu", "riju", "ratul", "nehru", "puspendu", "roki", "toni", "bisnu",
        "gauranga", "surja", "mani", "sabasachi", "sabyasachi", "parsanta", "saugata",
        "hari", "rajarshi", "sunny", "banty", "bharat", "susanta", "arkaprava",
        "bubai", "roni", "naveen", "anthony", "bapi", "sushanta", "kanhaiya", "raja",
        "chowdhury", "praveen", "prashant", "prashanta", "ali", "imran", "ilyas"
    ])
    DB_FEMALE.update([
        "zainab", "zaynab", "putul", "mohar", "sath", "sathi", "tithe", "chhaya", "dulu", "kiran",
        "shaheen", "poonam", "vrinda", "naheed", "sudipta", "papiya", "tabinda", "june",
        "ritu", "radha", "saranya", "rupal", "rikhiya", "tuku", "chandra", "siya",
        "swagata", "mumtaz", "mehnaz", "pratibha", "venus", "taniya", "manmun", "raziya", "sultana"
    ])

# ==========================================
# REFINED MORPHOLOGICAL RULES
# ==========================================

FEMALE_TOKENS = {
    "devi", "kumari", "khatun", "khatoon", "bibi", "begum", "banu", "bano", 
    "ara", "parvin", "nisa", "unissa", "nesa", "bai", "dasi", "mahila", 
    "khatunbibi", "sultana", "begam", "jahan"
}

MALE_EXCLUSIVE_TOKENS = {
    "kumar", "chandra", "nath", "prasad", "lal", "babu", "da", "uddin", "ullah",
    "chowdhury", "choudhury", "samaddar", "hoare"
}

MALE_PREFIXES = ("abdul", "mohd", "mohammad", "muhammad", "md", "sk", "sheikh", "syed", "ghulam", "ali")

MALE_SUFFIXES = (
    "jeet", "jit", "joy", "rup", "brata", "kanta", "kanti", "sekhar", "shekhar",
    "moy", "shis", "shish", "esh", "kant", "anand", "dev", "deb", "dhar",
    "nav", "veer", "ul", "ik", "av", "ban", "ron", "oy", "ey", "arat",
    "anthony", "prava", "rshi", "sachi", "endu", "tanu", "bindu", "bhandu", "bandhu",
    "anshu", "ansu"
)

FEMALE_SUFFIXES = (
    "wati", "vati", "mati", "mita", "tika", "ika", "ita", "isha", "priya",
    "shree", "sri", "lata", "mala", "bala", "dita", "purna", "lekha", "shila",
    "rekha", "nita", "jani", "shikha", "rupa", "dharini", "nandini", "sundari",
    "eena", "ina", "usrat", "shrat", "khat", "smat", "enat", "nnat",
    "nam", "sum", "yeen", "reen", "min", "rin", "qis", "gis", "heen", "heed",
    "taz", "naz"
)

HONORIFIC_REGEX = r'^(mr|mrs|ms|dr|shri|smt|miss|prof|master)\.?\s+'

class PredictRequest(BaseModel):
    name: str

class BatchPredictRequest(BaseModel):
    names: List[str]

def normalize_name(raw_name: str):
    clean = raw_name.lower().strip()
    clean = re.sub(HONORIFIC_REGEX, '', clean)
    tokens = [re.sub(r'[^a-z]', '', t) for t in re.split(r'[\s\-]+', clean) if t]
    first_token = tokens[0] if tokens else ""
    return tokens, first_token

def evaluate_gender(raw_name: str) -> str:
    tokens, token = normalize_name(raw_name)
    if not token:
        return "Male"

    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"

    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    for t in tokens:
        if t in MALE_EXCLUSIVE_TOKENS:
            return "Male"

    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"

    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"

    if token.endswith("a"):
        if re.search(r'(rta|nya|tya|rka|nda|mba|rya|tra|dra|ndra|ranga|prava|kha)$', token):
            return "Male"
        return "Female"

    if token.endswith("u"):
        return "Male"

    if token.endswith(("i", "ee", "aa")):
        return "Female"

    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female"

    return "Male"

@app.get("/")
def home():
    return {
        "status": "Live",
        "total_male_in_db": len(DB_MALE),
        "total_female_in_db": len(DB_FEMALE),
        "total_corpus": len(DB_MALE) + len(DB_FEMALE)
    }

@app.post("/predict")
def predict(req: PredictRequest):
    _, first_token = normalize_name(req.name)
    return {
        "input": req.name,
        "first_name": first_token,
        "gender": evaluate_gender(req.name)
    }

@app.post("/predict-batch")
def predict_batch(req: BatchPredictRequest):
    return [{"name": nm, "gender": evaluate_gender(nm)} for nm in req.names]
