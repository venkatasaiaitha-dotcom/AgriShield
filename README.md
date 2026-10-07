# AgriShield: Protect, Predict, Prove, Pay 🌾🛡️

> **A Voice-First, Multilingual Agricultural Resilience & Parametric Claims Platform for Smallholder Farmers**  
> *Sample data modeled on ESA Copernicus Sentinel-1 (Radar SAR) and Sentinel-2 (Optical) earth observation.*

---

## ⚡ Quick Start (Runnable in ONE Command)

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Modern web browser (Chrome, Edge, Safari, Firefox)

### Run in simple commands:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate simulated Sentinel-1/2 data
python data/generate.py

# 3. Launch application server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🌾 Comprehensive Farmer Dashboard Features

The Farmer Dashboard now integrates:

### 1. 🌤️ Weather & Satellite Resource Center
- **Live Agro-Meteorological Metrics**: Real-time ambient temperature (°C), relative humidity (%), recorded weekly precipitation (mm), and wind speed (km/h).
- **Satellite Earth Observation Resources**:
  - **Sentinel-2 Optical (NDVI Canopy Index)**: MultiSpectral chlorophyll reflectance assessing canopy density vs. seasonal baseline.
  - **Sentinel-1 Radar (SAR Backscatter in dB)**: C-Band radar piercing clouds to detect soil moisture saturation and water stagnation.
  - **Cloud Obscuration Monitor**: Displays all-weather radar penetration status during monsoon cloud cover.
- **Actionable Agro-Advisory with "🔊 Listen"**: Provides real-time field suggestions (e.g. *"Open drainage channels immediately", "Hold chemical fertilizer application until floodwaters recede"*).

### 2. 🤖 Interactive Multilingual AI Chatbot (AgriShield Sahayak)
- **Voice & Text Assistant**: Farmers can ask questions in their native language (**Tamil, Hindi, Telugu, Kannada, Malayalam, English**) via microphone or text.
- **Audio Readout ("🔊 Listen")**: Every AI response includes text-to-speech so farmers who cannot read can listen to advice aloud.
- **Quick Question Chips**:
  - 🌦️ *Today's Weather & Rain Forecast*
  - 🌱 *Analyse My Crop Health*
  - 🏦 *What Loan Can I Get For This Damage?*
  - 📋 *Required Documents for Relief*
  - 🚨 *What Is My First Step Right Now?*
- **Context-Aware Recommendations**: Chatbot knows the selected farmer's plot condition, verified damage %, and recommended schemes.

### 3. 🏛️ Agricultural Loans & Disaster Relief Portal
- **"For Which Damage What Loan Applies?" Interactive Guide**:
  - 🌊 **Flood / Submergence Damage**: PMFBY Mid-Season Adversity Claim (Grant up to ₹30,000/acre), KCC Calamity Debt Rescheduling (3–5 year moratorium), SDRF Input Subsidy.
  - ☀️ **Drought / Canal Lag**: KCC Contingent Irrigation Credit, Micro-irrigation Subsidies.
  - 🐛 **Pest / Blast Disease Attack**: Emergency Bio-Fungicide Subsidy, Short-Term Crop Protection Working Capital.
  - 🌱 **Normal / Healthy Season**: Standard Kisan Credit Card (KCC) Seasonal Production Loan (₹3 Lakh @ 4%), Agriculture Infrastructure Fund (AIF).
- **First Step What Farmer Must Take (Step-by-Step Roadmap)**:
  - 1️⃣ **Step 1:** Download AgriShield Satellite Proof PDF (instant verified proof).
  - 2️⃣ **Step 2:** Intimate Village Administrative Officer (VAO) within 72 hours.
  - 3️⃣ **Step 3:** Submit claim to local PACCS / Bank branch with the auto-attached satellite certificate.
- **Required Documents Checklist**: Aadhaar Card, Land Patta/Chitta, Bank Passbook IFSC, AgriShield Satellite Report, Sowing Declaration.
- **Instant 1-Click Loan Application Form (Modal)**:
  - Pre-filled with farmer name, village, acreage, damage %, recommended scheme, and eligible amount.
  - Generates official **Application Reference Number** (e.g. `AGRI-RELIEF-TN-2026-9482`).
  - Auto-attaches Sentinel-1/2 verification certificate.
  - Provides downloadable/printable **Acknowledgment Receipt Slip** and voice confirmation.

---

## 🌟 The Core Four Pillars & Insurer Mode

1. **PROTECT**: Sowing window guidelines, flood-tolerant varieties (**Swarna Sub1** surviving 14 days submergence), task checklist with dynamic compliance score, 16-week risk calendar (Blast, Water Stress, Flood).
2. **PREDICT**: Interactive Leaflet plot map, 16-week Chart.js NDVI timeline, SMS/IVR phone simulator with feature phone audio playback.
3. **PROVE**: Sentinel-1 SAR 20×20 grid overlay (400 cells), Optical vs. Radar view toggle simulating 92% monsoon cloud cover vs. clear radar penetration.
4. **PAY**: Transparent claims formula:
   $$\text{Loss Score} = (0.5 \times \text{NDVI Drop}) + (0.4 \times \text{Flooded Fraction}) + (0.1 \times \text{Weather Severity})$$
   - Algorithmic triage: **RECOMMEND APPROVE**, **TARGETED GROUND CHECK**, **NO CLAIM**.
   - Downloadable ReportLab PDF claims certificate with embedded matplotlib NDVI chart.
5. **INSURER DASHBOARD & COMPARISON**:
   - Ranked triage table, regional fraud anomaly verification, 3-minute settlement speed comparison, and side-by-side comparison of Murugan vs. Lakshmi.

---

## 📡 API Endpoints Summary

| Endpoint | Method | Description |
|---|---|---|
| `/api/plots` | `GET` | List all 3 Thanjavur demo farmers and summary metadata |
| `/api/plot/{id}/health` | `GET` | 16-week NDVI timeline, baseline, stress flag, and health color |
| `/api/plot/{id}/flood` | `GET` | SAR before/after dB, flooded %, and 20×20 cell grid overlay |
| `/api/plan/{id}` | `GET` | Agronomy protection plan evaluated against plot weather |
| `/api/alerts/{id}` | `GET` | Localized template alerts across all 6 languages |
| `/api/claim/{id}` | `GET` | Algorithmic loss score, confidence %, and plain-language reasoning |
| `/api/claim/{id}/pdf` | `GET` | Downloadable ReportLab PDF with embedded matplotlib NDVI chart |
| `/api/weather/{id}` | `GET` | Live weather, 3-day forecast, satellite resources & agro-advisories |
| `/api/loans` | `GET` | Complete catalog of agricultural loans mapped by damage type |
| `/api/loans/recommend/{id}` | `GET` | Recommends specific loan/relief scheme based on plot damage |
| `/api/loans/apply` | `POST` | Submits loan/relief application, generates reference ID & receipt |
| `/api/insurer` | `GET` | All plots ranked by loss score with processing speed comparison |
| `/api/fraud/{id}` | `GET` | Regional spatial anomaly cross-verification |
| `/api/ask` | `POST/GET`| Multilingual AI chatbot assistant (weather, health, loans, first steps) |

---

## 🗣️ Supported Languages

- **Tamil** (`தமிழ்`)
- **Hindi** (`हिन्दी`)
- **Telugu** (`తెలుగు`)
- **Kannada** (`ಕನ್ನಡ`)
- **Malayalam** (`മലയാളം`)
- **English** (`English`)
