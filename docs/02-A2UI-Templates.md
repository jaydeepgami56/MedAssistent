# MedAssist AI — A2UI Interface Templates

All A2UI JSONL templates for the medical agent interfaces.

---

## 1. Triage Dashboard

**File:** `a2ui/templates/triage-dashboard.jsonl`

```jsonl
{"surfaceUpdate":{"surfaceId":"triage","components":[
  {"id":"root","component":{"Column":{"children":{"explicitList":["header","stats","queue","disclaimer"]}}}},
  {"id":"header","component":{"Row":{"children":{"explicitList":["title","refresh_btn"]}}}},
  {"id":"title","component":{"Text":{"text":{"literalString":"Emergency Triage Dashboard"},"usageHint":"h1"}}},
  {"id":"refresh_btn","component":{"Button":{"label":"Refresh Queue","action":"refresh_triage"}}},

  {"id":"stats","component":{"Row":{"children":{"explicitList":["esi1","esi2","esi3","esi4","esi5"]}}}},

  {"id":"esi1","component":{"Card":{"children":{"explicitList":["esi1_ct","esi1_lb"]}}}},
  {"id":"esi1_ct","component":{"Text":{"text":{"binding":{"key":"esi1_count"}},"usageHint":"h1"}}},
  {"id":"esi1_lb","component":{"Text":{"text":{"literalString":"Critical (ESI-1)"},"usageHint":"caption"}}},

  {"id":"esi2","component":{"Card":{"children":{"explicitList":["esi2_ct","esi2_lb"]}}}},
  {"id":"esi2_ct","component":{"Text":{"text":{"binding":{"key":"esi2_count"}},"usageHint":"h1"}}},
  {"id":"esi2_lb","component":{"Text":{"text":{"literalString":"Emergency (ESI-2)"},"usageHint":"caption"}}},

  {"id":"esi3","component":{"Card":{"children":{"explicitList":["esi3_ct","esi3_lb"]}}}},
  {"id":"esi3_ct","component":{"Text":{"text":{"binding":{"key":"esi3_count"}},"usageHint":"h1"}}},
  {"id":"esi3_lb","component":{"Text":{"text":{"literalString":"Urgent (ESI-3)"},"usageHint":"caption"}}},

  {"id":"esi4","component":{"Card":{"children":{"explicitList":["esi4_ct","esi4_lb"]}}}},
  {"id":"esi4_ct","component":{"Text":{"text":{"binding":{"key":"esi4_count"}},"usageHint":"h1"}}},
  {"id":"esi4_lb","component":{"Text":{"text":{"literalString":"Semi-urgent (ESI-4)"},"usageHint":"caption"}}},

  {"id":"esi5","component":{"Card":{"children":{"explicitList":["esi5_ct","esi5_lb"]}}}},
  {"id":"esi5_ct","component":{"Text":{"text":{"binding":{"key":"esi5_count"}},"usageHint":"h1"}}},
  {"id":"esi5_lb","component":{"Text":{"text":{"literalString":"Non-urgent (ESI-5)"},"usageHint":"caption"}}},

  {"id":"queue","component":{"List":{"items":{"binding":{"key":"patient_queue"}}}}},

  {"id":"disclaimer","component":{"Text":{"text":{"literalString":"⚠️ AI-assisted triage — requires clinician verification. ESI 1-2 auto-escalate to attending physician."},"usageHint":"caption"}}}
]}}
{"beginRendering":{"surfaceId":"triage","root":"root"}}
```

**Dynamic update (new patient arrives):**

```jsonl
{"dataModelUpdate":{"surfaceId":"triage","updates":{
  "esi1_count":"2",
  "esi2_count":"3",
  "esi3_count":"5",
  "esi4_count":"4",
  "esi5_count":"2",
  "patient_queue":["p001","p002","p003","p004","p005"]
}}}
```

---

## 2. Radiology Report

**File:** `a2ui/templates/radiology-report.jsonl`

```jsonl
{"surfaceUpdate":{"surfaceId":"radiology","components":[
  {"id":"root","component":{"Column":{"children":{"explicitList":["title","panels","disclaimer"]}}}},
  {"id":"title","component":{"Text":{"text":{"literalString":"Radiology Analysis Report"},"usageHint":"h1"}}},
  {"id":"panels","component":{"Row":{"children":{"explicitList":["left","right"]}}}},

  {"id":"left","component":{"Column":{"children":{"explicitList":["pt_card","findings_card","classification_card"]}}}},

  {"id":"pt_card","component":{"Card":{"children":{"explicitList":["pt_name","pt_mod","pt_date","pt_model"]}}}},
  {"id":"pt_name","component":{"Text":{"text":{"binding":{"key":"patient_name"}},"usageHint":"h2"}}},
  {"id":"pt_mod","component":{"Text":{"text":{"binding":{"key":"modality"}},"usageHint":"body"}}},
  {"id":"pt_date","component":{"Text":{"text":{"binding":{"key":"study_date"}},"usageHint":"caption"}}},
  {"id":"pt_model","component":{"Text":{"text":{"literalString":"Model: MedImageInsight + MedGemma 4B"},"usageHint":"caption"}}},

  {"id":"findings_card","component":{"Card":{"children":{"explicitList":["f_title","f_list"]}}}},
  {"id":"f_title","component":{"Text":{"text":{"literalString":"Findings"},"usageHint":"h2"}}},
  {"id":"f_list","component":{"List":{"items":{"binding":{"key":"findings"}}}}},

  {"id":"classification_card","component":{"Card":{"children":{"explicitList":["cls_title","cls_results"]}}}},
  {"id":"cls_title","component":{"Text":{"text":{"literalString":"Zero-Shot Classification"},"usageHint":"h3"}}},
  {"id":"cls_results","component":{"List":{"items":{"binding":{"key":"classification_results"}}}}},

  {"id":"right","component":{"Column":{"children":{"explicitList":["ev_card","rec_card","actions"]}}}},

  {"id":"ev_card","component":{"Card":{"children":{"explicitList":["ev_title","ev_count","ev_cases"]}}}},
  {"id":"ev_title","component":{"Text":{"text":{"literalString":"Similar Cases (KNN Evidence)"},"usageHint":"h3"}}},
  {"id":"ev_count","component":{"Text":{"text":{"binding":{"key":"evidence_count"}},"usageHint":"caption"}}},
  {"id":"ev_cases","component":{"List":{"items":{"binding":{"key":"similar_cases"}}}}},

  {"id":"rec_card","component":{"Card":{"children":{"explicitList":["rec_title","rec_text"]}}}},
  {"id":"rec_title","component":{"Text":{"text":{"literalString":"Recommendation"},"usageHint":"h3"}}},
  {"id":"rec_text","component":{"Text":{"text":{"binding":{"key":"recommendation"}},"usageHint":"body"}}},

  {"id":"actions","component":{"Row":{"children":{"explicitList":["approve","flag","reassign"]}}}},
  {"id":"approve","component":{"Button":{"label":"✓ Approve Report","action":"approve_report"}}},
  {"id":"flag","component":{"Button":{"label":"⚑ Flag for Review","action":"flag_review"}}},
  {"id":"reassign","component":{"Button":{"label":"↗ Reassign Specialist","action":"reassign"}}},

  {"id":"disclaimer","component":{"Text":{"text":{"literalString":"⚠️ AI-assisted analysis — requires radiologist review. Confidence < 0.7 flagged for mandatory review."},"usageHint":"caption"}}}
]}}
{"beginRendering":{"surfaceId":"radiology","root":"root"}}
```

---

## 3. Drug Interaction Alert

**File:** `a2ui/templates/drug-alert.jsonl`

```jsonl
{"surfaceUpdate":{"surfaceId":"drug_alert","components":[
  {"id":"root","component":{"Column":{"children":{"explicitList":["alert_header","drug_pair","severity_badge","interaction_detail","evidence_card","actions","disclaimer"]}}}},

  {"id":"alert_header","component":{"Text":{"text":{"literalString":"⚠️ Drug Interaction Alert"},"usageHint":"h1"}}},

  {"id":"drug_pair","component":{"Row":{"children":{"explicitList":["drug_a_card","arrow","drug_b_card"]}}}},
  {"id":"drug_a_card","component":{"Card":{"children":{"explicitList":["drug_a_name","drug_a_dose"]}}}},
  {"id":"drug_a_name","component":{"Text":{"text":{"binding":{"key":"drug_a_name"}},"usageHint":"h2"}}},
  {"id":"drug_a_dose","component":{"Text":{"text":{"binding":{"key":"drug_a_dose"}},"usageHint":"caption"}}},
  {"id":"arrow","component":{"Text":{"text":{"literalString":"⟷"},"usageHint":"h2"}}},
  {"id":"drug_b_card","component":{"Card":{"children":{"explicitList":["drug_b_name","drug_b_dose"]}}}},
  {"id":"drug_b_name","component":{"Text":{"text":{"binding":{"key":"drug_b_name"}},"usageHint":"h2"}}},
  {"id":"drug_b_dose","component":{"Text":{"text":{"binding":{"key":"drug_b_dose"}},"usageHint":"caption"}}},

  {"id":"severity_badge","component":{"Text":{"text":{"binding":{"key":"severity_text"}},"usageHint":"h3"}}},
  {"id":"interaction_detail","component":{"Text":{"text":{"binding":{"key":"interaction_description"}},"usageHint":"body"}}},

  {"id":"evidence_card","component":{"Card":{"children":{"explicitList":["ev_source","ev_text"]}}}},
  {"id":"ev_source","component":{"Text":{"text":{"literalString":"Source: DrugBank + RxNorm"},"usageHint":"caption"}}},
  {"id":"ev_text","component":{"Text":{"text":{"binding":{"key":"evidence"}},"usageHint":"body"}}},

  {"id":"actions","component":{"Row":{"children":{"explicitList":["override_btn","alt_btn","cancel_btn"]}}}},
  {"id":"override_btn","component":{"Button":{"label":"Override (Requires Reason)","action":"override_interaction"}}},
  {"id":"alt_btn","component":{"Button":{"label":"Suggest Alternative","action":"suggest_alternative"}}},
  {"id":"cancel_btn","component":{"Button":{"label":"Cancel Prescription","action":"cancel_prescription"}}},

  {"id":"disclaimer","component":{"Text":{"text":{"literalString":"Critical interactions BLOCK workflow. Override requires documented clinical justification."},"usageHint":"caption"}}}
]}}
{"beginRendering":{"surfaceId":"drug_alert","root":"root"}}
```

---

## 4. Patient Vitals Monitor

**File:** `a2ui/templates/patient-vitals.jsonl`

```jsonl
{"surfaceUpdate":{"surfaceId":"vitals","components":[
  {"id":"root","component":{"Column":{"children":{"explicitList":["title","vitals_grid","trend_card","alert_card","actions","disclaimer"]}}}},

  {"id":"title","component":{"Text":{"text":{"literalString":"Patient Vitals Monitor"},"usageHint":"h1"}}},

  {"id":"vitals_grid","component":{"Row":{"children":{"explicitList":["hr_card","bp_card","spo2_card","temp_card","rr_card","mews_card"]}}}},

  {"id":"hr_card","component":{"Card":{"children":{"explicitList":["hr_icon","hr_val","hr_lbl","hr_range"]}}}},
  {"id":"hr_icon","component":{"Text":{"text":{"literalString":"❤️"},"usageHint":"h2"}}},
  {"id":"hr_val","component":{"Text":{"text":{"binding":{"key":"hr"}},"usageHint":"h1"}}},
  {"id":"hr_lbl","component":{"Text":{"text":{"literalString":"Heart Rate (bpm)"},"usageHint":"body"}}},
  {"id":"hr_range","component":{"Text":{"text":{"literalString":"Normal: 60-100"},"usageHint":"caption"}}},

  {"id":"bp_card","component":{"Card":{"children":{"explicitList":["bp_icon","bp_val","bp_lbl","bp_range"]}}}},
  {"id":"bp_icon","component":{"Text":{"text":{"literalString":"🩸"},"usageHint":"h2"}}},
  {"id":"bp_val","component":{"Text":{"text":{"binding":{"key":"bp"}},"usageHint":"h1"}}},
  {"id":"bp_lbl","component":{"Text":{"text":{"literalString":"Blood Pressure"},"usageHint":"body"}}},
  {"id":"bp_range","component":{"Text":{"text":{"literalString":"Normal: 120/80"},"usageHint":"caption"}}},

  {"id":"spo2_card","component":{"Card":{"children":{"explicitList":["spo2_icon","spo2_val","spo2_lbl","spo2_range"]}}}},
  {"id":"spo2_icon","component":{"Text":{"text":{"literalString":"🫁"},"usageHint":"h2"}}},
  {"id":"spo2_val","component":{"Text":{"text":{"binding":{"key":"spo2"}},"usageHint":"h1"}}},
  {"id":"spo2_lbl","component":{"Text":{"text":{"literalString":"SpO2 (%)"},"usageHint":"body"}}},
  {"id":"spo2_range","component":{"Text":{"text":{"literalString":"Normal: >95%"},"usageHint":"caption"}}},

  {"id":"temp_card","component":{"Card":{"children":{"explicitList":["temp_icon","temp_val","temp_lbl","temp_range"]}}}},
  {"id":"temp_icon","component":{"Text":{"text":{"literalString":"🌡️"},"usageHint":"h2"}}},
  {"id":"temp_val","component":{"Text":{"text":{"binding":{"key":"temp"}},"usageHint":"h1"}}},
  {"id":"temp_lbl","component":{"Text":{"text":{"literalString":"Temperature (°C)"},"usageHint":"body"}}},
  {"id":"temp_range","component":{"Text":{"text":{"literalString":"Normal: 36.5-37.5"},"usageHint":"caption"}}},

  {"id":"rr_card","component":{"Card":{"children":{"explicitList":["rr_icon","rr_val","rr_lbl","rr_range"]}}}},
  {"id":"rr_icon","component":{"Text":{"text":{"literalString":"💨"},"usageHint":"h2"}}},
  {"id":"rr_val","component":{"Text":{"text":{"binding":{"key":"rr"}},"usageHint":"h1"}}},
  {"id":"rr_lbl","component":{"Text":{"text":{"literalString":"Respiratory Rate (/min)"},"usageHint":"body"}}},
  {"id":"rr_range","component":{"Text":{"text":{"literalString":"Normal: 12-20"},"usageHint":"caption"}}},

  {"id":"mews_card","component":{"Card":{"children":{"explicitList":["mews_icon","mews_val","mews_lbl","mews_range"]}}}},
  {"id":"mews_icon","component":{"Text":{"text":{"literalString":"📈"},"usageHint":"h2"}}},
  {"id":"mews_val","component":{"Text":{"text":{"binding":{"key":"mews"}},"usageHint":"h1"}}},
  {"id":"mews_lbl","component":{"Text":{"text":{"literalString":"MEWS Score"},"usageHint":"body"}}},
  {"id":"mews_range","component":{"Text":{"text":{"literalString":"Normal: 0-2"},"usageHint":"caption"}}},

  {"id":"trend_card","component":{"Card":{"children":{"explicitList":["trend_title","trend_data"]}}}},
  {"id":"trend_title","component":{"Text":{"text":{"literalString":"Heart Rate Trend (6 hours)"},"usageHint":"h3"}}},
  {"id":"trend_data","component":{"Text":{"text":{"binding":{"key":"trend_summary"}},"usageHint":"body"}}},

  {"id":"alert_card","component":{"Card":{"children":{"explicitList":["alert_text","alert_action"]}}}},
  {"id":"alert_text","component":{"Text":{"text":{"binding":{"key":"alert_text"}},"usageHint":"h3"}}},
  {"id":"alert_action","component":{"Button":{"label":"Call Attending Physician","action":"call_attending"}}},

  {"id":"actions","component":{"Row":{"children":{"explicitList":["threshold_btn","ack_btn","history_btn"]}}}},
  {"id":"threshold_btn","component":{"Button":{"label":"Set Alert Threshold","action":"set_threshold"}}},
  {"id":"ack_btn","component":{"Button":{"label":"Acknowledge Alert","action":"acknowledge"}}},
  {"id":"history_btn","component":{"Button":{"label":"View Full History","action":"view_history"}}},

  {"id":"disclaimer","component":{"Text":{"text":{"literalString":"Real-time vitals powered by Monitoring Agent. MEWS > 3 triggers automatic attending notification."},"usageHint":"caption"}}}
]}}
{"beginRendering":{"surfaceId":"vitals","root":"root"}}
```

**Real-time update (every 30 seconds):**

```jsonl
{"dataModelUpdate":{"surfaceId":"vitals","updates":{
  "hr":"92",
  "bp":"138/88",
  "spo2":"96",
  "temp":"37.4",
  "rr":"20",
  "mews":"3",
  "trend_summary":"HR trending upward: 78→85→88→92 over last 2 hours",
  "alert_text":"⚠️ MEWS Score elevated (3). Consider clinical review."
}}}
```

---

## 5. Clinical Notes (SOAP)

**File:** `a2ui/templates/clinical-notes.jsonl`

```jsonl
{"surfaceUpdate":{"surfaceId":"soap","components":[
  {"id":"root","component":{"Column":{"children":{"explicitList":["title","subjective","objective","assessment","plan","codes","actions","disclaimer"]}}}},

  {"id":"title","component":{"Text":{"text":{"literalString":"Clinical Note — SOAP Format"},"usageHint":"h1"}}},

  {"id":"subjective","component":{"Card":{"children":{"explicitList":["s_title","s_input"]}}}},
  {"id":"s_title","component":{"Text":{"text":{"literalString":"S — Subjective"},"usageHint":"h2"}}},
  {"id":"s_input","component":{"TextField":{"placeholder":"Patient's chief complaint, HPI, symptoms...","binding":{"key":"subjective_text"}}}},

  {"id":"objective","component":{"Card":{"children":{"explicitList":["o_title","o_input"]}}}},
  {"id":"o_title","component":{"Text":{"text":{"literalString":"O — Objective"},"usageHint":"h2"}}},
  {"id":"o_input","component":{"TextField":{"placeholder":"Vitals, exam findings, lab results, imaging...","binding":{"key":"objective_text"}}}},

  {"id":"assessment","component":{"Card":{"children":{"explicitList":["a_title","a_input"]}}}},
  {"id":"a_title","component":{"Text":{"text":{"literalString":"A — Assessment"},"usageHint":"h2"}}},
  {"id":"a_input","component":{"TextField":{"placeholder":"Diagnosis, differential diagnoses...","binding":{"key":"assessment_text"}}}},

  {"id":"plan","component":{"Card":{"children":{"explicitList":["p_title","p_input"]}}}},
  {"id":"p_title","component":{"Text":{"text":{"literalString":"P — Plan"},"usageHint":"h2"}}},
  {"id":"p_input","component":{"TextField":{"placeholder":"Treatment plan, medications, follow-up, referrals...","binding":{"key":"plan_text"}}}},

  {"id":"codes","component":{"Card":{"children":{"explicitList":["codes_title","codes_list"]}}}},
  {"id":"codes_title","component":{"Text":{"text":{"literalString":"Suggested ICD-10 Codes"},"usageHint":"h3"}}},
  {"id":"codes_list","component":{"List":{"items":{"binding":{"key":"icd10_codes"}}}}},

  {"id":"actions","component":{"Row":{"children":{"explicitList":["finalize_btn","draft_btn","export_btn"]}}}},
  {"id":"finalize_btn","component":{"Button":{"label":"✓ Finalize Note","action":"finalize_note"}}},
  {"id":"draft_btn","component":{"Button":{"label":"Save Draft","action":"save_draft"}}},
  {"id":"export_btn","component":{"Button":{"label":"Export to EHR","action":"export_ehr"}}},

  {"id":"disclaimer","component":{"Text":{"text":{"literalString":"Auto-generated by Documentation Agent. Review and edit all sections before finalizing."},"usageHint":"caption"}}}
]}}
{"beginRendering":{"surfaceId":"soap","root":"root"}}
```

---

## CLI Commands Reference

```bash
# Push template to Canvas
openclaw nodes canvas a2ui push --jsonl a2ui/templates/triage-dashboard.jsonl --node <node-id>

# Reset Canvas
openclaw nodes canvas a2ui reset --node <node-id>

# Quick text push
openclaw nodes canvas a2ui push --node <node-id> --text "Status: All systems operational"

# Snapshot current state
openclaw nodes canvas snapshot --node <node-id>

# Get node ID
openclaw nodes list
```
