import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Advanced Pan-Indian & Bengali Gender Classification Engine")

# ==========================================
# 1. DATA STRUCTURES & LINGUISTIC DICTIONARIES
# ==========================================

# Direct High-Confidence Female Name Corpus
FEMALE_CORPUS = {
    # Bengali specific female names
    "moumita", "debapriya", "madhumita", "anindita", "paramita", "sarmistha", 
    "sharmistha", "piyali", "ruma", "chhanda", "sampa", "kakoli", "baishakhi", 
    "sucharita", "monalisa", "titas", "swarnali", "barnali", "sayani", "soma", 
    "rupali", "jhuma", "mousumi", "tanusree", "tanushree", "subhashree", 
    "debaleena", "indrani", "chaitali", "basanti", "paoli", "payel", "rituparna",
    "bhaswati", "shrabani", "sraban", "arati", "arundhati", "sutapa", "shampa",
    # Pan-Indian / Hindi / Vedic
    "pooja", "priya", "ananya", "sunita", "deepika", "kavita", "roshni", "meera", 
    "swati", "tanvi", "aaradhya", "shruti", "neha", "sneha", "aarti", "divya", 
    "anjali", "riya", "simran", "shreya", "payal", "komal", "pallavi", "radha", 
    "seema", "rekha", "geeta", "monika", "sonam", "preeti", "jyoti", "nisha", 
    "rashmi", "mamta", "sapna", "kajal", "vandana", "alka", "renu", "bhavna",
    "abantika", "avantika", "ishita", "sakshi", "kriti", "shweta", "garima",
    "mansi", "mahima", "diksha", "deeksha", "prachi", "kanchan", "sheetal",
    # Modern / Anglo / Pet names ending in -y, -i, -ee
    "ruby", "dolly", "pinky", "rinky", "sweety", "mary", "lily", "daisy", 
    "simy", "bobby", "munni", "baby", "tina", "rina", "mina", "sheena",
    # Islamic / Bengali Muslim Female
    "fatima", "fatema", "ayesha", "khadija", "yasmin", "yasmine", "parveen", 
    "sultana", "nasrin", "farhana", "roksana", "tanzila", "salma", "shabnam", 
    "rehana", "shahana", "tasnim", "afreen", "nargis", "samina", "tahmina",
    "razia", "asifa", "rabia", "sumaiya", "zoya", "bushra", "saima"
}

# Direct High-Confidence Male Name Corpus
MALE_CORPUS = {
    # Bengali Masculine names ending in -a / -o (Vowel paradox)
    "abhinaba", "abhinob", "subrata", "debabrata", "satyabrata", "soumya", 
    "sukanta", "shantanu", "tanmoy", "chinmoy", "mrinal", "arka", "rana", 
    "anupam", "pranab", "biplab", "sourav", "saurav", "anirban", "indranil", 
    "nilanjan", "partha", "sukomal", "dipankar", "subhas", "subhash", "kalyan", 
    "prosenjit", "prasenjit", "subhashis", "debjit", "tathagata", "saptarshi",
    "buddhadeb", "debashis", "ashis", "avisek", "avishek", "shouvik", "souvik",
    "supratim", "debrup", "shubhankar", "tamal", "kallol", "somnath", "sanjay",
    # Pan-Indian Masculine Names
    "aayush", "ayush", "abdul", "abhijit", "abhijoy", "abhinav", "abhinesh", 
    "abhirup", "abhishek", "abdhesh", "avdhesh", "rahul", "amit", "rajesh", 
    "suresh", "vikram", "rohan", "arjun", "sachin", "prateek", "diptesh", 
    "krishna", "gaurav", "manoj", "vijay", "ajay", "anil", "sunil", "deepak", 
    "rakesh", "ashok", "dinesh", "pankaj", "mukesh", "alok", "vivek", "varun", 
    "kunal", "sumit", "sourabh", "imran", "rohit", "aman", "ankit", "mohit", 
    "vicky", "nitin", "mayank", "ravi", "ram", "sham", "shyam", "ilyas", "elias",
    # Islamic Male Names & Surnames used as First
    "mohammed", "mohammad", "muhammad", "ahmed", "ahmad", "tariq", "rashid", 
    "arif", "shahid", "zahid", "waseem", "nadeem", "mustafa", "murtaza", "saif",
    "aslam", "farhan", "salman", "rizwan", "altaf", "iqbal", "firoz", "tanvir"
}

# Unisex / Ambiguous names
UNISEX_NAMES = {
    "kiran", "deep", "snehal", "tapas", "chandan", "shashi", "milon", 
    "harpreet", "gurpreet", "jaspreet", "manpreet", "amrit", "sonu", "shumon"
}

# High-Precision Female Suffixes
FEMALE_SUFFIXES = (
    "wati", "vati", "mati", "kumari", "devi", "khatun", "bibi", "begum", "banu", 
    "mita", "tika", "tikaa", "ika", "ita", "isha", "priya", "shree", "sri", 
    "lata", "mala", "bala", "dita", "purna", "lekha", "shila", "rekha", "nita", 
    "jani", "shikha", "rupa", "rani", "mani", "dharini", "nandini", "sundari",
    "parveen", "nisa", "unissa", "tara"
)

# High-Precision Male Suffixes
# Note: 'oy', 'ey', 'ay' handle names like Abhijoy, Joy, Tanmoy, Chinmoy, Binoy
MALE_SUFFIXES = (
    "kumar", "chandra", "nath", "prasad", "singh", "babu", "da", "lal", "das",
    "ram", "jit", "jeet", "joy", "rup", "bhab", "brata", "kanta", "kanti", 
    "sekhar", "shekhar", "moy", "shis", "shish", "bhadra", "esh", "kant", 
    "anand", "dev", "deb", "dhar", "pal", "nav", "bhan", "veer", "ul", "it", 
    "ik", "ak", "av", "am", "sh", "ay", "ab", "ban", "ron", "ran", "oy", "ey"
)

# Titles / Prefix lists
MALE_PREFIXES = ("abdul", "mohd", "mohammad", "md", "sk", "sheikh", "syed", "ghulam")
HONORIFIC_PREFIXES = r'^(mr|mrs|ms|dr|shri|smt|miss|prof|master)\.?\s+'

# ==========================================
# 2. CORE LINGUISTIC EVALUATION PIPELINE
# ==========================================

class PredictRequest(BaseModel):
    name: str

class PredictResponse(BaseModel):
    input: str
    first_name: str
    gender: str
    confidence: float
    probabilities: dict
    reason: str

class BatchPredictRequest(BaseModel):
    names: List[str]

def normalize_name(raw_name: str):
    clean = raw_name.lower().strip()
    clean = re.sub(HONORIFIC_PREFIXES, '', clean)
    tokens = [re.sub(r'[^a-z]', '', t) for t in re.split(r'[\s\-]+', clean) if t]
    first_token = tokens[0] if tokens else ""
    return tokens, first_token

def evaluate_gender(raw_name: str):
    tokens, token = normalize_name(raw_name)
    if not token:
        return "Unknown", 0.0, "Invalid name"

    # --- LEVEL 1: Full-Name Token Inspection (Surnames / Secondary Markers) ---
    for t in tokens:
        if t in {"devi", "kumari", "khatun", "bibi", "begum", "banu", "ara", "parveen"}:
            return "Female", 0.99, f"Deterministic female honorific/token ({t})"
        if t in {"kumar", "chandra", "nath", "prasad", "das", "singh", "lal"}:
            return "Male", 0.98, f"Deterministic male middle/suffix token ({t})"

    # --- LEVEL 2: Unisex & Exact Corpus Matches ---
    if token in UNISEX_NAMES:
        return "Unisex", 0.50, "Recognized unisex name"

    if token in FEMALE_CORPUS:
        return "Female", 0.99, "Corpus verified female"

    if token in MALE_CORPUS:
        return "Male", 0.99, "Corpus verified male"

    # --- LEVEL 3: Distinct Male Prefix Check ---
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male", 0.98, f"Male prefix rule ({pref})"

    # --- LEVEL 4: Morphological Suffix Match ---
    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female", 0.95, f"Feminine morphological suffix (-{sfx})"

    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male", 0.95, f"Masculine morphological suffix (-{sfx})"

    # --- LEVEL 5: English Suffix Rule for Indian Names ---
    # Words ending in 'y' like Ruby, Dolly, Pinky, Rinky, Sweety
    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female", 0.90, "Feminine diminutive suffix (-y)"

    # Female vowel endings (-i, -ee, -aa)
    if token.endswith("i") or token.endswith("ee") or token.endswith("aa"):
        return "Female", 0.82, "Feminine phonetic vocalic ending"

    # Bengali male single 'a' exceptions vs standard 'a'
    if token.endswith("a"):
        # If preceded by certain conjuncts (e.g., -rta, -bha, -nya, -tya, -rka)
        if re.search(r'(rta|bha|nya|tya|rka|nda|mba|rya|pta|tra)$', token):
            return "Male", 0.85, "Bengali Sanskrit masculine conjunct ending in -a"
        return "Female", 0.70, "Open vocalic -a ending"

    # Consonant terminal (overwhelmingly male in Indic scripts)
    return "Male", 0.78, "Terminal consonant indicator"

# ==========================================
# 3. FASTAPI ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {"status": "Live", "engine": "Indic-Linguistic-v3", "docs": "/docs"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    _, first_token = normalize_name(req.name)
    gender, conf, reason = evaluate_gender(req.name)
    
    p_male = conf if gender == "Male" else round(1.0 - conf, 3)
    p_female = conf if gender == "Female" else round(1.0 - conf, 3)
    if gender == "Unisex":
        p_male, p_female = 0.50, 0.50

    return {
        "input": req.name,
        "first_name": first_token,
        "gender": gender,
        "confidence": conf,
        "probabilities": {"Male": p_male, "Female": p_female},
        "reason": reason
    }

@app.post("/predict-batch")
def predict_batch(req: BatchPredictRequest):
    output = []
    for nm in req.names:
        g, c, _ = evaluate_gender(nm)
        output.append({"name": nm, "gender": g, "confidence": c})
    return output
