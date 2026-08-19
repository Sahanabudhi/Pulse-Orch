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

