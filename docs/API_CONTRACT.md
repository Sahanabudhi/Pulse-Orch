\# PULSE-ORCH API Contract



Base URL (local dev): http://127.0.0.1:8000



\## GET /api/hospitals

Returns all hospitals.

Example response:

\[{"id":"uuid","name":"Hospital A - City General","location":"Downtown",

"icu\_beds\_total":10,"icu\_beds\_available":2,"trauma\_beds\_total":8,

"trauma\_beds\_available":3,"operating\_rooms\_total":4,"operating\_rooms\_available":1,

"ventilators\_total":12,"ventilators\_available":4,"created\_at":"..."}]



\## GET /api/patients

Returns all patients.

Example: \[{"id":"uuid","name":"John Reyes","age":34,

"emergency\_type":"Road Accident","triage\_level":"critical",

"hospital\_id":"uuid","status":"admitted","created\_at":"..."}]



\## GET /api/patients/{patient\_id}

Returns a single patient object (same shape as above), or {"error":"Patient not found"}.



\## GET /api/doctors

Returns all doctors.

Example: \[{"id":"uuid","hospital\_id":"uuid","name":"Dr. Sarah Chen",

"specialty":"Trauma Surgeon","is\_available":true}]



\## GET /api/blood-inventory

Returns all blood inventory rows.

Example: \[{"id":"uuid","hospital\_id":"uuid","blood\_type":"O+","units\_available":3}]



\## GET /api/equipment

Returns all equipment rows.

Example: \[{"id":"uuid","hospital\_id":"uuid","equipment\_type":"CT Scanner",

"total":2,"available":1}]



\## GET /api/allergies/{patient\_id}

Returns allergies for one patient.

Example: \[{"id":"uuid","patient\_id":"uuid","allergy\_name":"Penicillin"}]



\## POST /api/orchestrate/{patient\_id}

Runs the orchestrator across Triage, Bed, Blood, and Doctor agents for a patient, logging each step.

Example: {"patient\_id":"uuid","events":\[{"agent":"TRIAGE AGENT","message":"Patient classified as CRITICAL","status":"success"}, ...]}



\## GET /api/agent-events

Returns the 20 most recent agent event log entries, newest first.

Example: \[{"id":"uuid","patient\_id":"uuid","agent\_name":"BED AGENT","message":"ICU bed available at ...","status":"success","created\_at":"..."}]



\## GET /api/shadow-mode/{hospital\_id}

Predicts ICU capacity shortages for a hospital based on incoming critical patients.

Example: {"hospital":"City General","warning":true,"message":"ICU CAPACITY SHORTAGE PREDICTED — exhausted in \~15 minutes.","icu\_beds\_available":2,"critical\_patients\_incoming":3}



\## GET /api/recommend-transfer/{patient\_id}

Scores all other hospitals for a patient's transfer suitability (ICU beds, specialist availability, blood supply, OR availability) and returns a ranked list plus a top recommendation, with an AI-generated one-sentence explanation.

Example: {"patient\_id":"uuid","recommended":{"hospital":"Hospital C","hospital\_id":"uuid","score":43}, "brain\_agent\_reasoning":"...", "all\_options":\[...]}

