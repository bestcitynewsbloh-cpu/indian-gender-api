import os
import re
import urllib.request
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Indic & Bengali Enterprise Gender Engine")

# ==========================================
# 1. PRESERVED HARDCODED CORPUS (ORIGINAL DATA)
# ==========================================

DB_MALE = {
    # Bengali Male Names (Including -jeet variants and Sanskrit conjunct roots)
    "abhijeet", "abhijit", "abhijoy", "abhinaba", "abhinav", "abhinob", "abhirup", "abhishek",
    "indrajeet", "ranjeet", "satyajeet", "manjeet", "surjeet", "harjeet", "baljeet",
    "subrata", "debabrata", "satyabrata", "soumya", "sukanta", "shantanu", "santanab",
    "tanmoy", "chinmoy", "mrinal", "arka", "rana", "anupam", "pranab", "biplab",
    "sourav", "saurav", "anirban", "indranil", "nilanjan", "partha", "sukomal",
    "dipankar", "subhas", "subhash", "kalyan", "prosenjit", "prasenjit", "subhashis",
    "debjit", "tathagata", "saptarshi", "buddhadeb", "debashis", "ashis", "avisek",
    "avishek", "shouvik", "souvik", "supratim", "debrup", "shubhankar", "tamal",
    "kallol", "somnath", "abhinesh", "joy", "bijoy", "sanjay", "ajay", "sujay",
    "ranajit", "biswajit", "arijit", "bappa", "barun", "basudev", "bhabesh", "bhola",
    "bibhas", "bidhan", "bikash", "bikram", "binod", "binoy", "biren", "chandan",
    "chayan", "chittaranjan", "dhiman", "dilip", "dipak", "dulal", "haradhan",
    "jayanta", "koustav", "mainak", "manas", "manik", "mithun", "monir", "mousam",
    "niloy", "nirmal", "paresh", "pinaki", "prabhat", "prabir", "pradip", "pramod",
    "pritom", "purnendu", "rabin", "rajat", "rajib", "ritam", "saikat", "samar",
    "samrat", "sandip", "sanjoy", "sankar", "santu", "satyajit", "shankha", "shashank",
    "shirish", "siddhartha", "soham", "sougata", "soumyajit", "subal", "subhabrata",
    "subhadip", "subham", "subir", "subodh", "suhas", "sujan", "sukhen", "suman",
    "surajit", "surya", "swapan", "swarup", "tanmay", "tapan", "tapas", "tarun",
    "tuhin", "uday", "ujjwal", "utpal", "uttam",

    # Islamic Male First Names & Compounds
    "ali", "hussain", "hasan", "hassan", "ahsan", "mohammed", "mohammad", "muhammad",
    "ahmed", "ahmad", "tariq", "rashid", "arif", "shahid", "zahid", "waseem", "wasim",
    "nadeem", "mustafa", "murtaza", "saif", "aslam", "farhan", "salman", "rizwan",
    "altaf", "iqbal", "firoz", "tanvir", "tanveer", "ilyas", "elias", "imran", "irfan",
    "azhar", "akhtar", "sajid", "shakir", "samir", "sameer", "rehan", "sohail", "suhail",
    "afzal", "parvez", "shahnawaz", "shahbaz", "naim", "naeem", "javed", "babar", "bilal",
    "abu", "akbar", "akram", "alauddin", "alishah", "amjad", "asad", "asif", "atik",
    "dawood", "farooq", "fazle", "habib", "hafiz", "haider", "ibrahim", "imtiaz", "ismail",
    "jahangir", "jalal", "jamal", "kabir", "mansoor", "masud", "motiur", "mubarak",
    "murshid", "mushtaq", "nasir", "nazir", "nur", "rahim", "rahman", "reza", "riaz",
    "riyaz", "saddam", "salim", "sarfaraz", "sayed", "sayeed", "selim", "shabbir",
    "shahrukh", "shams", "shaukat", "siraj", "yasin", "yusuf", "zafar", "zishan", "zubair",

    # Pan-Indian Masculine Names
    "aayush", "ayush", "abdul", "abdhesh", "avdhesh", "rahul", "amit", "rajesh", "suresh",
    "vikram", "rohan", "arjun", "sachin", "prateek", "diptesh", "krishna", "gaurav",
    "manoj", "vijay", "anil", "sunil", "deepak", "rakesh", "ashok", "dinesh", "pankaj",
    "mukesh", "alok", "vivek", "varun", "kunal", "sumit", "sourabh", "saurabh", "rohit",
    "aman", "ankit", "mohit", "vicky", "nitin", "mayank", "ravi", "ram", "sham", "shyam",
    "amar", "amal", "akshay", "akshit", "alkesh", "aditya", "akash", "anand", "animesh",
    "arun", "badal", "bahadur", "debendra", "gautam", "gopal", "govind", "himanshu",
    "kamal", "karan", "karthik", "kaushik", "keshav", "lakshman", "madhav", "manish",
    "mukund", "munna", "naresh", "nayan", "nilesh", "piyush", "prakash", "pratik",
    "prem", "rajeev", "rajendra", "ratan", "ronit", "sagar", "sandeep", "satish",
    "shakti", "shambhu", "shekhar", "shivam", "shreyas", "shubham", "vinay", "vipin", "vishal"
}

DB_FEMALE = {
    # Modern Diminutives & Pet Names
    "ruby", "dolly", "pinky", "rinky", "sweety", "mary", "lily", "daisy", "simy",
    "bobby", "munni", "baby", "tina", "rina", "mina", "sheena", "puja", "pooja",
    "simi", "tannu", "tanu",

    # Islamic Consonant & Classical Feminine Names
    "zainab", "zaynab", "maryam", "mariam", "shabnam", "tabassum", "kulsum", "kalsum",
    "nusrat", "ishrat", "nikhat", "ismat", "zeenat", "jannat", "nargis", "bilqis",
    "firdaus", "afreen", "yasmin", "yasmine", "nasrin", "nasreen", "shirin", "parveen",
    "parvin", "iram", "sanam", "fatima", "fatema", "ayesha", "khadija", "sultana",
    "farhana", "roksana", "tanzila", "salma", "rehana", "shahana", "tasnim", "samina",
    "tahmina", "razia", "asifa", "rabia", "sumaiya", "zoya", "bushra", "saima",
    "shabana", "sanida", "afroza", "amina", "asma", "farida", "hasina", "israt",
    "jahanara", "jamila", "julekha", "khaleda", "marina", "mashiura", "nafisa",
    "nilufar", "rahela", "rokeya", "sabera", "sabina", "sadia", "sajeda", "saleha",
    "sanjida", "shahnaz", "tarannum",

    # Bengali Feminine Names
    "moumita", "debapriya", "madhumita", "anindita", "paramita", "sarmistha", "sharmistha",
    "piyali", "ruma", "chhanda", "sampa", "kakoli", "kakali", "baishakhi", "sucharita",
    "monalisa", "titas", "swarnali", "barnali", "sayani", "soma", "rupali", "jhuma",
    "mousumi", "tanusree", "tanushree", "subhashree", "debaleena", "indrani", "chaitali",
    "basanti", "paoli", "payel", "rituparna", "bhaswati", "shrabani", "arati", "arundhati",
    "sutapa", "bhabani", "bhagabati", "bharati", "bina", "binapani", "bipasha", "bithi",
    "chandrani", "chinmoyee", "chitra", "damayanti", "debasree", "debika", "jharna",
    "jhumur", "kadambari", "kalyani", "koli", "koyel", "kuntala", "lipika", "lopa",
    "lopamudra", "madhabi", "madhabilata", "mahuya", "maitreyi", "malabika", "mamoni",
    "manjusree", "mitali", "mithu", "mitra", "moly", "mou", "munmun", "pallabi",
    "paromita", "piya", "pritikana", "rimpa", "romola", "rupashree", "samita", "sanchita",
    "sanghamitra", "santwana", "sarama", "sayantani", "shampa", "shefali", "snigdha",
    "sohini", "srabanti", "subarna", "suchandra", "suchitra", "sudeshna", "sukanya",
    "sukla", "sulekha", "surobhita", "tarulata", "teesta", "tumpa", "utpala",

    # Pan-Indian Feminine Names
    "abantika", "avantika", "priya", "ananya", "sunita", "deepika", "kavita", "roshni",
    "meera", "swati", "tanvi", "aaradhya", "shruti", "neha", "sneha", "aarti", "divya",
    "anjali", "riya", "simran", "shreya", "payal", "komal", "pallavi", "radha", "seema",
    "rekha", "geeta", "monika", "sonam", "preeti", "jyoti", "nisha", "rashmi", "mamta",
    "sapna", "kajal", "vandana", "alka", "renu", "bhavna", "ishita", "sakshi", "kriti",
    "shweta", "garima", "mansi", "mahima", "diksha", "deeksha", "prachi", "sheetal",
    "akshta", "alafiya", "alankrita", "alia", "alifya", "alisha", "shameli", "aditi",
    "amita", "anamika", "anita", "ankita", "annapurna", "anupama", "anuradha", "aparna",
    "aradhana", "archana", "arpita", "arushi", "babita", "barkha", "bela", "chameli",
    "champa", "chandana", "chandani", "deepa", "deepali", "dipti", "durga", "gargi",
    "gautami", "gayatri", "geetanjali", "indira", "jaya", "jayati", "jayashree", "jyotsna",
    "kamala", "kanan", "kanchan", "kanta", "kasturi", "kaushalya", "kripa", "krishnaa",
    "kusum", "lakshmi", "latika", "leela", "madhuri", "malati", "mallika", "mamata",
    "manasi", "mandira", "manisha", "manjari", "manju", "manjula", "mohini", "mona",
    "moni", "naina", "namita", "nandini", "nandita", "neelam", "nikita", "nilanjana",
    "nilima", "nirmala", "nupur", "padma", "paramita", "parbati", "poornima", "prabha",
    "prativa", "pratima", "prerna", "priyanka", "purnima", "radhika", "ragini", "raima",
    "rakhi", "rani", "ratna", "reba", "renuka", "resmi", "richa", "roma", "rupa",
    "sabita", "sahana", "sandhya", "sangeeta", "sarada", "saraswati", "sarita", "saroj",
    "sarojini", "shakuntala", "shanta", "shanti", "sharada", "sharmila", "sheela",
    "shikha", "shipra", "shobha", "shubhra", "shyama", "smita", "sonali", "subhadra",
    "sudha", "sujata", "sumana", "sumati", "sumita", "sumitra", "sunanda", "sunayana",
    "suparna", "supriti", "supriya", "surabhi", "suruchi", "sushama", "sushila",
    "sushmita", "swapna", "sweta", "tania", "tapasya", "tara", "trisha", "uma",
    "urmila", "usha", "vaishali", "varsha", "vidya", "vinita"
}

# ==========================================
# 2. ADD GIST DATASETS (EXPANDS BASE CORPUS)
# ==========================================

@app.on_event("startup")
def load_gist_datasets():
    global DB_FEMALE, DB_MALE
    gist_sources = [
        ("https://gist.githubusercontent.com/mbejda/9b93c7545c9dd93060bd/raw/indian-female-names.csv", "female"),
        ("https://gist.githubusercontent.com/mbejda/7f86e35f30de9207433f/raw/indian-male-names.csv", "male")
    ]

    for url, g_type in gist_sources:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                for line in lines[1:]:
                    parts = line.strip().split(",")
                    if parts and parts[0]:
                        raw_nm = parts[0].strip().lower()
                        clean_nm = re.sub(r'[^a-z]', '', raw_nm)
                        if len(clean_nm) >= 2:
                            if g_type == "female":
                                DB_FEMALE.add(clean_nm)
                            else:
                                DB_MALE.add(clean_nm)
        except Exception as e:
            print(f"Skipping external sync from {url}: {e}")

    # Agar koi common conflicts aate hain toh unhe clean karein
    conflicts = DB_MALE.intersection(DB_FEMALE)
    DB_MALE -= conflicts
    DB_FEMALE -= conflicts

    # Core explicit entries hamesha override aur fixed rahenge
    DB_MALE.update([
        "ali", "imran", "ilyas", "abhijeet", "abhijit", "abhirup", "abhishek", 
        "subrata", "debabrata", "soumya", "joy", "tanmoy", "chinmoy", "diptesh", "krishna"
    ])
    DB_FEMALE.update([
        "zainab", "zaynab", "ruby", "dolly", "pinky", "maryam", "shabnam", "tabassum", 
        "nusrat", "zeenat", "jannat", "afreen", "yasmin", "nasrin", "parveen"
    ])

# ==========================================
# 3. DETERMINISTIC HEURISTIC RULES
# ==========================================

FEMALE_TOKENS = {"devi", "kumari", "khatun", "bibi", "begum", "banu", "ara", "parveen", "nisa", "unissa"}
MALE_TOKENS = {"kumar", "chandra", "nath", "prasad", "das", "singh", "lal", "babu", "da", "uddin", "ullah"}
MALE_PREFIXES = ("abdul", "mohd", "mohammad", "muhammad", "md", "sk", "sheikh", "syed", "ghulam", "ali")

# Male Suffixes (Evaluated first to protect -jeet, -jit, -joy)
MALE_SUFFIXES = (
    "jeet", "jit", "joy", "rup", "brata", "kanta", "kanti", "sekhar", "shekhar",
    "moy", "shis", "shish", "esh", "kant", "anand", "dev", "deb", "dhar", "pal",
    "nav", "veer", "ul", "it", "ik", "ak", "av", "am", "sh", "ay", "ab", "ban",
    "ron", "ran", "oy", "ey"
)

# Female Suffixes
FEMALE_SUFFIXES = (
    "wati", "vati", "mati", "mita", "tika", "ika", "ita", "isha", "priya",
    "shree", "sri", "lata", "mala", "bala", "dita", "purna", "lekha", "shila",
    "rekha", "nita", "jani", "shikha", "rupa", "rani", "mani", "dharini",
    "nandini", "sundari", "nab", "eena", "ina", "rat", "hat", "mat",
    "nam", "sum", "yeen", "veen", "reen", "min", "rin", "qis", "gis"
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

    # Step 1: Token-level deterministic titles
    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"
        if t in MALE_TOKENS:
            return "Male"

    # Step 2: In-Memory Master Database Match
    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    # Step 3: Prefix Matches (Abdul, Ali, Sk, Md)
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    # Step 4: Suffix Matches (Male evaluated first)
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"

    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"

    # Step 5: Anglo-Indian Diminutive (-y)
    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female"

    # Step 6: Sanskrit Conjunct Endings with -a
    if token.endswith("a"):
        if re.search(r'(rta|bha|nya|tya|rka|nda|mba|rya|pta|tra|dra|ndra)$', token):
            return "Male"
        return "Female"

    # Terminal Vowels
    if token.endswith(("i", "ee", "aa")):
        return "Female"

    # Terminal Consonant Default
    return "Male"

# ==========================================
# 4. FASTAPI ENDPOINTS
# ==========================================

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
