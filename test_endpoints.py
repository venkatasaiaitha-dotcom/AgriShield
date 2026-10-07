#!/usr/bin/env python3
"""
AgriShield Comprehensive API and Integration Test Suite
Verifies all 10 endpoints, data integrity, calculations, PDF generation, and multilingual responses.
"""

import sys
import io

# Ensure UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 60)
    print("RUNNING AGRISHIELD TEST SUITE")
    print("=" * 60)
    failures = []

    # 1. Test Static Files & Index
    print("\n[1] Testing Static Delivery & Root HTML...")
    try:
        r = requests.get(f"{BASE_URL}/")
        assert r.status_code == 200, f"Root returned {r.status_code}"
        assert "AgriShield" in r.text, "AgriShield title missing in HTML"
        assert "Farmer Voice Mode" in r.text, "Farmer Voice Mode missing in HTML"
        print("  [OK] Root index.html served correctly")

        r_js = requests.get(f"{BASE_URL}/static/app.js")
        assert r_js.status_code == 200, "app.js returned non-200"
        print("  [OK] static/app.js accessible")

        r_css = requests.get(f"{BASE_URL}/static/style.css")
        assert r_css.status_code == 200, "style.css returned non-200"
        print("  [OK] static/style.css accessible")
    except Exception as e:
        print(f"  [FAIL] {e}")
        failures.append(str(e))

    # 2. Test /api/plots
    print("\n[2] Testing GET /api/plots...")
    try:
        r = requests.get(f"{BASE_URL}/api/plots")
        assert r.status_code == 200, f"Plots returned {r.status_code}"
        data = r.json()
        plots = data.get("plots", [])
        assert len(plots) == 3, f"Expected 3 plots, got {len(plots)}"
        plot_ids = [p["id"] for p in plots]
        assert "plot_1" in plot_ids and "plot_2" in plot_ids and "plot_3" in plot_ids
        print(f"  [OK] Found 3 farmers: {[p['farmer_name'] for p in plots]}")
    except Exception as e:
        print(f"  [FAIL] {e}")
        failures.append(str(e))

    # 3. Test Each Plot's Health, Flood, Plan, Alerts, Claims, Fraud, and PDF
    for p_id in ["plot_1", "plot_2", "plot_3"]:
        print(f"\n[3] Testing Plot '{p_id}' endpoints...")
        
        # Health
        try:
            r = requests.get(f"{BASE_URL}/api/plot/{p_id}/health")
            assert r.status_code == 200
            h = r.json()
            assert len(h["ndvi_timeline"]) == 16, "Expected 16 weeks of NDVI"
            assert "baseline_ndvi" in h and "health_color" in h
            print(f"  [OK] Health: Color={h['health_color']}, Latest NDVI={h['latest_ndvi']}, Stressed={h['is_stressed']}")
        except Exception as e:
            print(f"  [FAIL] Health failed for {p_id}: {e}")
            failures.append(f"{p_id} health: {e}")

        # Flood
        try:
            r = requests.get(f"{BASE_URL}/api/plot/{p_id}/flood")
            assert r.status_code == 200
            f = r.json()
            grid = f["grid"]
            assert len(grid) == 20 and len(grid[0]) == 20, "Expected 20x20 SAR grid"
            print(f"  [OK] Flood: SAR before={f['sar_before_db']} dB, after={f['sar_after_db']} dB, Flooded={f['flooded_pct']}%")
        except Exception as e:
            print(f"  [FAIL] Flood failed for {p_id}: {e}")
            failures.append(f"{p_id} flood: {e}")

        # Plan
        try:
            r = requests.get(f"{BASE_URL}/api/plan/{p_id}")
            assert r.status_code == 200
            p = r.json()
            assert "resilient_varieties" in p and "stage_tasks" in p
            print(f"  [OK] Plan: Variety={p['farmer_variety']}, Protection Score={p['protection_score']}%, Active Risks={len(p['active_risks'])}")
        except Exception as e:
            print(f"  [FAIL] Plan failed for {p_id}: {e}")
            failures.append(f"{p_id} plan: {e}")

        # Alerts (in English and Tamil)
        try:
            r_en = requests.get(f"{BASE_URL}/api/alerts/{p_id}?lang=en")
            r_ta = requests.get(f"{BASE_URL}/api/alerts/{p_id}?lang=ta")
            assert r_en.status_code == 200 and r_ta.status_code == 200
            print(f"  [OK] Alerts: EN and TA returned {len(r_en.json()['alerts'])} alerts")
        except Exception as e:
            print(f"  [FAIL] Alerts failed for {p_id}: {e}")
            failures.append(f"{p_id} alerts: {e}")

        # Claim Decision
        try:
            r = requests.get(f"{BASE_URL}/api/claim/{p_id}")
            assert r.status_code == 200
            c = r.json()
            assert "loss_score" in c and "confidence" in c and "decision" in c
            print(f"  [OK] Claim: Loss={c['loss_score']}, Conf={c['confidence']}, Decision={c['decision']}")
            if p_id == "plot_1":
                assert c["decision"] == "RECOMMEND APPROVE", f"Expected RECOMMEND APPROVE for Murugan, got {c['decision']}"
            elif p_id == "plot_2":
                assert c["decision"] == "TARGETED GROUND CHECK", f"Expected TARGETED GROUND CHECK for Lakshmi, got {c['decision']}"
            elif p_id == "plot_3":
                assert c["decision"] == "NO CLAIM", f"Expected NO CLAIM for Selvam, got {c['decision']}"
        except Exception as e:
            print(f"  [FAIL] Claim failed for {p_id}: {e}")
            failures.append(f"{p_id} claim: {e}")

        # PDF Generation
        try:
            r = requests.get(f"{BASE_URL}/api/claim/{p_id}/pdf")
            assert r.status_code == 200, f"PDF status {r.status_code}"
            assert r.headers.get("content-type") == "application/pdf"
            pdf_bytes = r.content
            assert len(pdf_bytes) > 5000, f"PDF file size suspiciously small: {len(pdf_bytes)} bytes"
            assert pdf_bytes.startswith(b"%PDF"), "Generated file does not have valid PDF magic bytes"
            print(f"  [OK] PDF: Generated successfully ({len(pdf_bytes)} bytes, valid %PDF header)")
        except Exception as e:
            print(f"  [FAIL] PDF failed for {p_id}: {e}")
            failures.append(f"{p_id} pdf: {e}")

        # Fraud check
        try:
            r = requests.get(f"{BASE_URL}/api/fraud/{p_id}")
            assert r.status_code == 200
            fr = r.json()
            assert "verification_status" in fr
            print(f"  [OK] Fraud Check: Status={fr['verification_status']}")
        except Exception as e:
            print(f"  [FAIL] Fraud Check failed for {p_id}: {e}")
            failures.append(f"{p_id} fraud: {e}")

    # 4. Test Insurer Dashboard
    print("\n[4] Testing GET /api/insurer...")
    try:
        r = requests.get(f"{BASE_URL}/api/insurer")
        assert r.status_code == 200
        ins = r.json()
        assert len(ins["ranking"]) == 3
        assert ins["claims_approved"] == 1
        assert ins["ground_checks_required"] == 1
        assert ins["no_claims"] == 1
        print("  [OK] Insurer Dashboard: 1 Approve, 1 Ground Check, 1 No Claim correctly triaged")
    except Exception as e:
        print(f"  [FAIL] Insurer Dashboard failed: {e}")
        failures.append(f"insurer: {e}")

    # 5. Test Multilingual Ask Intent Engine
    print("\n[5] Testing POST /api/ask across 6 languages...")
    languages = ["ta", "hi", "te", "kn", "ml", "en"]
    for lang in languages:
        try:
            payload = {
                "plot_id": "plot_1",
                "language": lang,
                "question_text": "How is my crop?"
            }
            r = requests.post(f"{BASE_URL}/api/ask", json=payload)
            assert r.status_code == 200
            data = r.json()
            assert "answer" in data and len(data["answer"]) > 5
            print(f"  [OK] Language '{lang}': Answered -> {data['answer'][:50]}...")
        except Exception as e:
            print(f"  [FAIL] Ask failed for {lang}: {e}")
            failures.append(f"ask {lang}: {e}")

    # 6. Test Weather & Satellite Resources
    print("\n[6] Testing GET /api/weather/{plot_id}...")
    for p_id in ["plot_1", "plot_2", "plot_3"]:
        try:
            r = requests.get(f"{BASE_URL}/api/weather/{p_id}")
            assert r.status_code == 200
            w = r.json()
            assert "current_weather" in w and "satellite_resources" in w
            print(f"  [OK] Weather {p_id}: Temp={w['current_weather']['temperature_c']}°C, Rain={w['current_weather']['rainfall_recorded_mm']}mm, Alert='{w['alert_level']}'")
        except Exception as e:
            print(f"  [FAIL] Weather failed for {p_id}: {e}")
            failures.append(f"weather {p_id}: {e}")

    # 7. Test Loans Catalog, Recommendation & Application
    print("\n[7] Testing Agricultural Loans & Relief Endpoints...")
    try:
        r_cat = requests.get(f"{BASE_URL}/api/loans")
        assert r_cat.status_code == 200
        cat = r_cat.json()
        assert len(cat["damage_schemes"]) >= 4
        print(f"  [OK] Loans Catalog: {len(cat['damage_schemes'])} damage categories loaded")
    except Exception as e:
        print(f"  [FAIL] Loans catalog failed: {e}")
        failures.append(f"loans catalog: {e}")

    for p_id in ["plot_1", "plot_2", "plot_3"]:
        try:
            r_rec = requests.get(f"{BASE_URL}/api/loans/recommend/{p_id}")
            assert r_rec.status_code == 200
            rec = r_rec.json()
            assert "recommended_scheme" in rec and "first_step" in rec
            print(f"  [OK] Loan Recommendation {p_id}: Scheme='{rec['recommended_scheme']['name']}', Eligible=₹{rec['recommended_scheme']['estimated_eligible_amount_inr']}")
        except Exception as e:
            print(f"  [FAIL] Loan rec failed for {p_id}: {e}")
            failures.append(f"loan rec {p_id}: {e}")

    # Test Loan Application Submission
    try:
        apply_payload = {
            "plot_id": "plot_1",
            "farmer_name": "Murugan",
            "scheme_id": "pmfby_midseason",
            "scheme_name": "PM Fasal Bima Yojana (PMFBY) Mid-Season Flood Disaster Relief",
            "requested_amount": 54000.0,
            "village": "Punnainallur, Thanjavur District",
            "aadhaar_last4": "8821",
            "survey_number": "142/3B",
            "bank_name": "Punnainallur PACCS / Indian Bank"
        }
        r_apply = requests.post(f"{BASE_URL}/api/loans/apply", json=apply_payload)
        assert r_apply.status_code == 200
        app_res = r_apply.json()
        assert app_res["status"] == "SUCCESS"
        assert "application_ref_id" in app_res
        print(f"  [OK] Loan Application: Submitted successfully -> Ref ID: {app_res['application_ref_id']}")
    except Exception as e:
        print(f"  [FAIL] Loan apply failed: {e}")
        failures.append(f"loan apply: {e}")

    print("\n" + "=" * 60)
    if not failures:
        print("[SUCCESS] ALL TESTS PASSED! ZERO ERRORS.")
        print("=" * 60)
        return True
    else:
        print(f"[FAIL] {len(failures)} TESTS FAILED:")
        for f in failures:
            print(f" - {f}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
