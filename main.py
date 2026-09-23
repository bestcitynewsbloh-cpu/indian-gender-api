import os
import re
import json
import joblib
from functools import lru_cache
from typing import List
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="Indic & Bengali Enterprise Hybrid Gender Engine")

# ==========================================
# 1. SUPABASE CLIENT SETUP
# ==========================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase connection warning: {e}")

# ==========================================
# 2. IN-MEMORY ASSETS & CORPUS
# ==========================================
DB_MALE = set()
DB_FEMALE = set()
ml_model = None

@app.on_event("startup")
def load_all_assets():
    global DB_MALE, DB_FEMALE, ml_model

    # 1. Primary names_db.json file loading
    for db_file in ["names_db.json", "names_db_2.json"]:
        if os.path.exists(db_file):
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if "male" in data:
                            DB_MALE.update([str(x).lower().strip() for x in data["male"] if x])
                        if "female" in data:
                            DB_FEMALE.update([str(x).lower().strip() for x in data["female"] if x])
                print(f"Loaded {len(DB_MALE)} Male and {len(DB_FEMALE)} Female names from {db_file}")
                break
            except Exception as e:
                print(f"Error loading {db_file}: {e}")

    # Fallback for separate files if present
    if not DB_MALE and os.path.exists("male_names.json"):
        try:
            with open("male_names.json", "r", encoding="utf-8") as f:
                DB_MALE.update([str(x).lower().strip() for x in json.load(f) if x])
        except Exception as e:
            print(f"Error loading male_names.json: {e}")

    if not DB_FEMALE and os.path.exists("female_names.json"):
        try:
            with open("female_names.json", "r", encoding="utf-8") as f:
                DB_FEMALE.update([str(x).lower().strip() for x in json.load(f) if x])
        except Exception as e:
            print(f"Error loading female_names.json: {e}")

    # Load ML Model
    if os.path.exists("gender_model.pkl"):
        try:
            ml_model = joblib.load("gender_model.pkl")
            print("ML model pipeline loaded successfully.")
        except Exception as e:
            print(f"Error loading ML model: {e}")

    # Load User Feedbacks into live memory
    if os.path.exists("user_feedbacks.json"):
        try:
            with open("user_feedbacks.json", "r", encoding="utf-8") as f:
                saved_feedbacks = json.load(f)
                for nm, g in saved_feedbacks.items():
                    clean_nm = str(nm).lower().strip()
                    if g == "Male":
                        DB_MALE.add(clean_nm)
                        DB_FEMALE.discard(clean_nm)
                    elif g == "Female":
                        DB_FEMALE.add(clean_nm)
                        DB_MALE.discard(clean_nm)
        except Exception as e:
            print(f"Error syncing feedbacks on startup: {e}")

# ==========================================
# 3. RULE-BASED PATTERNS
# ==========================================
FEMALE_TOKENS = {
    "begum", "khatun", "bibi", "devi", "kumari", "shree", "sri",
    "rani", "banu", "bai", "amma", "mati", "moni"
}

# Sirf strict male middle names / honorifics (Surnames excluded)
MALE_EXCLUSIVE_TOKENS = {
    "kumar", "prasad", "kant", "lal", "mohan", "kishore", "babu", "da"
}

MALE_PREFIXES = (
    "deb", "shib", "som", "ram", "subh", "soum", "swar",
    "abhr", "indr", "chandr", "sur", "bhab", "prab"
)

MALE_SUFFIXES = (
    "esh", "ish", "raj", "deep", "dip", "brata", "moy", "may",
    "jit", "jeet", "endu", "anshu", "ayan", "ankar", "kanta",
    "tosh", "ndra", "bhanu", "dhar", "kar", "vanta", "want",
    "man", "dev", "deb", "ananda", "ratna", "ranjan", "swarup"
)

FEMALE_SUFFIXES = (
    "wati", "vati", "mati", "mita", "tika", "ika", "ita", "isha", "priya",
    "shree", "sri", "lata", "mala", "bala", "dita", "purna", "lekha", "shila",
    "rekha", "nita", "jani", "shikha", "rupa", "dharini", "nandini", "sunita",
    "eena", "ina", "usrat", "shrat", "khat", "smat", "enat", "nnat", "reen",
    "nam", "sum", "yeen", "reen", "min", "rin", "qis", "gis", "heen", "har",
    "taz", "naz"
)

HONORIFIC_REGEX = r'^(mr|mrs|ms|dr|shri|smt|miss|prof|master)\.?\s+'

# ==========================================
# 4. REQUEST SCHEMAS
# ==========================================
class PredictRequest(BaseModel):
    name: str

class BatchPredictRequest(BaseModel):
    names: List[str]

class FeedbackRequest(BaseModel):
    name: str
    correct_gender: str

# ==========================================
# 5. CORE CLASSIFICATION ENGINE
# ==========================================
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

    # Step 1: 100% Female Tokens / Suffixes anywhere in the name (Highest Priority)
    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"

    # Step 2: Exact Database Match on First Name
    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    # Step 3: Male Middle Tokens (e.g. Kumar, Prasad) - Only on middle/last tokens
    for t in tokens[1:]:
        if t in MALE_EXCLUSIVE_TOKENS:
            return "Male"

    # Step 4: Strict Male Prefix Guards
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    # Step 5: Structural Suffixes
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"
    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"

    # Step 6: Terminal -u in Bengali / Indian names
    if token.endswith("u"):
        return "Male"

    # Step 7: Scikit-Learn Model Prediction
    if ml_model is not None:
        try:
            prediction = ml_model.predict([token])[0]
            return prediction
        except Exception:
            pass

    # Step 8: Heuristic Fallbacks
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
# 6. LICENSE & CREDIT SYSTEM
# ==========================================
def verify_and_deduct_credits(api_key: str, cost: int):
    if not supabase:
        return True

    res = supabase.table("api_licenses").select("*").eq("api_key", api_key).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid License Key")

    client_record = res.data[0]
    if not client_record.get("is_active", False):
        raise HTTPException(status_code=403, detail="License key is deactivated")

    remaining = client_record.get("credits_remaining", 0)
    if remaining < cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. Required: {cost}, Remaining: {remaining}"
        )

    supabase.table("api_licenses").update(
        {"credits_remaining": remaining - cost}
    ).eq("api_key", api_key).execute()
    
    return True

# ==========================================
# 7. API ENDPOINTS
# ==========================================
@app.get("/")
def home():
    return {
        "status": "Live",
        "engine": "Hybrid (Rules + Database + Scikit-Learn ML + License Engine)",
        "total_male_in_db": len(DB_MALE),
        "total_female_in_db": len(DB_FEMALE),
        "total_corpus": len(DB_MALE) + len(DB_FEMALE),
        "ml_model_loaded": ml_model is not None,
        "supabase_connected": supabase is not None
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
def predict_batch(req: BatchPredictRequest, x_api_key: str = Header(...)):
    verify_and_deduct_credits(x_api_key, len(req.names))
    return [{"name": nm, "gender": evaluate_gender(nm)} for nm in req.names]

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
