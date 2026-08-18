from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PULSE-ORCH backend is running"}

@app.get("/api/hospitals")
def get_hospitals():
    return supabase.table("hospitals").select("*").execute().data

@app.get("/api/patients")
def get_patients():
    return supabase.table("patients").select("*").execute().data

@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: str):
    result = supabase.table("patients").select("*").eq("id", patient_id).execute().data
    return result[0] if result else {"error": "Patient not found"}

@app.get("/api/doctors")
def get_doctors():
    return supabase.table("doctors").select("*").execute().data

@app.get("/api/blood-inventory")
def get_blood_inventory():
    return supabase.table("blood_inventory").select("*").execute().data

@app.get("/api/equipment")
def get_equipment():
    return supabase.table("equipment").select("*").execute().data

@app.get("/api/allergies/{patient_id}")
def get_allergies(patient_id: str):
    return supabase.table("allergies").select("*").eq("patient_id", patient_id).execute().data