import os
import re
import urllib.request
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Indic & Bengali Enterprise Gender Engine")

# ==========================================
# 1. FEMALE & MALE SURNAME / TOKEN MARKERS
# ==========================================

FEMALE_TOKENS = {
    # Traditional Honorific Surnames & Titles
    "devi", "kumari", "khatun", "khatoon", "bibi", "begum", "banu", "bano", 
    "ara", "parveen", "parvin", "nisa", "unissa", "nesa", "bai", "rani", 
    "dasi", "mahila", "shree", "bala"
}

MALE_TOKENS = {
    # Traditional Honorific Surnames & Masculine Middle/Last Tokens
    "kumar", "chandra", "nath", "prasad", "das", "singh", "lal", "babu", 
    "da", "uddin", "ullah", "hussain", "hassan", "hasan", "khan", "ali", 
    "mondal", "mandal", "halder", "sardar", "laskar", "molla", "mulla", 
    "shaikh", "sheikh", "mallick", "gazi", "middey", "baidya", "ghosh", 
    "bose", "mitra", "dutta", "chatterjee", "banerjee", "mukherjee", 
    "ganguly", "chakraborty", "bhattacharya", "sen", "roy", "ray", "pal", 
    "dey", "kundu", "saha", "barman", "majumdar", "adhikari", "samanta", 
    "jana", "patra", "maity", "bera", "sasmal", "pradhan", "manna", "bag", 
    "hazra", "kole", "panja", "shaw", "gupta", "agarwal", "sharma", "verma", 
    "yadav", "tiwari", "pandey", "mishra", "dubey", "chaubey", "singha", 
    "rawat", "joshi", "pathak", "thakur", "jha", "shukla"
}

# ==========================================
# 2. MERGED PRODUCTION CORPUS (EXCEL + BASE)
# ==========================================

DB_MALE = {
    "aayush", "abdhesh", "abdur", "abdul", "abhijeet", "abhijit", "abhijoy", "abhimanyu",
    "abhinaba", "abhinav", "abhinesh", "abhinob", "abhirup", "abhisek", "abhishek",
    "abhishrk", "abu", "adesh", "aditya", "aftab", "afzal", "ahmad", "ahmed", "ahsan",
    "ajaat", "ajay", "ajit", "ajoy", "akash", "akbar", "akhtar", "akram", "akshay",
    "akshit", "alauddin", "ali", "alishah", "alkesh", "alok", "altaf", "amal", "aman",
    "amar", "ambuj", "amimesh", "amit", "amitabh", "amitava", "amjad", "amlesh", "amod",
    "amol", "amrit", "amrito", "anadi", "anamik", "anand", "ananda", "ani", "anil",
    "animesh", "aninda", "anindya", "anirban", "aniruddha", "anirup", "ankit", "anowar",
    "ansuman", "anuj", "anup", "anupam", "anupom", "anurag", "apurba", "arghya", "arif",
    "arijit", "arka", "arjun", "arpan", "arup", "arun", "arunabha", "arunangshu",
    "asad", "asif", "ashis", "ashish", "ashit", "ashok", "asit", "aslam", "asoke",
    "atik", "atul", "avdhesh", "avijit", "avisek", "avishek", "avranil", "ayush",
    "azhar", "babar", "babu", "badal", "bahadur", "baidya", "baidyanath", "baljeet",
    "banibrata", "bappa", "bappaditya", "barun", "basudev", "bhabesh", "bhola", "bibhas",
    "bidhan", "bijan", "bijoy", "bikas", "bikash", "bikram", "bilal", "binod", "binoy",
    "biplab", "bipul", "biren", "bireswar", "biresh", "biswajit", "biswanath", "bratin",
    "buddhadeb", "bulbul", "chaitanya", "champak", "chandan", "chandi", "chandra",
    "chandranath", "chayan", "chinmay", "chinmoy", "chittaranjan", "dawood", "debabrata",
    "debal", "debasish", "debayan", "debbrata", "debdatta", "debendra", "debjit",
    "debrata", "debrup", "deep", "deepak", "dhiman", "dhiraj", "dibyendu", "dilip",
    "dinesh", "dipak", "dipankar", "dipen", "diptesh", "dulal", "elias", "farhan",
    "farooq", "fazle", "firoz", "gadadhar", "gagan", "ganesh", "gaurav", "gautam",
    "gobinda", "gopal", "gourab", "gouranga", "govind", "habib", "hafiz", "haider",
    "haradhan", "haridas", "harihar", "harjeet", "hasan", "hassan", "himadri", "himangshu",
    "himanshu", "hiranmoy", "hussain", "ibrahim", "ilyas", "imran", "imtiaz", "indrajit",
    "indrajeet", "indranil", "iqbal", "irfan", "ismail", "jahangir", "jalal", "jamal",
    "jasim", "javed", "jayanta", "jayanto", "jaydeb", "jeet", "jibon", "jitendra",
    "jiten", "joy", "joyanta", "joydeb", "joydeep", "kabir", "kallol", "kalyan", "kamal",
    "kamalesh", "kanai", "kanak", "kanti", "karan", "karthik", "karunamoy", "kashinath",
    "kaushik", "keshab", "keshav", "khagendra", "kiron", "kishore", "koushik", "koustav",
    "krishna", "krishnendu", "kunal", "lakshman", "lalit", "madhab", "madhav", "madhu",
    "madhusudan", "mainak", "manas", "manash", "manik", "manindra", "manish", "manjeet",
    "manoj", "mansoor", "masud", "mayank", "milan", "mithun", "mitul", "mohammad",
    "mohammed", "mohit", "monir", "motiur", "mousam", "mrinal", "mubarak", "mukesh",
    "mukund", "munna", "murshid", "mushtaq", "mustafa", "nadeem", "naeem", "naim",
    "naresh", "nasir", "nayan", "nazir", "nilesh", "nilmoni", "niloy", "nirmal",
    "nirmalya", "nitai", "nitin", "nur", "pabitra", "palash", "panchanan", "pankaj",
    "parag", "parameswar", "paresh", "partha", "parvez", "pinaki", "piyush", "prabhat",
    "prabir", "pradip", "pradyut", "prakash", "pramod", "pranab", "pranay", "prasenjit",
    "prateek", "pratik", "pratul", "prem", "pritom", "priyabrata", "prokash", "proloy",
    "prono", "pronob", "prosenjit", "pujit", "pulak", "pulin", "purnendu", "purushottam",
    "rabin", "rabindra", "radha", "radhakanta", "radheshyam", "raghab", "raghunath",
    "rahim", "rahman", "rahul", "rajat", "rajdip", "rajeev", "rajendra", "rajesh",
    "rajib", "rakesh", "ram", "ramaprasad", "ramkrishna", "ramprasad", "rana", "ranabir",
    "ranajit", "ranen", "ranendra", "ranjeet", "rashid", "ratan", "ratin", "ravi",
    "rehan", "reza", "riaz", "ripun", "rishi", "ritam", "ritesh", "ritwik", "riyaz",
    "rohan", "rohit", "ronit", "rupak", "rupam", "sachin", "saddam", "sagar", "saikat",
    "saif", "sajid", "salim", "salman", "samar", "samarendra", "samarjit", "sambhu",
    "sameer", "samir", "samiran", "samrat", "sandeep", "sandip", "sangram", "sanjay",
    "sanjoy", "sankar", "santanab", "santu", "saptarshi", "saradindu", "sarat", "sarfaraz",
    "saroj", "sarojit", "sasanka", "sasikanta", "satadal", "satikanta", "satish",
    "satyabrata", "satyajit", "satyajeet", "satyaki", "satyaranjan", "saurabh", "saurav",
    "sayed", "sayeed", "sekhar", "selim", "shabbir", "shahbaz", "shahid", "shahnawaz",
    "shahrukh", "shakti", "sham", "shambhu", "shams", "shankha", "shantanu", "shashank",
    "shaukat", "shekhar", "shirish", "shivam", "shouvik", "shreyas", "shubham",
    "shubhankar", "shyam", "shyamal", "siddhartha", "siraj", "soham", "sohail", "somnath",
    "sougata", "soumya", "soumyajit", "sourav", "souvik", "subal", "subhabrata",
    "subhadip", "subham", "subhas", "subhash", "subhashis", "subir", "subodh", "subrata",
    "sudhangshu", "sudhanshu", "sudhir", "sudip", "suhas", "sujan", "sujay", "sujit",
    "sukanta", "sukhen", "sukomal", "suman", "sumanta", "sumit", "sunil", "suprabhat",
    "supratim", "supratik", "surajit", "suresh", "surjeet", "surya", "suryakanta",
    "swadhin", "swapan", "swarup", "swastik", "tamal", "tanmay", "tanmoy", "tanvir",
    "tanveer", "tapan", "tapas", "tariq", "tarun", "tarunendra", "tathagata", "tirtha",
    "tirthankar", "tridib", "tuhin", "uday", "ujjwal", "utpal", "uttam", "varun",
    "vicky", "vijay", "vikas", "vikram", "vinay", "vipin", "vishal", "vivek", "wasim",
    "waseem", "yasin", "yusuf", "zafar", "zahid", "zishan", "zubair"
}

DB_FEMALE = {
    "aarti", "abantika", "aditi", "afreen", "afroza", "ahati", "ahona", "aindrila",
    "akshta", "alafiya", "alankrita", "alia", "alifya", "alisha", "alka", "alpona",
    "amina", "amita", "amrita", "anamika", "ananya", "anindita", "anirupa", "anita",
    "anjali", "ankita", "ankuta", "annapurna", "antara", "antra", "anua", "anupallavi",
    "anupama", "anuradha", "anushka", "anuska", "anushree", "aparajita", "aparna",
    "aradhana", "arati", "archana", "aritri", "arpita", "arundhati", "arushi", "asha",
    "ashima", "asifa", "asma", "atreyee", "auswa", "avantika", "ayanika", "ayesha",
    "babita", "baby", "baishakhi", "barkha", "barnali", "basanti", "bela", "bhabani",
    "bhagabati", "bharati", "bhaswati", "bhavna", "bina", "binapani", "binita", "bipasha",
    "bithi", "bobby", "bohnisikha", "bushra", "chaitali", "chaitaly", "chaitaty", "chameli",
    "champa", "chandana", "chandani", "chandrani", "chhanda", "chinmoyee", "chitra",
    "daisy", "damayanti", "debaleena", "debapriya", "debasree", "debika", "deeksha",
    "deepa", "deepali", "deepika", "diksha", "dipti", "divya", "dolly", "durga",
    "farhana", "farida", "fatema", "fatima", "firdaus", "gargi", "garima", "gautami",
    "gayatri", "geeta", "geetanjali", "hasina", "indira", "indrani", "iram", "ishita",
    "ishrat", "ismat", "israt", "jahanara", "jamila", "jannat", "jaya", "jayati",
    "jayashree", "jharna", "jhuma", "jhumur", "julekha", "jyoti", "jyotsna", "kadambari",
    "kajal", "kakali", "kakoli", "kalpana", "kalyani", "kamala", "kanan", "kanchan",
    "kanta", "kalsum", "kasturi", "kaushalya", "kavita", "khadija", "khaleda", "koli",
    "komal", "koyel", "kripa", "krishnaa", "kriti", "kulsum", "kuntala", "kusum",
    "lakshmi", "latika", "leela", "lily", "lipika", "lopa", "lopamudra", "madhabi",
    "madhabilata", "madhumita", "madhuri", "mahima", "mahuya", "maitreyi", "malabika",
    "malati", "mallika", "mamata", "mamoni", "mamta", "manasi", "mandira", "manisha",
    "manjari", "manju", "manjula", "manjusree", "mansi", "mariam", "marina", "mary",
    "maryam", "mashiura", "meera", "mina", "mitali", "mithu", "mitra", "mohini",
    "moly", "mona", "monalisa", "moni", "monika", "mou", "moumita", "mousumi", "munmun",
    "munni", "nafisa", "naina", "namita", "nandini", "nandita", "nargis", "nasreen",
    "nasrin", "neelam", "neha", "nikhat", "nikita", "nilanjana", "nilima", "nilufar",
    "nirmala", "nisha", "nupur", "nusrat", "padma", "pallabi", "pallavi", "paoli",
    "paramita", "parbati", "paromita", "parveen", "parvin", "payal", "payel", "pinky",
    "piya", "piyali", "poli", "pooja", "poornima", "prabha", "prachi", "prativa",
    "pratima", "preeti", "prerna", "pritikana", "priya", "priyanka", "puja", "purnima",
    "rabia", "radha", "radhika", "ragini", "rahela", "raima", "rakhi", "rani",
    "rashmi", "ratna", "razia", "reba", "rehana", "rekha", "renu", "renuka", "resmi",
    "richa", "rimpa", "rina", "rinki", "rituparna", "riya", "rokeya", "roksana",
    "roma", "romola", "roshni", "ruby", "ruma", "rupa", "rupali", "rupashree", "sabera",
    "sabina", "sabita", "sadia", "sahana", "saima", "sajeda", "sakshi", "saleha",
    "salma", "samina", "samita", "sampa", "sanam", "sanchita", "sandhya", "sangeeta",
    "sanghamitra", "sanida", "sanjida", "santwana", "sapna", "sarada", "sarama",
    "saraswati", "sarita", "sarmistha", "saroj", "sarojini", "sayani", "sayantani",
    "seema", "shabana", "shabnam", "shahana", "shahnaz", "shakuntala", "shameli",
    "shampa", "shanta", "shanti", "sharada", "sharmila", "sharmistha", "sharmista",
    "sheela", "sheena", "sheetal", "shefali", "shikha", "shipra", "shirin", "shobha",
    "shrabani", "shrestha", "shreya", "shruti", "shubhra", "shweta", "shyama", "simi",
    "simran", "simy", "smita", "sneha", "snigdha", "sohini", "soma", "sonali", "sonam",
    "srabanti", "subarna", "subhadra", "subhashree", "suchandra", "sucharita", "suchitra",
    "sudeshna", "sudha", "sujata", "sukanya", "sukla", "sulekha", "sultana", "suman",
    "sumana", "sumati", "sumita", "sumitra", "sumaiya", "sunanda", "sunayana", "sunita",
    "suparna", "supriti", "supriya", "surabhi", "surobhita", "suruchi", "sushama",
    "sushila", "sushmita", "sutapa", "swapna", "swarnali", "swati", "sweety", "sweta",
    "tabassum", "tahmina", "tania", "tannu", "tanu", "tanushree", "tanusree", "tanvi",
    "tanzila", "tapasya", "tara", "tarannum", "tarulata", "tasnim", "teesta", "tina",
    "titas", "trisha", "tumpa", "tusi", "uma", "urmila", "usha", "utpala", "vaishali",
    "vandana", "varsha", "vidya", "vinita", "yasmin", "yasmine", "zainab", "zaynab",
    "zeenat", "zoya"
}

# ==========================================
# 3. ADD GIST DATASETS (SYNC EXTRA 15K+ NAMES)
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

    # Remove overlapping names to eliminate ambiguity
    conflicts = DB_MALE.intersection(DB_FEMALE)
    DB_MALE -= conflicts
    DB_FEMALE -= conflicts

# ==========================================
# 4. MORPHOLOGICAL RULES (MALE / FEMALE ONLY)
# ==========================================

MALE_PREFIXES = ("abdul", "mohd", "mohammad", "muhammad", "md", "sk", "sheikh", "syed", "ghulam", "ali")

MALE_SUFFIXES = (
    "jeet", "jit", "joy", "rup", "brata", "kanta", "kanti", "sekhar", "shekhar",
    "moy", "shis", "shish", "esh", "kant", "anand", "dev", "deb", "dhar", "pal",
    "nav", "veer", "ul", "it", "ik", "ak", "av", "am", "sh", "ay", "ab", "ban",
    "ron", "ran", "oy", "ey"
)

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
        return "Male"

    # Step 1: Check Female Honorifics / Surnames across ALL tokens first (High Priority)
    for t in tokens:
        if t in FEMALE_TOKENS:
            return "Female"

    # Step 2: Check Male Surnames / Titles across ALL tokens
    for t in tokens:
        if t in MALE_TOKENS:
            return "Male"

    # Step 3: Check In-Memory Database for First Name
    if token in DB_FEMALE:
        return "Female"
    if token in DB_MALE:
        return "Male"

    # Step 4: Prefix Check (Abdul, Ali, Sk, Md)
    for pref in MALE_PREFIXES:
        if token.startswith(pref):
            return "Male"

    # Step 5: Suffix Heuristic (Male prioritized to preserve -jeet, -jit, -joy)
    for sfx in MALE_SUFFIXES:
        if token.endswith(sfx):
            return "Male"

    for sfx in FEMALE_SUFFIXES:
        if token.endswith(sfx):
            return "Female"

    # Step 6: Anglo-Indian Pet Names (-y)
    if token.endswith("y") and not token.endswith(("oy", "ay", "ey")):
        return "Female"

    # Step 7: Sanskrit Conjunct Endings with -a
    if token.endswith("a"):
        if re.search(r'(rta|bha|nya|tya|rka|nda|mba|rya|pta|tra|dra|ndra)$', token):
            return "Male"
        return "Female"

    # Terminal Vowels typical to feminine Indian names
    if token.endswith(("i", "ee", "aa")):
        return "Female"

    # Strictly Binary Fallback: Default to Male
    return "Male"

# ==========================================
# 5. FASTAPI ENDPOINTS
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
