#!/usr/bin/env python3
"""Profile recoverable identity/result fields from the immutable frozen archive.

No network access is used. The report contains only aggregate counts, source table
headers/labels and anonymized value-shapes; no participant names are emitted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import gzip, json, re, shutil, sqlite3, tempfile, unicodedata

ROOT=Path(__file__).resolve().parents[1]
GZ=ROOT/'data/archive/ost-results-2018-2026.sqlite.gz'
OUT=ROOT/'reports/identity-field-profile.json'
OUTMD=ROOT/'reports/identity-field-profile.md'


def mask_shape(value):
    s=unicodedata.normalize('NFKC',str(value or '').strip())
    s=re.sub(r'\d+','<N>',s)
    s=re.sub(r'[^\W\d_]+','<A>',s,flags=re.UNICODE)
    s=re.sub(r'\s+',' ',s)
    return s[:120]


def norm(s):
    return re.sub(r'\s+',' ',str(s or '').strip()).casefold()


def main():
    with tempfile.TemporaryDirectory(prefix='ost-ident-') as td:
        db=Path(td)/'a.sqlite'
        with gzip.open(GZ,'rb') as f,db.open('wb') as o:shutil.copyfileobj(f,o)
        con=sqlite3.connect(db);con.row_factory=sqlite3.Row

        list_headers=defaultdict(Counter)
        list_nonempty=defaultdict(Counter)
        detail_labels=Counter()
        identity_shapes=defaultdict(Counter)
        normalized_coverage=defaultdict(Counter)
        totals=Counter()

        for imp in con.execute('SELECT year,race_family,snapshot_json FROM imports'):
            key=f"{imp['year']}:{imp['race_family']}"
            snap=json.loads(imp['snapshot_json'])
            for rec in snap.get('results',[]):
                totals['source_records']+=1
                headers=tuple((h or '').strip() for h in (rec.get('list_headers') or []))
                if headers:list_headers[key][headers]+=1
                row=rec.get('list_row') or []
                for i,h in enumerate(headers):
                    if i<len(row) and (row[i].get('text') or '').strip():
                        list_nonempty[key][h]+=1

        for r in con.execute('SELECT year,race_family,normalized_json FROM results'):
            key=f"{r['year']}:{r['race_family']}"
            obj=json.loads(r['normalized_json']);totals['results']+=1
            for field in ('name','club','country','gender','age','age_category','overall_place','class_place','gender_place','finish_seconds'):
                v=obj.get(field)
                if v is not None and (not isinstance(v,str) or v.strip()):normalized_coverage[key][field]+=1
            tables=obj.get('raw_tables') or obj.get('raw_record',{}).get('tables',[])
            for t in tables:
                for row in t.get('rows',[]):
                    vals=[(c.get('text') or '').strip() for c in row]
                    if len(vals)>=2 and vals[0]:detail_labels[vals[0]]+=1
                    if len(vals)>=2 and not vals[0] and vals[1]:identity_shapes[key][mask_shape(vals[1])]+=1
        con.close()

    safe_labels={k:v for k,v in detail_labels.most_common() if v>=20}
    report={
        'schema_version':1,
        'source':'data/archive/ost-results-2018-2026.sqlite.gz',
        'privacy_rule':'Aggregate structure only; participant/team names are not emitted.',
        'totals':dict(totals),
        'list_header_sets':{
            k:[{'headers':list(h),'records':n} for h,n in c.most_common()] for k,c in sorted(list_headers.items())
        },
        'list_nonempty_by_header':{k:dict(c) for k,c in sorted(list_nonempty.items())},
        'normalized_field_counts':{k:dict(c) for k,c in sorted(normalized_coverage.items())},
        'identity_value_shapes':{k:dict(c.most_common(20)) for k,c in sorted(identity_shapes.items())},
        'frequent_detail_first_cell_labels':safe_labels,
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    lines=['# Fältprofil från fryst Sportstiming-arkiv','',report['privacy_rule'],'','## Listkolumner','']
    for k,sets in report['list_header_sets'].items():
        lines.append(f"- **{k}:** "+' / '.join(', '.join(x['headers'])+f" ({x['records']})" for x in sets[:3]))
    lines += ['','## Redan normaliserade fält','', '| Grupp | Namn | Klubb | Land | Kön | Ålder | Åldersklass | Placering |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for k,c in sorted(normalized_coverage.items()):
        lines.append(f"| {k} | {c['name']} | {c['club']} | {c['country']} | {c['gender']} | {c['age']} | {c['age_category']} | {c['overall_place']} |")
    lines += ['','## Anonymiserade identitetsvärdeformer','']
    for k,c in sorted(identity_shapes.items()):
        lines.append(f"- **{k}:** "+', '.join(f'`{shape}`={n}' for shape,n in c.most_common(8)))
    OUTMD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'groups':len(normalized_coverage),'source_records':totals['source_records'],'results':totals['results']},indent=2))

if __name__=='__main__':main()
