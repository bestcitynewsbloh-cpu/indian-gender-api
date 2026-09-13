import os
import re
import joblib
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

model = None

# 1. High-precision curated lookup for common Indian names
FEMALE_NAMES = {
    "pooja", "priya", "ananya", "sunita", "deepika", "kavita", "roshni", "meera",
    "swati", "tanvi", "aaradhya", "shruti", "neha", "sneha", "aarti", "divya",
    "anjali", "riya", "simran", "shreya", "payal", "komal", "pallavi", "radha",
    "seema", "rekha", "geeta", "monika", "sonam", "preeti", "jyoti", "nisha",
    "rashmi", "mamta", "sapna", "kajal", "vandana", "alka", "renu", "bhavna"
}

MALE_NAMES = {
    "rahul", "amit", "rajesh", "suresh", "vikram", "rohan", "arjun", "sachin",
    "prateek", "diptesh", "krishna", "gaurav", "manoj", "vijay", "ajay", "sanjay",
    "anil", "sunil", "deepak", "rakesh", "ashok", "dinesh", "pankaj", "mukesh",
    "alok", "vivek", "abhishek", "varun", "kunal", "sumit", "sourabh", "imran",
    "rohit", "aman", "ankit", "mohit", "vicky", "nitin", "mayank", "ravi"
}

UNISEX_NAMES = {
    "kiran", "deep", "harpreet", "gurpreet", "jaspreet",
    "manpreet", "amrit", "snehal", "sonu", "shashi"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_path = "indian_gender_model.joblib"
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    yield

app = FastAPI(title="Indian Name Gender API", lifespan=lifespan)

class PredictRequest(BaseModel):
    name: str

class PredictResponse(BaseModel):
    input: str
    first_name: str
    gender: str
    confidence: float
    probabilities: dict
    reason: Optional[str] = None

def preprocess(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'^(mr|mrs|ms|dr|shri|smt)\.?\s+', '', name)
    first_token = re.split(r'\s+', name)[0]
    return re.sub(r'[^a-z]', '', first_token)

@app.get("/")
def home():
    return {"status": "Live", "docs": "/docs"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    token = preprocess(req.name)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid name")

    # Layer 1: Unisex check
    if token in UNISEX_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Unisex",
            "confidence": 0.50,
            "probabilities": {"Male": 0.5, "Female": 0.5},
            "reason": "Commonly used for both genders in Indian culture"
        }

    # Layer 2: Direct lookup for deterministic accuracy
    if token in FEMALE_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Female",
            "confidence": 0.99,
            "probabilities": {"Male": 0.01, "Female": 0.99},
            "reason": "Dictionary verified"
        }

    if token in MALE_NAMES:
        return {
            "input": req.name,
            "first_name": token,
            "gender": "Male",
            "confidence": 0.99,
            "probabilities": {"Male": 0.99, "Female": 0.01},
            "reason": "Dictionary verified"
        }

    # Layer 3: ML Model Fallback for unseen names
    if model is None:
        raise HTTPException(status_code=500, detail="Model file missing")

    probs = model.predict_proba([token])[0]
    classes = list(model.classes_)
    female_p = float(probs[classes.index("Female")])
    male_p = float(probs[classes.index("Male")])

    pred = "Female" if female_p > male_p else "Male"
    top_conf = max(female_p, male_p)

    return {
        "input": req.name,
        "first_name": token,
        "gender": pred if top_conf >= 0.65 else "Uncertain",
        "confidence": round(top_conf, 3),
        "probabilities": {"Male": round(male_p, 3), "Female": round(female_p, 3)},
        "reason": "ML pattern inference"
    }
