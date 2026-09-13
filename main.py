import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Indian Bengali Name Gender Predictor API")

class PredictRequest(BaseModel):
    name: str

class PredictResponse(BaseModel):
    input: str
    first_name: str
    gender: str
    confidence: float
    probabilities: dict
    reason: str

# 1. Unisex / Ambiguous Bengali Names
UNISEX_NAMES = {
    "kiran", "deep", "snehal", "tapas", "chandan", "shashi", "milon", "shumon"
}

# 2. Bengali Male Names ending with -a / -o (jo regular models me female ban jaate hain)
BENGALI_MALE_SPECIAL = {
    "abhinaba", "abhinob", "subrata", "debabrata", "satyabrata", "soumya", 
    "sukanta", "shantanu", "santanab", "tanmoy", "chinmoy", "mrinal", "arka", 
    "rana", "anupam", "pranab", "biplab", "sourav", "saurav", "anirban",
    "indranil", "nilanjan", "partha", "sukomal", "dipankar", "subhas", 
    "subhash", "kalyan", "prosenjit", "prasenjit", "subhashis", "debjit"
}

# 3. Explicit Male Names (Common West Bengal / Bangladesh / Pan-India)
MALE_NAMES = {
    "aayush", "ayush", "abdul", "abhijit", "abhijoy", "abhinav", "abhinesh", 
    "abhirup", "abhishek", "abdhesh", "avdhesh", "rahul", "amit", "rajesh", 
    "suresh", "vikram", "rohan", "arjun", "sachin", "prateek", "diptesh", 
    "krishna", "gaurav", "manoj", "vijay", "ajay", "sanjay", "anil", "sunil", 
    "deepak", "rakesh", "ashok", "dinesh", "pankaj", "mukesh", "alok", "vivek", 
    "varun", "kunal", "sumit", "sourabh", "imran", "rohit", "aman", "ankit", 
    "mohit", "vicky", "nitin", "mayank", "ravi", "basit", "tathagata", "saptarshi",
    "buddhadeb", "debashis", "ashis", "avisek", "avishek", "shouvik", "souvik"
}

# 4. Explicit Female Names (Bengali & Indian)
FEMALE_NAMES = {
    "abantika", "avantika", "pooja", "priya", "ananya", "sunita", "deepika", 
    "kavita", "roshni", "meera", "swati", "tanvi", "aaradhya", "shruti", 
    "neha", "sneha", "aarti", "divya", "anjali", "riya", "simran", "shreya", 
    "payal", "komal", "pallavi", "radha", "seema", "rekha", "geeta", "monika", 
    "sonam", "preeti", "jyoti", "nisha", "rashmi", "mamta", "sapna", "kajal", 
    "vandana", "alka", "renu", "bhavna", "moumita", "debapriya", "madhumita", 
    "anindita", "paramita", "sarmistha", "sharmistha", "piyali", "ruma", 
    "chhanda", "sampa", "kakoli", "baishakhi", "sucharita", "monalisa", "titas"
}

# 5. Distinct Bengali Male Suffixes
BENGALI_MALE_SUFFIXES = (
    "jit", "jeet", "joy", "rup", "bhab", "bhabh", "brata", "kanta", "kanti",
    "sekhar", "shekhar", "moy", "moyee", "shis", "shish", "bhadra", "kumar", 
    "esh", "kant", "anand", "dev", "deb", "nath", "dhar", "pal", "singh", 
    "nav", "bhan", "lal", "das", "prasad", "ram", "chand", "veer", "ul", 
    "it", "ik", "ak", "av", "ey", "am", "sh", "ay", "ab", "ban", "ron", "ran"
)

# 6. Distinct Bengali Female Suffixes
BENGALI_FEMALE_SUFFIXES = (
    "mita", "tika", "tikaa", "ika", "ita", "isha", "priya", "shree", "sri", 
    "mati", "wati", "devi", "kumari", "lata", "mala", "bala", "dita", "purna", 
    "lekha", "shila", "rekha", "nita", "jani", "shikha", "rupa"
)

def clean_token(name: str) -> str:
    name = name.lower().strip()
    # Strip titles and honorary prefixes
    name = re.sub(r'^(mr|mrs|ms|dr|shri|smt|md|mohd|sheikh|sk)\.?\s+', '', name)
    first_token = re.split(r'[\s\-]+', name)[0]
    return re.sub(r'[^a-z]', '', first_token)

@app.get("/")
def home():
    return {"status": "Live", "docs": "/docs"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    token = clean_token(req.name)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid name")

    # 1. Unisex Check
    if token in UNISEX_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Unisex",
            "confidence": 0.50,
            "probabilities": {"Male": 0.5, "Female": 0.5},
            "reason": "Known unisex Bengali name"
        }

    # 2. Bengali special male names ending with -a/-o
    if token in BENGALI_MALE_SPECIAL:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Male",
            "confidence": 0.99,
            "probabilities": {"Male": 0.99, "Female": 0.01},
            "reason": "Bengali masculine vowel-ending pattern"
        }

    # 3. Direct Dictionary Match
    if token in MALE_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Male",
            "confidence": 0.99,
            "probabilities": {"Male": 0.99, "Female": 0.01},
            "reason": "Dictionary verified male"
        }

    if token in FEMALE_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Female",
            "confidence": 0.99,
            "probabilities": {"Male": 0.01, "Female": 0.99},
            "reason": "Dictionary verified female"
        }

    # 4. Common Islamic Prefix Check (e.g. Abdul, Md, Sheikh)
    if token.startswith("abdul") or token.startswith("mohd") or token.startswith("md") or token.startswith("sk"):
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Male",
            "confidence": 0.98,
            "probabilities": {"Male": 0.98, "Female": 0.02},
            "reason": "Prefix pattern match"
        }

    # 5. Bengali Suffix Engine
    for suffix in BENGALI_FEMALE_SUFFIXES:
        if token.endswith(suffix):
            return {
                "input": req.name,
                "first_name": token,
                "gender": "Female",
                "confidence": 0.94,
                "probabilities": {"Male": 0.06, "Female": 0.94},
                "reason": f"Female suffix match (-{suffix})"
            }

    for suffix in BENGALI_MALE_SUFFIXES:
        if token.endswith(suffix):
            return {
                "input": req.name,
                "first_name": token,
                "gender": "Male",
                "confidence": 0.95,
                "probabilities": {"Male": 0.95, "Female": 0.05},
                "reason": f"Male suffix match (-{suffix})"
            }

    # 6. Fallback logic
    # Bengali female names often end in -i, -ee, -a (unless caught by male special)
    if token.endswith("i") or token.endswith("ee") or token.endswith("a"):
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Female",
            "confidence": 0.72,
            "probabilities": {"Male": 0.28, "Female": 0.72},
            "reason": "Feminine phonetic ending"
        }

    return {
        "input": req.name,
        "first_name": token,
        "gender": "Male",
        "confidence": 0.75,
        "probabilities": {"Male": 0.75, "Female": 0.25},
        "reason": "Masculine consonant ending"
    }
