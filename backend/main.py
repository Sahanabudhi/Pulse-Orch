from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

import anthropic
import json

anthropic_client = anthropic.Anthropic()

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

from datetime import datetime

EMERGENCY_SPECIALTY_MAP = {
    "Road Accident": "Trauma Surgeon", "Gunshot Wound": "Trauma Surgeon",
    "Cardiac Event": "Cardiologist", "Stroke": "Neurosurgeon",
    "Fall Injury": "Orthopedic Surgeon", "Burn Injury": "Trauma Surgeon",
    "Respiratory Distress": "Emergency Physician",
    "Allergic Reaction": "Emergency Physician",
}

def log_event(patient_id, agent_name, message, status):
    supabase.table("agent_events").insert({
        "patient_id": patient_id, "agent_name": agent_name,
        "message": message, "status": status,
    }).execute()

@app.post("/api/orchestrate/{patient_id}")
def orchestrate_patient(patient_id: str):
    patient = supabase.table("patients").select("*").eq("id", patient_id).execute().data[0]
    hospital = supabase.table("hospitals").select("*").eq("id", patient["hospital_id"]).execute().data[0]
    events = []

    msg = f'Patient classified as {patient["triage_level"].upper()}'
    log_event(patient_id, "TRIAGE AGENT", msg, "success")
    events.append({"agent": "TRIAGE AGENT", "message": msg, "status": "success"})

    ok = hospital["icu_beds_available"] > 0
    msg = f'{"ICU bed available" if ok else "No ICU beds available"} at {hospital["name"]}'
    log_event(patient_id, "BED AGENT", msg, "success" if ok else "warning")
    events.append({"agent": "BED AGENT", "message": msg, "status": "success" if ok else "warning"})

    if patient["emergency_type"] in ["Road Accident", "Gunshot Wound", "Burn Injury"]:
        blood = supabase.table("blood_inventory").select("*").eq("hospital_id", hospital["id"]).execute().data
        total = sum(b["units_available"] for b in blood)
        status = "success" if total >= 3 else "warning"
        msg = f"Blood supply: {total} units at {hospital['name']}"
        log_event(patient_id, "BLOOD AGENT", msg, status)
        events.append({"agent": "BLOOD AGENT", "message": msg, "status": status})

    specialty = EMERGENCY_SPECIALTY_MAP.get(patient["emergency_type"], "Emergency Physician")
    doctors = supabase.table("doctors").select("*").eq("hospital_id", hospital["id"]).eq("specialty", specialty).execute().data
    available = next((d for d in doctors if d["is_available"]), None)
    status = "success" if available else "warning"
    msg = f'{specialty} {"available" if available else "unavailable"} at {hospital["name"]}'
    log_event(patient_id, "DOCTOR AGENT", msg, status)
    events.append({"agent": "DOCTOR AGENT", "message": msg, "status": status})

    has_warning = any(e["status"] == "warning" for e in events)
    msg = "Resource conflict detected" if has_warning else "All resources confirmed"
    log_event(patient_id, "ORCHESTRATOR", msg, "warning" if has_warning else "success")
    events.append({"agent": "ORCHESTRATOR", "message": msg, "status": "warning" if has_warning else "success"})

    return {"patient_id": patient_id, "events": events}

@app.get("/api/agent-events")
def get_agent_events():
    return supabase.table("agent_events").select("*").order("created_at", desc=True).limit(20).execute().data
@app.get("/api/shadow-mode/{hospital_id}")
def shadow_mode(hospital_id: str):
    hospital = supabase.table("hospitals").select("*").eq("id", hospital_id).execute().data[0]
    critical_incoming = supabase.table("patients").select("*") \
        .eq("hospital_id", hospital_id).eq("status", "registered") \
        .eq("triage_level", "critical").execute().data

    icu_available = hospital["icu_beds_available"]
    incoming_needing_icu = len(critical_incoming)

    if incoming_needing_icu >= icu_available and icu_available > 0:
        minutes = round((icu_available / max(incoming_needing_icu, 1)) * 15)
        return {"hospital": hospital["name"], "warning": True,
                "message": f"ICU CAPACITY SHORTAGE PREDICTED — exhausted in ~{minutes} minutes.",
                "icu_beds_available": icu_available, "critical_patients_incoming": incoming_needing_icu}
    elif icu_available == 0:
        return {"hospital": hospital["name"], "warning": True, "message": "ICU CAPACITY ALREADY EXHAUSTED.",
                "icu_beds_available": 0, "critical_patients_incoming": incoming_needing_icu}
    return {"hospital": hospital["name"], "warning": False, "message": "Capacity nominal.",
            "icu_beds_available": icu_available, "critical_patients_incoming": incoming_needing_icu}


@app.get("/api/recommend-transfer/{patient_id}")
def recommend_transfer(patient_id: str):
    patient = supabase.table("patients").select("*").eq("id", patient_id).execute().data[0]
    hospitals = supabase.table("hospitals").select("*").execute().data
    specialty = EMERGENCY_SPECIALTY_MAP.get(patient["emergency_type"], "Emergency Physician")

    scored = []
    for h in hospitals:
        if h["id"] == patient["hospital_id"]:
            continue
        doctors = supabase.table("doctors").select("*").eq("hospital_id", h["id"]) \
            .eq("specialty", specialty).eq("is_available", True).execute().data
        blood = supabase.table("blood_inventory").select("*").eq("hospital_id", h["id"]).execute().data
        blood_total = sum(b["units_available"] for b in blood)
        score = (h["icu_beds_available"] * 3 + len(doctors) * 3
                 + min(blood_total, 10) + h["operating_rooms_available"] * 2)
        scored.append({"hospital": h["name"], "hospital_id": h["id"], "score": score,
                        "icu_beds_available": h["icu_beds_available"],
                        "specialist_available": len(doctors) > 0, "blood_units": blood_total})

    scored.sort(key=lambda x: x["score"], reverse=True)
    brain = brain_agent_decision(patient, scored[:3])
    return {"patient_id": patient_id, "recommended": scored[0] if scored else None,
            "brain_agent_reasoning": brain["reasoning"], "all_options": scored}

def brain_agent_decision(patient, scored_options):
    if not scored_options:
        return {"chosen_hospital_id": None, "reasoning": "No candidate hospitals available."}

    prompt = f"""You are a hospital allocation assistant. You are given a patient's
emergency type and a list of candidate hospitals with pre-computed scores.
Do NOT invent or change any numbers. Pick the best option from the list and
explain the tradeoff in one short sentence for a paramedic.

Patient emergency: {patient['emergency_type']}
Triage level: {patient['triage_level']}
Candidates: {json.dumps(scored_options)}

Respond ONLY as JSON: {{"chosen_hospital_id": "...", "reasoning": "..."}}"""

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        decision = json.loads(raw)

        valid_ids = {o["hospital_id"] for o in scored_options}
        if decision.get("chosen_hospital_id") not in valid_ids:
            raise ValueError("LLM returned an invalid hospital id")

        return decision

        except Exception as e:
        return {
            "chosen_hospital_id": scored_options[0]["hospital_id"],
            "reasoning": f"Fallback: highest deterministic score. Error: {str(e)}"
        }