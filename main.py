import os
import re
import urllib.request
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Production Indic & Bengali 50K Gender Engine")

DB_MALE = set()
DB_FEMALE = set()

# Server start hone par 50,000+ names seedha official raw datasets se RAM me load honge
@app.on_event("startup")
def load_datasets():
    global DB_MALE, DB_FEMALE
    print("Loading 50,000+ Indic names from open-source datasets...")

    sources = [
        "https://raw.githubusercontent.com/anilbhatt1/Indian-Names-Dataset/master/Names_2010Census.csv",
        "https://raw.githubusercontent.com/amrrs/indian-names-gender/master/Indian-Names-Dataset-Gender.csv"
    ]

    for url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        raw_nm = re.sub(r'[^a-z]', '', parts[0].strip().lower())
                        raw_g = parts[1].strip().lower()
                        if len(raw_nm) < 2:
                            continue
                        if raw_g in ["m", "male", "boy"]:
                            DB_MALE.add(raw_nm)
                        elif raw_g in ["f", "female", "girl"]:
                            DB_FEMALE.add(raw_nm)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # Conflicts resolve karein
    conflicts = DB_MALE.intersection(DB_FEMALE)
    DB_MALE -= conflicts
    DB_FEMALE -= conflicts

    # High-Priority Bengali & Islamic Core additions
    DB_FEMALE.update([
        "zainab", "zaynab", "ruby", "dolly", "pinky", "rinky", "sweety", "maryam", 
        "mariam", "shabnam", "tabassum", "kulsum", "kalsum", "nusrat", "ishrat", 
        "nikhat", "ismat", "zeenat", "jannat", "nargis", "bilqis", "firdaus", 
        "afreen", "yasmin", "nasrin", "shirin", "parveen", "iram", "sanam",
        "akshta", "alafiya", "alankrita", "alia", "alifya", "alisha", "shameli"
    ])
    DB_MALE.update([
        "ali", "imran", "ilyas", "sham", "ram", "abhinaba", "abhinob", "abhirup", 
        "soumya", "subrata", "debabrata", "joy", "tanmoy", "chinmoy", "diptesh", 
        "krishna", "alauddin", "alishah", "alkesh"
    ])
    print(f"Dataset Loaded Successfully! Male: {len(DB_MALE)}, Female: {len(DB_FEMALE)}")

# Linguistic Fallbacks
FEMALE_TOKENS = {"devi", "kumari", "khatun", "bibi", "begum", "banu", "ara", "parveen", "nisa", "unissa"}
MALE_TOKENS = {"kumar", "chandra", "nath", "prasad", "das", "singh", "lal", "babu", "da", "uddin", "ullah"}
MALE_PREFIXES = ("abdul", "mohd", "mohammad", "muhammad", "md", "sk", "sheikh", "syed", "ghulam", "ali")
FEMALE_SUFFIXES = (
    "wati", "vati", "mati", "mita", "tika", "ika", "ita", "isha", "priya", 
    "shree", "sri", "lata", "mala", "bala", "dita", "purna", "lekha", "shila", 
    "rekha", "nita", "jani", "shikha", "rupa", "rani", "mani", "dharini", 
    "nandini", "sundari", "nab", "eena", "ina", "eet", "rat", "hat", "mat", 
    "nam", "sum", "yeen", "veen", "reen", "min", "rin", "qis", "gis"
)
MALE_SUFFIXES = (
    "jit", "jeet", "joy", "rup", "brata", "kanta", "kanti", "sekhar", "shekhar", 
    "moy", "shis", "shish", "esh", "kant", "anand", "dev", "deb", "dhar", "pal", 
    "nav", "veer", "ul", "it", "ik", "ak", "av", "am", "sh", "ay", "ab", "ban", 
    "ron", "ran", "oy", "ey"
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
        return "Unknown"

    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"
        if t in MALE_TOKENS:
            return "Male"

    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"

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
