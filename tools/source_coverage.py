#!/usr/bin/env python3
"""Print a compact coverage matrix from the course-source manifest."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/"config/course-source-manifest.json").read_text(encoding="utf-8"))
years = [2018, 2019, 2022, 2023, 2024, 2025, 2026]
families = ["ultra60", "trail22", "trail14", "trail5"]

for family in families:
    print(f"\n{family}")
    for year in years:
        src = [s for s in data["sources"] if s.get("family")==family and (s.get("year")==year or isinstance(s.get("year"), list) and year in s["year"])]
        statuses = ", ".join(f"{s['source_type']}:{s['status']}" for s in src) or "MISSING"
        print(f"  {year}: {statuses}")
