#!/usr/bin/env python3
"""Print a compact public-result roster for short-course GPS source matching.

This is a research helper only. It reads the already-curated local ÖST database,
does no network access, and prints fields needed to cross-match public activity
recordings against Sportstiming: year, family, name, bib, official time and place.
"""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path
import shutil
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DB_GZ = ROOT / "data/derived/ost-analysis-2018-2026.sqlite.gz"


def fmt_time(value: float | None) -> str:
    if value is None:
        return ""
    sec = int(round(value))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", action="append", type=int, dest="years")
    ap.add_argument("--family", action="append", choices=["trail14", "trail5"], dest="families")
    args = ap.parse_args()
    years = args.years or [2018, 2019, 2022, 2023, 2024, 2025, 2026]
    families = args.families or ["trail14", "trail5"]

    with tempfile.TemporaryDirectory(prefix="ost-short-roster-") as td:
        db = Path(td) / "ost.sqlite"
        with gzip.open(DB_GZ, "rb") as src, db.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        q = """
        SELECT year, race_family, name_as_published, bib, source_result_id,
               status, finish_seconds, net_seconds, gross_seconds,
               overall_place, gender_place, class_place, source_class
        FROM results
        WHERE race_family IN ({families})
          AND year IN ({years})
        ORDER BY year, race_family,
                 CASE WHEN overall_place IS NULL THEN 1 ELSE 0 END,
                 overall_place, finish_seconds, name_as_published
        """.format(
            families=",".join("?" for _ in families),
            years=",".join("?" for _ in years),
        )
        rows = con.execute(q, [*families, *years]).fetchall()
        con.close()

    print("year\tfamily\tname\tbib\tresult_id\tstatus\tfinish\tnet\tgross\toverall\tgender\tclass_place\tsource_class")
    for r in rows:
        vals = [
            str(r["year"]),
            r["race_family"] or "",
            (r["name_as_published"] or "").replace("\t", " "),
            r["bib"] or "",
            r["source_result_id"] or "",
            r["status"] or "",
            fmt_time(r["finish_seconds"]),
            fmt_time(r["net_seconds"]),
            fmt_time(r["gross_seconds"]),
            "" if r["overall_place"] is None else str(r["overall_place"]),
            "" if r["gender_place"] is None else str(r["gender_place"]),
            "" if r["class_place"] is None else str(r["class_place"]),
            r["source_class"] or "",
        ]
        print("\t".join(vals))
    print(f"ROWS\t{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
