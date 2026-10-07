#!/usr/bin/env python3
"""
AgriShield - Demo Data Generator
Generates realistic simulated satellite and agronomy data modeled on Sentinel-1 (SAR)
and Sentinel-2 (Optical) for 3 paddy farmers in Thanjavur, Tamil Nadu.
"""

import json
import random
import os

def generate_plots_data():
    random.seed(42)

    # Common weather patterns for Thanjavur Samba season (16 weeks)
    # Week 12 corresponds to severe NE Monsoon storm / cyclone
    base_rainfall_flood_zone = [
        12, 18, 25, 15, 30, 45, 65, 20, 5, 8, 85, 210, 60, 25, 10, 5
    ]
    base_rainfall_shielded_zone = [
        10, 15, 20, 12, 25, 35, 40, 15, 12, 10, 40, 45, 25, 15, 8, 4
    ]
    
    # Humidity % (spikes weeks 5-7 to trigger Blast disease alert, and week 12)
    humidity_profile = [
        68, 70, 72, 75, 88, 89, 87, 76, 70, 68, 82, 94, 88, 74, 70, 65
    ]

    # Cloud cover % (optical Sentinel-2 blinded during monsoon week 11-13)
    cloud_cover_profile = [
        15, 20, 25, 30, 65, 70, 60, 25, 15, 20, 85, 96, 88, 35, 20, 15
    ]

    # Generate 20x20 SAR backscatter grid for flood mapping
    # Rule for flooded cell: (after_db - before_db < -3.0) and (after_db < -15.0)
    def create_sar_grid(target_flooded_ratio, center_lat, center_lon):
        grid = []
        total_cells = 400  # 20x20
        target_flooded_count = int(total_cells * target_flooded_ratio)
        
        # Create 20x20 cells
        # Cell indices clustered around center or low drainage corner
        flooded_indices = set()
        
        if target_flooded_ratio >= 0.7:
            # Most cells flooded except small corner bunds
            candidates = list(range(total_cells))
            random.shuffle(candidates)
            flooded_indices = set(candidates[:target_flooded_count])
        elif target_flooded_ratio >= 0.25:
            # Clustered in lower half (depression)
            candidates = [r * 20 + c for r in range(8, 20) for c in range(20)]
            random.shuffle(candidates)
            flooded_indices = set(candidates[:target_flooded_count])
        else:
            # Just isolated puddle cells
            candidates = list(range(total_cells))
            random.shuffle(candidates)
            flooded_indices = set(candidates[:target_flooded_count])

        step = 0.00004
        for r in range(20):
            row_cells = []
            for c in range(20):
                idx = r * 20 + c
                is_flooded = idx in flooded_indices
                before_db = round(random.uniform(-8.8, -7.5), 2)
                if is_flooded:
                    # Flood condition: drop > 3dB and after < -15dB
                    after_db = round(random.uniform(-21.5, -16.0), 2)
                else:
                    # Non-flooded: small attenuation or stable
                    after_db = round(before_db + random.uniform(-1.8, 0.5), 2)
                    if after_db < -14.5:
                        after_db = -14.2
                
                cell_lat = round(center_lat - (r - 10) * step, 6)
                cell_lon = round(center_lon + (c - 10) * step, 6)
                row_cells.append({
                    "row": r,
                    "col": c,
                    "lat": cell_lat,
                    "lon": cell_lon,
                    "before_db": before_db,
                    "after_db": after_db,
                    "delta_db": round(after_db - before_db, 2),
                    "is_flooded": is_flooded
                })
            grid.append(row_cells)
        return grid

    plots = [
        {
            "id": "plot_1",
            "farmer_name": "Murugan",
            "farmer_title": "Farmer Murugan (முருகு)",
            "village": "Punnainallur, Thanjavur District",
            "lat": 10.7825,
            "lon": 79.1350,
            "polygon": [
                [10.7820, 79.1344],
                [10.7831, 79.1345],
                [10.7830, 79.1357],
                [10.7819, 79.1355],
                [10.7820, 79.1344]
            ],
            "crop": "Paddy (Rice)",
            "variety": "CR 1009 (Standard / Non-tolerant)",
            "acreage": 1.8,
            "soil_type": "Clay Loam (Cauvery Alluvial)",
            "sowing_date": "2026-06-15",
            "followed_plan": False,
            "protection_score": 25,
            "protection_tasks": [
                {"week": 2, "task": "Pre-sowing seed treatment with Trichoderma", "done": False},
                {"week": 4, "task": "Clear secondary drainage channels", "done": False},
                {"week": 6, "task": "Blast prophylactic bio-spray during humidity spike", "done": False},
                {"week": 9, "task": "Irrigate to resolve NDVI vegetative water stress", "done": False},
                {"week": 11, "task": "Open perimeter bund drainage sluices ahead of storm", "done": True}
            ],
            "ndvi_timeline": [
                0.72, 0.74, 0.76, 0.78, 0.79, 0.78, 0.77, 0.75,
                0.58, 0.52, 0.55, 0.25, 0.24, 0.25, 0.26, 0.27
            ],
            "baseline_ndvi": 0.76,
            "sar_before_db": -8.1,
            "sar_after_db": -19.8,
            "flooded_pct": 78,
            "rainfall_weekly": base_rainfall_flood_zone,
            "humidity_weekly": humidity_profile,
            "cloud_cover_weekly": cloud_cover_profile,
            "alerts_history": [
                {
                    "week": 6,
                    "type": "blast_risk",
                    "icon": "🐛",
                    "title": "Blast Disease High Humidity Alert",
                    "sent_date": "2026-07-22"
                },
                {
                    "week": 9,
                    "type": "water_stress",
                    "icon": "💧",
                    "title": "Canal Deficit Water Stress Alert",
                    "sent_date": "2026-08-12"
                },
                {
                    "week": 12,
                    "type": "flood_warning",
                    "icon": "🌧️",
                    "title": "Monsoon Flash Flood Warning",
                    "sent_date": "2026-09-02"
                }
            ],
            "sar_grid": create_sar_grid(0.78, 10.7825, 79.1350)
        },
        {
            "id": "plot_2",
            "farmer_name": "Lakshmi",
            "farmer_title": "Farmer Lakshmi (லட்சுமி)",
            "village": "Kallaperambur, Thanjavur District",
            "lat": 10.7890,
            "lon": 79.1420,
            "polygon": [
                [10.7885, 79.1413],
                [10.7896, 79.1415],
                [10.7895, 79.1428],
                [10.7884, 79.1426],
                [10.7885, 79.1413]
            ],
            "crop": "Paddy (Rice)",
            "variety": "Swarna Sub1 (Flood Submergence Tolerant)",
            "acreage": 1.5,
            "soil_type": "Clay Loam (Cauvery Alluvial)",
            "sowing_date": "2026-06-18",
            "followed_plan": True,
            "protection_score": 85,
            "protection_tasks": [
                {"week": 2, "task": "Sow certified flood-tolerant Swarna Sub1 seeds", "done": True},
                {"week": 4, "task": "Deep trench bund clearing & outlet sluice inspection", "done": True},
                {"week": 6, "task": "Blast prophylactic bio-spray during humidity spike", "done": True},
                {"week": 9, "task": "Scheduled irrigation maintained healthy vegetative canopy", "done": True},
                {"week": 11, "task": "Pre-storm drainage sluice opening & bund reinforcement", "done": True}
            ],
            "ndvi_timeline": [
                0.71, 0.73, 0.75, 0.77, 0.78, 0.79, 0.78, 0.76,
                0.75, 0.74, 0.72, 0.55, 0.56, 0.58, 0.59, 0.60
            ],
            "baseline_ndvi": 0.75,
            "sar_before_db": -8.0,
            "sar_after_db": -14.2,
            "flooded_pct": 30,
            "rainfall_weekly": base_rainfall_flood_zone,
            "humidity_weekly": humidity_profile,
            "cloud_cover_weekly": cloud_cover_profile,
            "alerts_history": [
                {
                    "week": 6,
                    "type": "blast_risk",
                    "icon": "🐛",
                    "title": "Blast Disease High Humidity Alert",
                    "sent_date": "2026-07-22"
                },
                {
                    "week": 12,
                    "type": "flood_warning",
                    "icon": "🌧️",
                    "title": "Monsoon Flash Flood Warning",
                    "sent_date": "2026-09-02"
                }
            ],
            "sar_grid": create_sar_grid(0.30, 10.7890, 79.1420)
        },
        {
            "id": "plot_3",
            "farmer_name": "Selvam",
            "farmer_title": "Farmer Selvam (செல்வம்)",
            "village": "Vallam Upland, Thanjavur District",
            "lat": 10.7950,
            "lon": 79.1310,
            "polygon": [
                [10.7944, 79.1303],
                [10.7957, 79.1305],
                [10.7955, 79.1318],
                [10.7943, 79.1316],
                [10.7944, 79.1303]
            ],
            "crop": "Paddy (Rice)",
            "variety": "CO 51 (High Yielding Upland)",
            "acreage": 2.1,
            "soil_type": "Sandy Clay Loam",
            "sowing_date": "2026-06-12",
            "followed_plan": True,
            "protection_score": 90,
            "protection_tasks": [
                {"week": 2, "task": "Soil test based basal fertilizer application", "done": True},
                {"week": 4, "task": "SRI line transplanting with 25cm spacing", "done": True},
                {"week": 6, "task": "Blast prophylactic spray applied", "done": True},
                {"week": 9, "task": "Alternate wetting and drying irrigation followed", "done": True},
                {"week": 11, "task": "Elevated perimeter drainage operational", "done": True}
            ],
            "ndvi_timeline": [
                0.72, 0.74, 0.76, 0.78, 0.79, 0.81, 0.80, 0.79,
                0.78, 0.79, 0.77, 0.76, 0.77, 0.78, 0.79, 0.80
            ],
            "baseline_ndvi": 0.78,
            "sar_before_db": -8.2,
            "sar_after_db": -8.5,
            "flooded_pct": 2,
            "rainfall_weekly": base_rainfall_shielded_zone,
            "humidity_weekly": [65, 68, 70, 72, 75, 78, 74, 70, 66, 65, 72, 76, 72, 68, 64, 62],
            "cloud_cover_weekly": [12, 15, 20, 22, 45, 50, 40, 20, 12, 15, 55, 60, 45, 25, 15, 10],
            "alerts_history": [
                {
                    "week": 1,
                    "type": "all_clear",
                    "icon": "🌱",
                    "title": "Season Start Welcome Advisory",
                    "sent_date": "2026-06-15"
                }
            ],
            "sar_grid": create_sar_grid(0.02, 10.7950, 79.1310)
        }
    ]

    out_path = os.path.join(os.path.dirname(__file__), "plots.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"sample_notice": "Sample data modeled on Sentinel-1 and Sentinel-2", "plots": plots}, f, indent=2, ensure_ascii=False)
    
    print(f"Generated demo plots data successfully at: {out_path}")

if __name__ == "__main__":
    generate_plots_data()
