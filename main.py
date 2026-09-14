import os
import json
import re
import joblib
from functools import lru_cache
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Indic & Bengali Enterprise Hybrid Gender Engine")

DB_MALE = set()
DB_FEMALE = set()
ml_model = None

# ==========================================
# 1. STARTUP: LOAD JSON & ML MODEL
# ==========================================

@app.on_event("startup")
def load_all_assets():
    global DB_MALE, DB_FEMALE, ml_model

    # Load 38K+ JSON Database
    json_path = "names_db.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                DB_MALE = set(data.get("male", []))
                DB_FEMALE = set(data.get("female", []))
            print(f"Loaded {len(DB_MALE)} Male and {len(DB_FEMALE)} Female names from database.")
        except Exception as e:
            print(f"Error loading {json_path}: {e}")

    # Core high-priority overrides (Conflict proof)
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
        "swagata", "mumtaz", "mehnaz", "pratibha", "venus", "taniya", "manmun", "raziya", "sultana",
        "tusi", "sharmista", "shrestha", "rina", "shabnam", "poli", "auswa", "antara"
    ])

    # Load ML Model (.pkl)
    model_path = "gender_model.pkl"
    if os.path.exists(model_path):
        try:
            ml_model = joblib.load(model_path)
            print("Successfully loaded trained ML model (gender_model.pkl)!")
        except Exception as e:
            print(f"Error loading {model_path}: {e}")

# ==========================================
# 2. TOKENS & MORPHOLOGICAL GUARDS
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

class FeedbackRequest(BaseModel):
    name: str
    correct_gender: str
def normalize_name(raw_name: str):
    clean = raw_name.lower().strip()
    clean = re.sub(HONORIFIC_REGEX, '', clean)
    tokens = [re.sub(r'[^a-z]', '', t) for t in re.split(r'[\s\-]+', clean) if t]
    first_token = tokens[0] if tokens else ""
    return tokens, first_token
@lru_cache(maxsize=100000)
def evaluate_gender(raw_name: str) -> str:
    tokens, token = normalize_name(raw_name)
    if not token:
        return "Male"

    # Rule 1: Full-name honorific tokens (100% certainty)
    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"
    for t in tokens:
        if t in MALE_EXCLUSIVE_TOKENS:
            return "Male"

    # Rule 2: Database Exact Match (Zero-error lookup)
    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    # Rule 3: Strict Prefix Guards
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    # Rule 4: Structural Indian & Bengali Suffixes
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"
    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"

    # Rule 5: Terminal -u in Bengali / Indian is overwhelmingly MALE (Raju, Bablu, Pintu)
    if token.endswith("u"):
        return "Male"

    # Rule 6: Machine Learning Pipeline (Trained on 1.1 Lakh Truecaller Data)
    if ml_model is not None:
        try:
            prediction = ml_model.predict([token])[0]
            return str(prediction)
        except Exception:
            pass

    # Rule 7: Final Fallback Heuristics
    if token.endswith("a"):
        if re.search(r'(rta|nya|tya|rka|nda|mba|rya|tra|dra|ndra|ranga|prava|kha)$', token):
            return "Male"
        return "Female"

    if token.endswith(("i", "ee", "aa")):
        return "Female"

    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female"

    return "Male"

# ==========================================
# 3. FASTAPI ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {
        "status": "Live",
        "engine": "Hybrid (Rules + Database + Scikit-Learn ML)",
        "total_male_in_db": len(DB_MALE),
        "total_female_in_db": len(DB_FEMALE),
        "total_corpus": len(DB_MALE) + len(DB_FEMALE),
        "ml_model_loaded": ml_model is not None
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
    
    
    FEEDBACK_FILE = "user_feedbacks.json"

@app.post("/feedback")
def submit_feedback(data: FeedbackRequest):
    _, token = normalize_name(data.name)
    gender_input = data.correct_gender.capitalize()
    
    if not token or gender_input not in ["Male", "Female"]:
        return {"status": "error", "message": "Invalid name or gender"}

    feedbacks = {}
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        except Exception:
            feedbacks = {}

    feedbacks[token] = gender_input
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)

    if gender_input == "Male":
        DB_MALE.add(token)
        DB_FEMALE.discard(token)
    else:
        DB_FEMALE.add(token)
        DB_MALE.discard(token)

    evaluate_gender.cache_clear()

    return {
        "status": "success",
        "message": f"'{token}' ko '{gender_input}' ke roop mein save kar liya gaya hai.",
        "total_feedbacks": len(feedbacks)
    }
