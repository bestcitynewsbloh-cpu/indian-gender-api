import json
import os
import re
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Optimized Bengali & Indic Name Classifier")

# Load Local Pre-Compiled Database
DB_FILE = os.path.join(os.path.dirname(__file__), "names_db.json")

DB_MALE = set()
DB_FEMALE = set()

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        DB_MALE = set(data.get("male", []))
        DB_FEMALE = set(data.get("female", []))

# Additional fallback morphological rules
FEMALE_TOKENS = {"devi", "kumari", "khatun", "bibi", "begum", "banu", "ara", "parveen", "nisa", "unissa"}
MALE_TOKENS = {"kumar", "chandra", "nath", "prasad", "das", "singh", "lal", "babu", "da", "uddin", "ullah"}
MALE_PREFIXES = ("abdul", "mohd", "mohammad", "muhammad", "md", "sk", "sheikh", "syed", "ghulam", "ali")
FEMALE_SUFFIXES = ("wati", "vati", "mati", "mita", "tika", "ika", "ita", "isha", "priya", "shree", "sri", "lata", "mala", "bala", "dita", "purna", "lekha", "shila", "rekha", "nita", "jani", "shikha", "rupa", "rani", "mani", "dharini", "nandini", "sundari")
MALE_SUFFIXES = ("jit", "jeet", "joy", "rup", "brata", "kanta", "kanti", "sekhar", "shekhar", "moy", "shis", "shish", "esh", "kant", "anand", "dev", "deb", "dhar", "pal", "nav", "veer", "ul", "it", "ik", "ak", "av", "am", "sh", "ay", "ab", "ban", "ron", "ran", "oy", "ey")

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
        return "Unknown"

    # 1. Check direct middle/last deterministic titles
    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"
        if t in MALE_TOKENS:
            return "Male"

    # 2. Match from pre-compiled dataset
    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    # 3. Known Prefix matches
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    # 4. Suffix rules
    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"

    # 5. Phonetic heuristics for rare unseen names
    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female"

    if token.endswith("a"):
        if re.search(r'(rta|bha|nya|tya|rka|nda|mba|rya|pta|tra|dra|ndra)$', token):
            return "Male"
        return "Female"

    if token.endswith(("i", "ee", "aa")):
        return "Female"

    return "Male"

@app.get("/")
def home():
    return {
        "status": "Live", 
        "total_male_in_db": len(DB_MALE), 
        "total_female_in_db": len(DB_FEMALE)
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
