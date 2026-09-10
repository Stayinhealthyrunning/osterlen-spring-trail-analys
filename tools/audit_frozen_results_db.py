#!/usr/bin/env python3
"""Deep quality audit of the frozen ÖST Sportstiming result archive.

The audit is read-only. It verifies archive hashes/integrity, coverage, result field
quality, status consistency, split chronology and checkpoint semantics. It writes
aggregate diagnostics only; participant names are never written to reports.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse, gzip, hashlib, json, os, re, shutil, sqlite3, tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GZ = ROOT / 'data/archive/ost-results-2018-2026.sqlite.gz'
SUMMARY = ROOT / 'reports/result-archive-summary.json'
OUT_JSON = ROOT / 'reports/result-archive-audit.json'
OUT_MD = ROOT / 'reports/result-archive-audit.md'

EXPECTED_YEARS = {2018, 2019, 2022, 2023, 2024, 2025, 2026}
EXPECTED_FAMILIES_BY_YEAR = {
    2018: {'ultra60', 'trail22', 'trail14', 'trail5'},
    2019: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
    2022: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
    2023: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
    2024: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
    2025: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
    2026: {'ultra60', 'duo60', 'trail22', 'trail14', 'trail5'},
}
STATUS_WORD_RE = re.compile(
    r'\b(dnf|dns|dsq|dq|did not finish|did not start|disqual|retired|abandon|brutit|bröt|brutet|ej start|inte start|utgått)\b',
    re.I,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def q1(con: sqlite3.Connection, sql: str, args=()):
    return con.execute(sql, args).fetchone()[0]


def rows_dict(con: sqlite3.Connection, sql: str, args=()):
    cur = con.execute(sql, args)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def percent(n, d):
    return round(100.0 * n / d, 2) if d else None


def extract_status_words(raw_json: str) -> list[str]:
    try:
        obj = json.loads(raw_json)
    except Exception:
        return []
    vals = []
    for table in obj.get('raw_tables', []):
        for row in table.get('rows', []):
            texts = [(c.get('text') or '').strip() for c in row]
            if not texts:
                continue
            for text in texts:
                if STATUS_WORD_RE.search(text):
                    vals.extend(m.group(0).lower() for m in STATUS_WORD_RE.finditer(text))
    return vals


def audit(db: Path, gz: Path | None, summary: dict) -> dict:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required_tables = {'meta', 'imports', 'results', 'splits', 'derived_metrics', 'source_errors'}
    missing_tables = sorted(required_tables - tables)
    integrity = q1(con, 'PRAGMA integrity_check')

    import_rows = rows_dict(con, '''
        SELECT year,race_family,event_id,distance_id,entity_type,discovered_count,normalized_count,source_errors
        FROM imports ORDER BY year,race_family
    ''')
    result_rows = rows_dict(con, '''
        SELECT year,race_family,entity_type,
               COUNT(*) AS results,
               SUM(status='FINISHED') AS finished,
               SUM(status='UNKNOWN') AS unknown,
               SUM(CASE WHEN name IS NULL OR TRIM(name)='' THEN 1 ELSE 0 END) AS missing_name,
               SUM(CASE WHEN bib IS NULL OR TRIM(bib)='' THEN 1 ELSE 0 END) AS missing_bib,
               SUM(CASE WHEN gender IS NULL OR TRIM(gender)='' THEN 1 ELSE 0 END) AS missing_gender,
               SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) AS missing_age,
               SUM(CASE WHEN club IS NULL OR TRIM(club)='' THEN 1 ELSE 0 END) AS missing_club,
               SUM(CASE WHEN country IS NULL OR TRIM(country)='' THEN 1 ELSE 0 END) AS missing_country
        FROM results GROUP BY year,race_family,entity_type ORDER BY year,race_family
    ''')
    statuses = rows_dict(con, 'SELECT status,COUNT(*) AS n FROM results GROUP BY status ORDER BY n DESC,status')
    checkpoint_rows = rows_dict(con, '''
        SELECT r.year,r.race_family,s.checkpoint_source_label,s.checkpoint_semantic_key,s.checkpoint_role,
               s.analysis_primary,COUNT(*) AS passages,
               SUM(s.elapsed_seconds IS NULL) AS missing_elapsed,
               SUM(s.segment_seconds IS NULL) AS missing_segment
        FROM splits s JOIN results r ON r.result_uid=s.result_uid
        GROUP BY r.year,r.race_family,s.checkpoint_source_label,s.checkpoint_semantic_key,s.checkpoint_role,s.analysis_primary
        ORDER BY r.year,r.race_family,MIN(s.sequence_no)
    ''')

    total_results = q1(con, 'SELECT COUNT(*) FROM results')
    total_splits = q1(con, 'SELECT COUNT(*) FROM splits')
    total_metrics = q1(con, 'SELECT COUNT(*) FROM derived_metrics')
    total_source_errors = q1(con, 'SELECT COUNT(*) FROM source_errors')
    imports_count = q1(con, 'SELECT COUNT(*) FROM imports')

    checks = {}
    checks['missing_required_tables'] = missing_tables
    checks['integrity_check'] = integrity
    checks['imports_count'] = imports_count
    checks['source_errors'] = total_source_errors
    checks['import_count_mismatches'] = sum(1 for r in import_rows if r['discovered_count'] != r['normalized_count'])
    checks['empty_imports'] = sum(1 for r in import_rows if r['discovered_count'] <= 0)
    checks['duplicate_source_result_keys'] = q1(con, '''
        SELECT COUNT(*) FROM (
          SELECT event_id,entity_type,source_result_id,COUNT(*) c FROM results
          GROUP BY event_id,entity_type,source_result_id HAVING c>1
        )
    ''')
    checks['blank_result_uids'] = q1(con, "SELECT COUNT(*) FROM results WHERE result_uid IS NULL OR TRIM(result_uid)=''")
    checks['blank_source_result_ids'] = q1(con, "SELECT COUNT(*) FROM results WHERE source_result_id IS NULL OR TRIM(source_result_id)=''")
    checks['blank_names'] = q1(con, "SELECT COUNT(*) FROM results WHERE name IS NULL OR TRIM(name)=''")
    checks['finished_without_time'] = q1(con, "SELECT COUNT(*) FROM results WHERE status='FINISHED' AND (finish_seconds IS NULL OR finish_seconds<=0)")
    checks['nonfinished_with_time'] = q1(con, "SELECT COUNT(*) FROM results WHERE status<>'FINISHED' AND finish_seconds IS NOT NULL AND finish_seconds>0")
    checks['nonpositive_finish_times'] = q1(con, 'SELECT COUNT(*) FROM results WHERE finish_seconds IS NOT NULL AND finish_seconds<=0')
    checks['splits_without_parent'] = q1(con, 'SELECT COUNT(*) FROM splits s LEFT JOIN results r ON r.result_uid=s.result_uid WHERE r.result_uid IS NULL')
    checks['splits_outside_ultra'] = q1(con, "SELECT COUNT(*) FROM splits s JOIN results r ON r.result_uid=s.result_uid WHERE r.race_family<>'ultra60'")
    checks['splits_missing_elapsed'] = q1(con, 'SELECT COUNT(*) FROM splits WHERE elapsed_seconds IS NULL')
    checks['negative_split_seconds'] = q1(con, 'SELECT COUNT(*) FROM splits WHERE segment_seconds<0 OR elapsed_seconds<0')
    checks['derived_negative_seconds'] = q1(con, 'SELECT COUNT(*) FROM derived_metrics WHERE seconds<0')

    # Sequence/chronology check in Python for clarity and portability.
    chronology_errors = 0
    final_split_mismatch = 0
    final_split_checked = 0
    for result in con.execute("SELECT result_uid,finish_seconds FROM results WHERE race_family='ultra60'"):
        ss = con.execute('SELECT sequence_no,elapsed_seconds FROM splits WHERE result_uid=? ORDER BY sequence_no', (result['result_uid'],)).fetchall()
        prev = None
        for s in ss:
            e = s['elapsed_seconds']
            if e is not None and prev is not None and e < prev:
                chronology_errors += 1
            if e is not None:
                prev = e
        if ss and result['finish_seconds'] is not None and ss[-1]['elapsed_seconds'] is not None:
            final_split_checked += 1
            if abs(ss[-1]['elapsed_seconds'] - result['finish_seconds']) > 2:
                final_split_mismatch += 1
    checks['split_chronology_errors'] = chronology_errors
    checks['final_split_finish_mismatches_gt_2s'] = final_split_mismatch
    checks['final_split_finish_checked'] = final_split_checked

    # Expected year/family coverage.
    got = defaultdict(set)
    for r in import_rows:
        got[int(r['year'])].add(r['race_family'])
    coverage_missing = []
    coverage_extra = []
    for y in sorted(EXPECTED_YEARS | set(got)):
        exp = EXPECTED_FAMILIES_BY_YEAR.get(y, set())
        coverage_missing += [f'{y}:{f}' for f in sorted(exp - got.get(y, set()))]
        coverage_extra += [f'{y}:{f}' for f in sorted(got.get(y, set()) - exp)]
    checks['coverage_missing'] = coverage_missing
    checks['coverage_extra'] = coverage_extra

    # Unknown status distribution + safe aggregate keyword clues from embedded raw tables.
    unknown_by = rows_dict(con, '''
        SELECT year,race_family,entity_type,COUNT(*) AS unknown
        FROM results WHERE status='UNKNOWN'
        GROUP BY year,race_family,entity_type ORDER BY year,race_family
    ''')
    status_words = Counter()
    for row in con.execute("SELECT normalized_json FROM results WHERE status='UNKNOWN'"):
        status_words.update(extract_status_words(row['normalized_json']))

    # Field coverage is informative, not a hard failure.
    field_coverage = []
    for r in result_rows:
        n = r['results']
        field_coverage.append({
            'year': r['year'], 'race_family': r['race_family'], 'entity_type': r['entity_type'], 'results': n,
            'name_pct': percent(n-r['missing_name'], n), 'bib_pct': percent(n-r['missing_bib'], n),
            'gender_pct': percent(n-r['missing_gender'], n), 'age_pct': percent(n-r['missing_age'], n),
            'club_pct': percent(n-r['missing_club'], n), 'country_pct': percent(n-r['missing_country'], n),
        })

    # Service-window candidate diagnostics.
    service = rows_dict(con, '''
        SELECT r.year,COUNT(*) AS n,
               ROUND(AVG(d.seconds),1) AS avg_seconds,
               MIN(d.seconds) AS min_seconds,MAX(d.seconds) AS max_seconds
        FROM derived_metrics d JOIN results r ON r.result_uid=d.result_uid
        WHERE d.metric_key='bengtemolla_between_mats_seconds' AND d.seconds IS NOT NULL
        GROUP BY r.year ORDER BY r.year
    ''')

    summary_hash_ok = None
    gz_hash_ok = None
    if summary:
        if summary.get('database_sha256'):
            summary_hash_ok = sha256_file(db) == summary['database_sha256']
        if gz and summary.get('compressed_sha256'):
            gz_hash_ok = sha256_file(gz) == summary['compressed_sha256']

    hard_fail_keys = [
        'missing_required_tables','source_errors','import_count_mismatches','empty_imports','duplicate_source_result_keys',
        'blank_result_uids','blank_source_result_ids','finished_without_time','nonfinished_with_time','nonpositive_finish_times',
        'splits_without_parent','negative_split_seconds','derived_negative_seconds','split_chronology_errors','coverage_missing','coverage_extra'
    ]
    hard_failures = []
    for key in hard_fail_keys:
        value = checks[key]
        if value not in (0, [], 'ok'):
            hard_failures.append({'check': key, 'value': value})
    if integrity != 'ok':
        hard_failures.append({'check':'integrity_check','value':integrity})
    if summary_hash_ok is False:
        hard_failures.append({'check':'database_sha256','value':'mismatch'})
    if gz_hash_ok is False:
        hard_failures.append({'check':'compressed_sha256','value':'mismatch'})

    report = {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'archive': {
            'database_sha256_matches_summary': summary_hash_ok,
            'compressed_sha256_matches_summary': gz_hash_ok,
            'integrity_check': integrity,
            'imports': imports_count,
            'results': total_results,
            'splits': total_splits,
            'derived_metrics': total_metrics,
            'source_errors': total_source_errors,
        },
        'verdict': 'PASS' if not hard_failures else 'FAIL',
        'hard_failures': hard_failures,
        'checks': checks,
        'status_distribution': statuses,
        'unknown_status_by_year_family': unknown_by,
        'unknown_status_keyword_clues': dict(status_words.most_common()),
        'imports': import_rows,
        'result_counts': result_rows,
        'field_coverage': field_coverage,
        'checkpoint_coverage': checkpoint_rows,
        'bengtemolla_service_window_candidate': service,
        'notes': [
            'UNKNOWN is not treated as an audit failure because the current normalizer deliberately refuses to infer DNF/DNS/DSQ without explicit source evidence.',
            'Missing optional demographic/club fields are reported as coverage diagnostics, not failures.',
            'The audit never writes participant names to its report.'
        ]
    }
    con.close()
    return report


def write_reports(r: dict):
    OUT_JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    a = r['archive']; c = r['checks']
    lines = [
        '# Audit av fryst ÖST-resultatarkiv','',
        f"Status: **{r['verdict']}**",'',
        f"- Resultat: **{a['results']:,}**",
        f"- Mellantider: **{a['splits']:,}**",
        f"- Härledda checkpointmått: **{a['derived_metrics']:,}**",
        f"- År/distans-importer: **{a['imports']}**",
        f"- Källfel: **{a['source_errors']}**",
        f"- SQLite integrity_check: **{a['integrity_check']}**",
        f"- SQLite SHA-256 matchar frysningsrapport: **{a['database_sha256_matches_summary']}**",
        f"- Gzip SHA-256 matchar frysningsrapport: **{a['compressed_sha256_matches_summary']}**",'',
        '## Kritiska kontroller','',
        '| Kontroll | Värde |','|---|---:|',
    ]
    for key in ['import_count_mismatches','empty_imports','duplicate_source_result_keys','blank_result_uids','blank_source_result_ids','finished_without_time','nonfinished_with_time','nonpositive_finish_times','splits_without_parent','negative_split_seconds','derived_negative_seconds','split_chronology_errors','final_split_finish_mismatches_gt_2s']:
        lines.append(f"| `{key}` | {c[key]} |")
    lines += ['', '## Statusfördelning','', '| Status | Antal |','|---|---:|']
    for x in r['status_distribution']:
        lines.append(f"| {x['status']} | {x['n']} |")
    lines += ['', '## UNKNOWN per år/familj','', '| År | Familj | Typ | Antal |','|---:|---|---|---:|']
    for x in r['unknown_status_by_year_family']:
        lines.append(f"| {x['year']} | {x['race_family']} | {x['entity_type']} | {x['unknown']} |")
    lines += ['', '## Checkpointtäckning','', '| År | Familj | Källpunkt | Semantik | Passager | Saknar elapsed |','|---:|---|---|---|---:|---:|']
    for x in r['checkpoint_coverage']:
        lines.append(f"| {x['year']} | {x['race_family']} | {x['checkpoint_source_label']} | {x['checkpoint_semantic_key'] or '—'} | {x['passages']} | {x['missing_elapsed']} |")
    if r['bengtemolla_service_window_candidate']:
        lines += ['', '## Bengtemölla service-window candidate','', '| År | N | Snitt s | Min s | Max s |','|---:|---:|---:|---:|---:|']
        for x in r['bengtemolla_service_window_candidate']:
            lines.append(f"| {x['year']} | {x['n']} | {x['avg_seconds']} | {x['min_seconds']} | {x['max_seconds']} |")
    if r['unknown_status_keyword_clues']:
        lines += ['', '## Statusord funna i UNKNOWN-rådata','']
        for k,v in r['unknown_status_keyword_clues'].items(): lines.append(f'- `{k}`: {v}')
    lines += ['', '## Tolkning','',
              '- `PASS` betyder att arkivet är tekniskt helt, internt konsistent och täcker alla 34 förväntade år×distans-importer.',
              '- `UNKNOWN` är medvetet inte likställt med DNF/DNS. Det kräver uttrycklig källa eller separat validerad statuslogik.',
              '- Demografi/klubb/nationalitet kan saknas i Sportstiming och behandlas som datatäckning, inte importfel.','']
    OUT_MD.write_text('\n'.join(lines), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', default=str(DEFAULT_GZ.relative_to(ROOT)))
    ap.add_argument('--strict', action='store_true', help='Exit 1 if any hard audit failure exists')
    args = ap.parse_args()
    src = ROOT / args.archive
    if not src.exists(): raise SystemExit(f'Archive not found: {src}')
    summary = json.loads(SUMMARY.read_text(encoding='utf-8')) if SUMMARY.exists() else {}

    with tempfile.TemporaryDirectory(prefix='ost-audit-') as td:
        td = Path(td)
        if src.suffix == '.gz':
            db = td / 'archive.sqlite'
            with gzip.open(src, 'rb') as f, db.open('wb') as o: shutil.copyfileobj(f, o)
            gz = src
        else:
            db = src; gz = None
        r = audit(db, gz, summary)
    write_reports(r)
    print(json.dumps({'verdict':r['verdict'], **r['archive'], 'hard_failures':r['hard_failures']}, ensure_ascii=False, indent=2))
    if args.strict and r['verdict'] != 'PASS': raise SystemExit(1)

if __name__ == '__main__':
    main()
