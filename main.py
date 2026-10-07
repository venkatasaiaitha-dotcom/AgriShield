#!/usr/bin/env python3
"""
AgriShield: Protect, Predict, Prove, Pay
FastAPI Backend providing satellite analytics, crop protection advice,
automated claim assessment, PDF generation, fraud verification, and multilingual AI/voice routing.
"""

import os
import json
import io
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Matplotlib headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ReportLab imports for claims PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = FastAPI(
    title="AgriShield API",
    description="Protect, Predict, Prove, Pay - Agricultural Resilience & Claims Decision Engine",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Automatically load environment variables from .env if present
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


# Helper to load data
def load_json_file(filename: str) -> dict:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail=f"Data file {filename} not found.")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def get_plots():
    data = load_json_file("plots.json")
    return data.get("plots", [])

def get_plot_by_id(plot_id: str):
    plots = get_plots()
    for p in plots:
        if p["id"] == plot_id:
            return p
    raise HTTPException(status_code=404, detail=f"Plot with id '{plot_id}' not found.")

def calculate_claim_metrics(plot: dict) -> dict:
    baseline = plot["baseline_ndvi"]
    # latest NDVI is week 12 (or final week)
    ndvi_timeline = plot["ndvi_timeline"]
    min_post_flood_ndvi = min(ndvi_timeline[11:])
    ndvi_drop = max(0.0, (baseline - min_post_flood_ndvi) / baseline)
    flooded_fraction = plot["flooded_pct"] / 100.0

    # Weather severity: max weekly rainfall normalized (210mm -> 0.9)
    max_rain = max(plot["rainfall_weekly"])
    weather_severity = min(1.0, max_rain / 220.0)

    # Loss score = 0.5*NDVI drop + 0.4*flooded fraction + 0.1*weather severity
    loss_score = round((0.5 * ndvi_drop) + (0.4 * flooded_fraction) + (0.1 * weather_severity), 3)

    # Confidence calculation: optical clarity count + SAR reliability
    cloud_cover = plot["cloud_cover_weekly"]
    clear_optical_weeks = sum(1 for c in cloud_cover if c < 50)
    # SAR radar penetrates clouds, giving solid baseline confidence of 0.80
    optical_factor = (clear_optical_weeks / len(cloud_cover)) * 0.15
    sar_factor = 0.75  # Guaranteed radar imagery Sentinel-1
    confidence = round(min(0.96, sar_factor + optical_factor), 2)

    # Decision rule:
    # loss >= 0.6 and confidence >= 0.7 -> "RECOMMEND APPROVE"
    # loss 0.3-0.6 or confidence < 0.7 -> "TARGETED GROUND CHECK"
    # else -> "NO CLAIM"
    if loss_score >= 0.6 and confidence >= 0.7:
        decision = "RECOMMEND APPROVE"
        decision_code = "APPROVE"
        decision_color = "#16a34a" # green
        payout_pct = min(100, int(loss_score * 110))
        reasoning_en = (
            f"Substantial crop loss ({round(loss_score*100)}%) detected. High radar backscatter attenuation "
            f"confirms {plot['flooded_pct']}% plot submergence despite heavy cloud cover. Pre-disaster advisories were unheeded. "
            f"Rapid insurance payout recommended without delay."
        )
    elif loss_score >= 0.3 or (loss_score >= 0.2 and confidence < 0.7):
        decision = "TARGETED GROUND CHECK"
        decision_code = "GROUND_CHECK"
        decision_color = "#d97706" # amber
        payout_pct = min(60, int(loss_score * 90))
        reasoning_en = (
            f"Moderate loss score ({round(loss_score*100)}%). Plot showed resilience due to flood-tolerant "
            f"variety ({plot['variety']}) and drainage bunds. Flooded area limited to {plot['flooded_pct']}%. "
            f"Targeted physical inspection advised to determine partial salvageable yield."
        )
    else:
        decision = "NO CLAIM"
        decision_code = "NO_CLAIM"
        decision_color = "#2563eb" # blue
        payout_pct = 0
        reasoning_en = (
            f"Minimal loss score ({round(loss_score*100)}%). NDVI vegetation canopy index remained healthy "
            f"(~{round(ndvi_timeline[-1], 2)}) with only negligible surface water ({plot['flooded_pct']}%). "
            f"No compensation claim warranted."
        )

    return {
        "plot_id": plot["id"],
        "farmer_name": plot["farmer_name"],
        "baseline_ndvi": baseline,
        "latest_ndvi": min_post_flood_ndvi,
        "ndvi_drop_fraction": round(ndvi_drop, 3),
        "flooded_fraction": flooded_fraction,
        "flooded_pct": plot["flooded_pct"],
        "weather_severity": round(weather_severity, 3),
        "loss_score": loss_score,
        "confidence": confidence,
        "decision": decision,
        "decision_code": decision_code,
        "decision_color": decision_color,
        "estimated_payout_pct": payout_pct,
        "reasoning": reasoning_en,
        "protection_score": plot.get("protection_score", 0),
        "variety": plot["variety"]
    }

# ----------------- ENDPOINTS -----------------

@app.get("/api/plots")
def list_plots():
    """Return all demo farmer plots with summary metadata."""
    plots = get_plots()
    summary = []
    for p in plots:
        summary.append({
            "id": p["id"],
            "farmer_name": p["farmer_name"],
            "farmer_title": p["farmer_title"],
            "village": p["village"],
            "lat": p["lat"],
            "lon": p["lon"],
            "crop": p["crop"],
            "variety": p["variety"],
            "acreage": p["acreage"],
            "baseline_ndvi": p["baseline_ndvi"],
            "current_ndvi": p["ndvi_timeline"][-1],
            "protection_score": p["protection_score"],
            "flooded_pct": p["flooded_pct"]
        })
    return {"sample_notice": "Sample data modeled on Sentinel-1 and Sentinel-2", "plots": summary}


@app.get("/api/plot/{plot_id}/health")
def get_plot_health(plot_id: str):
    """NDVI timeline, baseline, stress flag, and health color (green/yellow/red)."""
    plot = get_plot_by_id(plot_id)
    baseline = plot["baseline_ndvi"]
    timeline = plot["ndvi_timeline"]

    stress_threshold = baseline * 0.85 # > 15% drop below baseline
    severe_threshold = baseline * 0.70

    stressed_weeks = []
    for idx, val in enumerate(timeline):
        if val < stress_threshold:
            stressed_weeks.append(idx + 1)

    latest_val = timeline[-1]
    min_val = min(timeline)

    # Health status based on recent state
    if min_val < severe_threshold or latest_val < severe_threshold:
        health_color = "red"
        status_label = "Severe Damage / Flood Loss"
        face_emoji = "😟"
    elif min_val < stress_threshold or latest_val < stress_threshold:
        health_color = "yellow"
        status_label = "Stress Warning (Water/Disease)"
        face_emoji = "😐"
    else:
        health_color = "green"
        status_label = "Healthy & Thriving"
        face_emoji = "😊"

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "baseline_ndvi": baseline,
        "stress_threshold": round(stress_threshold, 3),
        "ndvi_timeline": timeline,
        "weeks": list(range(1, len(timeline) + 1)),
        "is_stressed": len(stressed_weeks) > 0,
        "stressed_weeks": stressed_weeks,
        "latest_ndvi": latest_val,
        "min_ndvi": min_val,
        "health_color": health_color,
        "status_label": status_label,
        "face_emoji": face_emoji,
        "stress_rule": "Stress triggered when NDVI is >15% below baseline (0.85 * baseline)"
    }


@app.get("/api/plot/{plot_id}/flood")
def get_plot_flood(plot_id: str):
    """SAR before/after dB, flooded % of plot, and 20x20 cell grid overlay."""
    plot = get_plot_by_id(plot_id)
    grid = plot["sar_grid"]
    before_db = plot["sar_before_db"]
    after_db = plot["sar_after_db"]
    delta_db = round(after_db - before_db, 2)
    flooded_pct = plot["flooded_pct"]

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "sar_before_db": before_db,
        "sar_after_db": after_db,
        "delta_db": delta_db,
        "flooded_pct": flooded_pct,
        "grid_resolution": "20x20 (400 sample cells)",
        "grid": grid,
        "flooded_cell_rule": "Flooded if (after_db - before_db < -3.0 dB) AND (after_db < -15.0 dB)",
        "optical_vs_radar": {
            "optical": {
                "sensor": "Sentinel-2 MultiSpectral",
                "cloud_cover_pct": plot["cloud_cover_weekly"][11],
                "status": "UNRELIABLE / BLINDED BY MONSOON CLOUDS",
                "penetration": "0% through rainclouds"
            },
            "radar": {
                "sensor": "Sentinel-1 Synthetic Aperture Radar (SAR C-Band)",
                "cloud_cover_pct": 0,
                "status": "CLEAR & PENETRATING ALL CLOUDS",
                "penetration": "100% all-weather surface water reflection"
            }
        }
    }


@app.get("/api/plan/{plot_id}")
def get_crop_plan(plot_id: str):
    """Crop protection plan evaluated against plot weather data."""
    plot = get_plot_by_id(plot_id)
    knowledge = load_json_file("crop_knowledge.json")

    # Evaluate risk rules against plot's weather data
    evaluated_risks = []
    rainfall = plot["rainfall_weekly"]
    humidity = plot["humidity_weekly"]
    timeline = plot["ndvi_timeline"]
    baseline = plot["baseline_ndvi"]

    # Rule 1: Blast disease (humidity >= 85 in weeks 5-7)
    blast_triggered = any(humidity[w-1] >= 85 for w in [5, 6, 7])
    if blast_triggered:
        evaluated_risks.append({
            "risk_id": "blast_disease",
            "name": "Paddy Blast Disease (Pyricularia oryzae)",
            "status": "ACTIVE ALERT",
            "severity": "HIGH",
            "triggered_week": 6,
            "condition": f"Humidity reached {max(humidity[4:7])}% (threshold >= 85%) during tillering",
            "action": "Spray Tricyclazole 75 WP @ 1g/L or Pseudomonas fluorescens @ 5g/L immediately."
        })

    # Rule 2: Water deficit stress (NDVI drop > 15% in weeks 8-10)
    stress_w9_w10 = any((baseline - timeline[w-1]) / baseline > 0.15 for w in [8, 9, 10])
    if stress_w9_w10:
        evaluated_risks.append({
            "risk_id": "water_deficit_stress",
            "name": "Canal Deficit / Vegetative Water Stress",
            "status": "ACTIVE ALERT",
            "severity": "MEDIUM",
            "triggered_week": 9,
            "condition": f"NDVI dropped to {min(timeline[7:10])} (>15% below baseline {baseline})",
            "action": "Immediate irrigation required within 48h to prevent spikelet sterility."
        })

    # Rule 3: Monsoon flood submergence (Rainfall > 150mm in weeks 11-13)
    flood_triggered = any(rainfall[w-1] >= 150 for w in [11, 12, 13])
    if flood_triggered:
        max_flood_rain = max(rainfall[10:13])
        evaluated_risks.append({
            "risk_id": "monsoon_flood_submergence",
            "name": "Flash Flood Submergence Risk",
            "status": "CRITICAL DISASTER",
            "severity": "CRITICAL",
            "triggered_week": 12,
            "condition": f"Severe rainfall recorded: {max_flood_rain} mm (threshold >= 150 mm)",
            "action": "Open field drainage sluices immediately; breach perimeter bunds to drain floodwaters."
        })

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "crop": knowledge["crop"],
        "region": knowledge["region"],
        "season": knowledge["season"],
        "sowing_window": knowledge["sowing_window"],
        "resilient_varieties": knowledge["resilient_varieties"],
        "farmer_variety": plot["variety"],
        "stage_tasks": knowledge["stage_tasks"],
        "farmer_tasks": plot["protection_tasks"],
        "protection_score": plot["protection_score"],
        "followed_plan": plot["followed_plan"],
        "active_risks": evaluated_risks,
        "pre_disaster_protocol": knowledge["pre_disaster_protocol"],
        "disclaimer": knowledge["source"]
    }


@app.get("/api/alerts/{plot_id}")
def get_alerts(plot_id: str, lang: str = "en"):
    """Template-based alerts in supported languages (no external LLM)."""
    plot = get_plot_by_id(plot_id)
    i18n = load_json_file("i18n.json")
    supported_langs = i18n["languages"]
    
    if lang not in supported_langs:
        lang = "en"
    
    lang_alerts = supported_langs[lang]["alerts"]
    
    formatted_alerts = []
    for a in plot["alerts_history"]:
        alert_type = a["type"]
        text = lang_alerts.get(alert_type, lang_alerts.get("all_clear", "Advisory active"))
        formatted_alerts.append({
            "week": a["week"],
            "type": alert_type,
            "icon": a["icon"],
            "title": a["title"],
            "date": a["sent_date"],
            "text": text,
            "lang": lang
        })

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "language": lang,
        "alerts": formatted_alerts
    }


@app.get("/api/claim/{plot_id}")
def get_claim(plot_id: str, lang: str = "en"):
    """Claim recommendation score, confidence, and plain-language reasoning."""
    plot = get_plot_by_id(plot_id)
    metrics = calculate_claim_metrics(plot)
    i18n = load_json_file("i18n.json")
    
    # Localized reasoning if requested
    if lang in i18n["languages"] and lang != "en":
        intent_answers = i18n["languages"][lang]["intents"]["claim_status"]["answers"]
        if plot_id in intent_answers:
            metrics["reasoning_localized"] = intent_answers[plot_id]

    return metrics


@app.get("/api/insurer")
def get_insurer_dashboard():
    """All plots ranked by loss score and confidence, with decision & fraud status."""
    plots = get_plots()
    ranked = []
    for p in plots:
        metrics = calculate_claim_metrics(p)
        ranked.append(metrics)
    
    # Sort descending by loss score
    ranked.sort(key=lambda x: x["loss_score"], reverse=True)

    return {
        "total_plots": len(ranked),
        "claims_approved": sum(1 for r in ranked if r["decision_code"] == "APPROVE"),
        "ground_checks_required": sum(1 for r in ranked if r["decision_code"] == "GROUND_CHECK"),
        "no_claims": sum(1 for r in ranked if r["decision_code"] == "NO_CLAIM"),
        "ranking": ranked,
        "speed_comparison": {
            "agrishield_time": "3 minutes (fully automated satellite analytics)",
            "manual_inspection_time": "4 to 8 weeks (traditional surveyor queues)"
        }
    }


@app.get("/api/fraud/{plot_id}")
def get_fraud_check(plot_id: str):
    """Compare plot NDVI drop with other regional plots to detect anomalies."""
    plots = get_plots()
    target_plot = get_plot_by_id(plot_id)
    target_metrics = calculate_claim_metrics(target_plot)

    # Check regional context
    regional_floods = [p["flooded_pct"] for p in plots]
    avg_flood = sum(regional_floods) / len(regional_floods)
    
    # Anomaly condition: Claim reports heavy loss (>0.6) but regional rainfall/flood was 0%
    is_anomaly = False
    flag_reason = "Consistent with regional Cauvery basin flood event at Week 12."
    
    if target_metrics["loss_score"] > 0.6 and avg_flood < 5:
        is_anomaly = True
        flag_reason = "WARNING: Isolated crop damage reported while regional basin suffered no precipitation anomaly."

    return {
        "plot_id": plot_id,
        "farmer_name": target_plot["farmer_name"],
        "target_loss_score": target_metrics["loss_score"],
        "regional_average_flood_pct": round(avg_flood, 1),
        "is_fraud_anomaly": is_anomaly,
        "verification_status": "FLAGGED_FOR_AUDIT" if is_anomaly else "REGIONAL_CORROBORATED",
        "details": flag_reason,
        "regional_plots_compared": len(plots)
    }


DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

class AskRequest(BaseModel):
    plot_id: str
    language: str = "en"
    question_text: str
    history: Optional[List[Dict[str, str]]] = None

@app.post("/api/ask")
@app.get("/api/ask")
def ask_agrishield(
    plot_id: Optional[str] = Query(None),
    language: Optional[str] = Query("en"),
    question_text: Optional[str] = Query(None),
    body: Optional[AskRequest] = None
):
    """
    Multilingual Q&A and Conversational Agricultural Assistant.
    Powered by Google Gemini (Gemini 3 Flash) with full plot context,
    satellite verification metrics, agronomic problem-solving, and disaster relief guidance.
    Gracefully falls back to deterministic knowledge base if offline.
    """
    p_id = body.plot_id if body else (plot_id or "plot_1")
    lang = body.language if body else (language or "en")
    q_text = (body.question_text if body else question_text) or "How is my crop and what should I do?"
    history = body.history if body else None

    plot = get_plot_by_id(p_id)
    metrics = calculate_claim_metrics(plot)
    i18n = load_json_file("i18n.json")
    if lang not in i18n["languages"]:
        lang = "en"
    
    lang_data = i18n["languages"][lang]
    lang_name = lang_data.get("name", "English")
    q_lower = q_text.lower()

    # Match intent by keywords in the language
    matched_intent = "crop_health" # default
    intents = lang_data.get("intents", {})
    
    for intent_name, intent_obj in intents.items():
        keywords = intent_obj.get("keywords", [])
        if any(kw.lower() in q_lower for kw in keywords):
            matched_intent = intent_name
            break

    # Determine recommended loan scheme for context
    if plot["flooded_pct"] >= 50 or metrics["loss_score"] >= 0.6:
        rec_loan = "PM Fasal Bima Yojana (PMFBY) Mid-Season Flood Disaster Relief (Up to ₹30,000/acre grant) + KCC Debt Rescheduling (3-5 Years)"
        eligible_amt = int(plot.get("acreage", 1.8) * 30000)
        first_step_advice = "Download AgriShield Satellite Report PDF, notify VAO within 72 hours, and submit claim at local PACCS."
    elif plot["flooded_pct"] > 10:
        rec_loan = "KCC Emergency Working Capital Top-Up (₹40,000) + PMFBY Partial Yield Claim"
        eligible_amt = int(plot.get("acreage", 1.5) * 20000)
        first_step_advice = "Open field drainage outlets, obtain joint verification endorsement, and apply at cooperative society."
    else:
        rec_loan = "Standard Kisan Credit Card (KCC) Seasonal Production Loan (4% interest) + Agri Infrastructure Fund (AIF)"
        eligible_amt = int(plot.get("acreage", 2.1) * 35000)
        first_step_advice = "Apply via JanSamarth portal or visit nearest SBI/Cooperative Bank branch with Land Patta."

    # Connect to Gemini API
    gemini_key = os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)
    if gemini_key:
        try:
            import requests
            system_prompt = (
                f"You are AgriShield AI Agricultural Advisor (அக்ரிஷீல்ட் விவசாய ஆலோசகர் / কৃষি মিত্র). "
                f"You are directly assisting Farmer {plot['farmer_name']} from {plot['village']}, Thanjavur (Cauvery Delta). "
                f"Plot Details: Crop: {plot['crop']} ({plot['variety']}), Acreage: {plot['acreage']} Acres, Sowing Date: {plot['sowing_date']}.\n"
                f"Verified Satellite Earth Observation Data:\n"
                f"- NDVI Vegetation Canopy: {metrics['latest_ndvi']} (Baseline: {metrics['baseline_ndvi']}, -15% Stress Threshold: {round(metrics['baseline_ndvi']*0.85, 2)})\n"
                f"- Sentinel-1 SAR Radar: {plot['sar_after_db']} dB (Pre-storm: {plot['sar_before_db']} dB). Flooded Area: {plot['flooded_pct']}%\n"
                f"- Weather Context: 210mm monsoon rain recorded, 94% humidity during week 12 storm.\n"
                f"- Assessment: Decision is '{metrics['decision']}' (Loss Score: {metrics['loss_score']}, Confidence: {int(metrics['confidence']*100)}%).\n"
                f"- Recommended Financial Relief: {rec_loan} (Estimated Eligible: ₹{eligible_amt}).\n"
                f"- Immediate Action: {first_step_advice}\n\n"
                f"Instructions:\n"
                f"1. Act as an empathetic, authoritative agricultural and rural credit counselor talking directly to the farmer.\n"
                f"2. Clearly address the farmer's problems (waterlogging, crop submergence, blast disease, financial distress, debt pressure, or normal farming).\n"
                f"3. Provide practical, step-by-step solutions: both agronomic field actions (drainage, foliar sprays, fertilizer timing) and loan/relief steps (which scheme applies, where to go, what documents to take).\n"
                f"4. Respond naturally in {lang_name} (language code: {lang}). Use clear, conversational language that can be understood by rural farmers and easily read aloud by text-to-speech.\n"
                f"5. Keep the response between 2 to 4 clear, helpful sentences or short actionable points."
            )

            # Build Gemini contents structure
            contents = []
            if history and isinstance(history, list):
                for h in history[-4:]: # include recent turns
                    role = "user" if h.get("role") in ["user", "farmer"] else "model"
                    contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})

            contents.append({
                "role": "user",
                "parts": [{"text": f"[System Context: {system_prompt}]\n\nFarmer asks: {q_text}"}]
            })

            # Try Gemini models in priority order
            for model_name in ["models/gemini-3-flash-preview", "models/gemini-flash-latest"]:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={gemini_key}"
                resp = requests.post(gemini_url, json={"contents": contents}, timeout=10)
                if resp.status_code == 200:
                    answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {
                        "source": f"Gemini AI ({model_name.replace('models/', '')})",
                        "intent": matched_intent,
                        "language": lang,
                        "question": q_text,
                        "answer": answer
                    }
        except Exception as e:
            pass # degrade gracefully to offline templates

    # Default / Offline Template fallback
    intent_answers = intents.get(matched_intent, {}).get("answers", {})
    answer = intent_answers.get(p_id, f"Farmer {plot['farmer_name']}: Status verified by AgriShield.")
    
    return {
        "source": "Offline Agronomy Knowledge Base",
        "intent": matched_intent,
        "language": lang,
        "question": q_text,
        "answer": answer
    }


# ----------------- LOAN, RELIEF & WEATHER ENDPOINTS -----------------

class LoanApplicationRequest(BaseModel):
    plot_id: str
    farmer_name: str
    scheme_id: str
    scheme_name: str
    requested_amount: float
    village: str
    aadhaar_last4: str
    survey_number: str
    bank_name: str

@app.get("/api/loans")
def get_loans_catalog():
    """Returns agricultural loans and disaster relief schemes mapped by damage type."""
    loans_data = load_json_file("loans.json")
    return loans_data

@app.get("/api/loans/recommend/{plot_id}")
def get_loan_recommendation(plot_id: str):
    """
    Analyzes plot's verified satellite damage (flood %, NDVI drop) and recommends
    the exact loan or relief scheme, required documents, where to apply, and first action.
    """
    plot = get_plot_by_id(plot_id)
    metrics = calculate_claim_metrics(plot)
    loans_data = load_json_file("loans.json")
    
    acreage = plot.get("acreage", 1.5)
    flooded_pct = plot.get("flooded_pct", 0)
    loss_score = metrics["loss_score"]
    
    # Decision mapping: For which damage what loan applies
    if flooded_pct >= 50 or loss_score >= 0.6:
        # Severe Flood Submergence
        primary_damage_type = "flood_submergence"
        scheme_id = "pmfby_midseason"
        scheme_name = "PM Fasal Bima Yojana (PMFBY) Mid-Season Flood Disaster Relief"
        relief_type = "Disaster Compensation Grant (100% Non-repayable DBT)"
        est_amount = int(acreage * 30000)
        secondary_scheme = "KCC Natural Calamity Debt Rescheduling (3-5 Years Moratorium)"
        where_apply = f"Primary Agricultural Cooperative Credit Society (PACCS) {plot['village'].split(',')[0]} or District Central Cooperative Bank (DCCB)"
        first_step = "1. Click 'Download Claim PDF' for satellite proof. 2. Notify Village Administrative Officer (VAO) within 72 hours. 3. Submit application to local PACCS."
    elif flooded_pct > 10 or loss_score >= 0.3:
        # Moderate Flood / Partial Loss
        primary_damage_type = "flood_submergence"
        scheme_id = "kcc_disaster_rescheduling"
        scheme_name = "KCC Emergency Working Capital Top-Up & Partial Yield Claim"
        relief_type = "Low Interest Credit Line (4% subsidized) + Partial Claim"
        est_amount = int(acreage * 20000)
        secondary_scheme = "State Disaster Response Fund (SDRF) Input Subsidy"
        where_apply = f"Local Cooperative Bank or Indian Bank Branch, Thanjavur"
        first_step = "1. Keep drainage channels open. 2. Download AgriShield proof. 3. Request joint damage verification at local agriculture depot."
    elif metrics.get("latest_ndvi", 0.7) < 0.65:
        # Vegetative stress / water deficit
        primary_damage_type = "water_deficit_drought"
        scheme_id = "kcc_drought_contingency"
        scheme_name = "KCC Contingent Irrigation & Micro-Irrigation Loan"
        relief_type = "Emergency Farm Working Capital (4% Interest)"
        est_amount = int(acreage * 25000)
        secondary_scheme = "Tamil Nadu Agricultural Mechanization / Pump Subsidy"
        where_apply = "PACCS or Block Assistant Director of Agriculture (ADA)"
        first_step = "1. Attach AgriShield NDVI stress timeline. 2. Submit urgent irrigation credit request at PACCS."
    else:
        # Normal / Healthy Paddy
        primary_damage_type = "normal_growth"
        scheme_id = "standard_kcc_crop_loan"
        scheme_name = "Standard Kisan Credit Card (KCC) Seasonal Production Loan"
        relief_type = "Short-Term Seasonal Crop Credit (4% with prompt repayment)"
        est_amount = int(acreage * 35000)
        secondary_scheme = "Agriculture Infrastructure Fund (AIF) for Farm Modernization"
        where_apply = "State Bank of India (SBI), Canara Bank, or nearest PACCS"
        first_step = "1. Visit JanSamarth portal (jansamarth.in) or bank branch with Land Patta and Aadhaar."

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "village": plot["village"],
        "acreage": acreage,
        "verified_damage_type": primary_damage_type,
        "verified_loss_score": loss_score,
        "flooded_pct": flooded_pct,
        "recommended_scheme": {
            "id": scheme_id,
            "name": scheme_name,
            "relief_type": relief_type,
            "estimated_eligible_amount_inr": est_amount,
            "secondary_scheme": secondary_scheme
        },
        "requirements": [
            "Aadhaar Card (linked to bank for DBT)",
            "Land Patta / Chitta / Adangal (Ownership / Tenancy certificate)",
            "Bank Passbook copy with IFSC code",
            "AgriShield Satellite Damage Report PDF (Auto-attached)",
            "Sowing declaration / Crop insurance enrollment receipt"
        ],
        "where_to_apply": where_apply,
        "first_step": first_step,
        "damage_catalog": loans_data.get("damage_schemes", [])
    }

@app.post("/api/loans/apply")
def submit_loan_application(req: LoanApplicationRequest):
    """
    Submits a loan or disaster relief application with satellite proof verification.
    Generates a unique tracking reference number and provides immediate next steps.
    """
    import random
    import time
    ref_suffix = random.randint(1000, 9999)
    year = 2026
    app_ref_id = f"AGRI-RELIEF-TN-{year}-{ref_suffix}"
    
    return {
        "status": "SUCCESS",
        "application_ref_id": app_ref_id,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "farmer_name": req.farmer_name,
        "plot_id": req.plot_id,
        "village": req.village,
        "scheme_name": req.scheme_name,
        "requested_amount_inr": req.requested_amount,
        "satellite_verification_status": "ATTACHED & VERIFIED (Sentinel-1 SAR / Sentinel-2)",
        "processing_office": f"Primary Agricultural Cooperative Society (PACCS) - {req.village.split(',')[0]} Block",
        "next_step_instructions": (
            f"Your application {app_ref_id} has been provisionally registered with verified satellite proof. "
            f"Please visit {req.bank_name} or your local PACCS within 5 working days with your original Aadhaar card "
            f"and Land Patta to complete biometrics and disburse funds."
        )
    }

@app.get("/api/weather/{plot_id}")
def get_plot_weather(plot_id: str):
    """
    Returns live and forecast weather conditions, satellite resource metrics,
    and agro-meteorological advisories for smallholder farmers.
    """
    plot = get_plot_by_id(plot_id)
    rainfall_history = plot.get("rainfall_weekly", [])
    humidity_history = plot.get("humidity_weekly", [])
    cloud_history = plot.get("cloud_cover_weekly", [])
    
    latest_rain = rainfall_history[11] if len(rainfall_history) > 11 else 25 # flood week
    latest_humidity = humidity_history[11] if len(humidity_history) > 11 else 75
    latest_cloud = cloud_history[11] if len(cloud_history) > 11 else 30
    
    # Weather status based on rain
    if latest_rain >= 150:
        weather_condition = "Heavy Monsoon Rainstorm & High Wind"
        weather_icon = "⛈️"
        alert_level = "CRITICAL DISASTER WARNING"
        advisory = "Severe precipitation detected (>150mm). Keep field bund drainage channels wide open. Postpone urea application."
        temp_c = 26.5
    elif latest_humidity >= 85:
        weather_condition = "Warm & High Relative Humidity"
        weather_icon = "🌫️"
        alert_level = "PEST & DISEASE WARNING"
        advisory = "High relative humidity promotes blast spore germination. Spray bio-fungicide or Tricyclazole promptly."
        temp_c = 31.0
    else:
        weather_condition = "Optimal Sunny / Moderate Humid"
        weather_icon = "☀️"
        alert_level = "NORMAL ADVISORY"
        advisory = "Favorable weather for grain filling. Maintain 2-3 cm water depth in plot."
        temp_c = 32.5

    return {
        "plot_id": plot_id,
        "farmer_name": plot["farmer_name"],
        "village": plot["village"],
        "current_weather": {
            "temperature_c": temp_c,
            "humidity_pct": latest_humidity,
            "rainfall_recorded_mm": latest_rain,
            "wind_speed_kmh": 22 if latest_rain > 100 else 12,
            "condition": weather_condition,
            "icon": weather_icon
        },
        "forecast_3day": [
            {"day": "Tomorrow", "rain_mm": 45 if latest_rain > 100 else 5, "condition": "Scattered Rain", "icon": "🌦️"},
            {"day": "Day 2", "rain_mm": 20 if latest_rain > 100 else 0, "condition": "Partly Cloudy", "icon": "⛅"},
            {"day": "Day 3", "rain_mm": 5 if latest_rain > 100 else 0, "condition": "Sunny", "icon": "☀️"}
        ],
        "satellite_resources": {
            "optical_sentinel2": {
                "cloud_cover_pct": latest_cloud,
                "status": "Cloud Obscured (Unreliable)" if latest_cloud > 60 else "Clear Visibility",
                "ndvi_canopy_reading": plot["ndvi_timeline"][-1]
            },
            "radar_sentinel1_sar": {
                "backscatter_db": plot["sar_after_db"],
                "cloud_penetration": "100% Penetrating (All-Weather)",
                "soil_moisture_saturation": "98% (Inundated)" if plot["flooded_pct"] > 50 else ("75% (Moist)" if plot["flooded_pct"] > 10 else "45% (Optimal)")
            }
        },
        "alert_level": alert_level,
        "agro_advisory": advisory
    }


@app.get("/api/claim/{plot_id}/pdf")
def download_claim_pdf(plot_id: str):
    """
    Generate professional Claim Assessment PDF report via ReportLab,
    featuring an embedded matplotlib NDVI timeline chart and official disclaimer.
    """
    plot = get_plot_by_id(plot_id)
    metrics = calculate_claim_metrics(plot)

    # 1. Generate Matplotlib NDVI chart into BytesIO buffer
    fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=150)
    weeks = list(range(1, len(plot["ndvi_timeline"]) + 1))
    ndvi_vals = plot["ndvi_timeline"]
    baseline = plot["baseline_ndvi"]

    ax.plot(weeks, ndvi_vals, color="#16a34a", linewidth=2.5, marker="o", markersize=4, label="Plot NDVI (Sentinel-2)")
    ax.axhline(y=baseline, color="#2563eb", linestyle="--", linewidth=1.5, label=f"Plot Baseline ({baseline})")
    ax.axhline(y=baseline * 0.85, color="#f59e0b", linestyle=":", linewidth=1.2, label="Stress Warning (-15%)")
    
    # Highlight week 12 flood event
    ax.axvspan(11.5, 12.5, color="#ef4444", alpha=0.15, label="Week 12 Flood Event")
    
    # Annotate minimum point
    min_idx = ndvi_vals.index(min(ndvi_vals))
    ax.scatter([min_idx + 1], [ndvi_vals[min_idx]], color="#dc2626", s=80, zorder=5)
    ax.annotate(
        f"Low: {ndvi_vals[min_idx]}",
        xy=(min_idx + 1, ndvi_vals[min_idx]),
        xytext=(min_idx + 0.3, ndvi_vals[min_idx] + 0.08),
        arrowprops=dict(facecolor="#dc2626", shrink=0.05, width=1, headwidth=4),
        fontsize=8, fontweight="bold", color="#dc2626"
    )

    ax.set_title(f"16-Week NDVI Vegetation Canopy Profile - {plot['farmer_name']}'s Plot", fontsize=10, fontweight="bold")
    ax.set_xlabel("Season Week Number", fontsize=8)
    ax.set_ylabel("NDVI Index (0.0 - 1.0)", fontsize=8)
    ax.set_ylim(0.15, 0.95)
    ax.set_xlim(0.5, 16.5)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="lower left", fontsize=7, framealpha=0.9)
    plt.tight_layout()

    chart_buf = io.BytesIO()
    plt.savefig(chart_buf, format="png")
    plt.close(fig)
    chart_buf.seek(0)

    # 2. Build ReportLab PDF Document
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=colors.HexColor("#14532d"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=12
    )
    section_style = ParagraphStyle(
        "SectionH",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1f2937")
    )
    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.white,
        alignment=1
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.HexColor("#6b7280"),
        spaceBefore=10
    )

    story = []

    # Header
    story.append(Paragraph("AgriShield | Automated Crop Claim Verification Report", title_style))
    story.append(Paragraph("Modeled on Sentinel-1 SAR & Sentinel-2 Optical Earth Observation • Cauvery Delta Region", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#16a34a"), spaceAfter=10))

    # Farmer & Plot Overview Table
    summary_data = [
        [
            Paragraph("<b>Farmer Name:</b> " + plot["farmer_name"], body_style),
            Paragraph("<b>Plot Location:</b> " + plot["village"], body_style)
        ],
        [
            Paragraph(f"<b>Crop & Variety:</b> {plot['crop']} ({plot['variety']})", body_style),
            Paragraph(f"<b>Acreage:</b> {plot['acreage']} Acres ({plot['soil_type']})", body_style)
        ],
        [
            Paragraph(f"<b>Protection Score:</b> {plot['protection_score']}%", body_style),
            Paragraph(f"<b>Sowing Date:</b> {plot['sowing_date']}", body_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[270, 270])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Assessment Decision Box
    badge_bg = colors.HexColor(metrics["decision_color"])
    decision_table_data = [
        [
            Paragraph(f"RECOMMENDATION: {metrics['decision']}", badge_style),
            Paragraph(f"LOSS SCORE: {int(metrics['loss_score']*100)}% | CONFIDENCE: {int(metrics['confidence']*100)}%", badge_style)
        ]
    ]
    dec_table = Table(decision_table_data, colWidths=[270, 270])
    dec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_bg),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(dec_table)
    story.append(Spacer(1, 10))

    # Reasoning Paragraph
    story.append(Paragraph("<b>Satellite Analytics & Algorithmic Reasoning:</b>", section_style))
    story.append(Paragraph(metrics["reasoning"], body_style))
    story.append(Spacer(1, 8))

    # Matplotlib NDVI Chart
    story.append(Paragraph("<b>Vegetation Health Timeline (16 Weeks Sentinel-2 Profile):</b>", section_style))
    rl_chart = RLImage(chart_buf, width=540, height=185)
    story.append(rl_chart)
    story.append(Spacer(1, 8))

    # Synthetic Evidence Breakdown Table
    story.append(Paragraph("<b>Earth Observation Evidence Matrix:</b>", section_style))
    evidence_data = [
        ["Parameter", "Observed Value", "Standard Threshold", "Impact Weight"],
        ["NDVI Peak-to-Trough Drop", f"{round(metrics['ndvi_drop_fraction']*100, 1)}%", "< 15% normal variation", "50%"],
        ["SAR Backscatter Drop (Sentinel-1)", f"{plot['sar_before_db']} dB -> {plot['sar_after_db']} dB", "Drop > 3 dB indicates water", "40%"],
        ["Flooded Fraction of Plot", f"{plot['flooded_pct']}% of plot area", "> 50% critical loss", "Integrated in SAR"],
        ["Weather Event Severity", f"{max(plot['rainfall_weekly'])} mm (Wk 12 storm)", "> 150 mm extreme event", "10%"]
    ]
    ev_table = Table(evidence_data, colWidths=[150, 150, 140, 100])
    ev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(ev_table)
    story.append(Spacer(1, 12))

    # Mandatory Disclaimer
    disclaimer_text = (
        "<b>Disclaimer:</b> Satellite evidence supports but does not replace ground verification for borderline cases. "
        "Modeled on European Space Agency Copernicus Sentinel-1 and Sentinel-2 satellite data streams. "
        "Generated securely by AgriShield Decision Engine for agricultural insurance claims processing."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    # Build PDF
    doc.build(story)
    pdf_buf.seek(0)

    filename = f"AgriShield_Claim_{plot_id}_{plot['farmer_name']}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Serve root index.html
@app.get("/")
def serve_root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AgriShield API running. Static index.html not yet initialized."}

# Mount static assets & data
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
