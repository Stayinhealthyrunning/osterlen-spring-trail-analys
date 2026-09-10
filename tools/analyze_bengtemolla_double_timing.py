#!/usr/bin/env python3
"""Validate the 2022/2023 Sportstiming 32 km -> Bengtemölla double timing.

The goal is to determine whether `32 km` behaves as a pre-warning mat and
`Bengtemölla` as the canonical checkpoint. Only aggregate diagnostics are
written; runner identities are not mirrored in the report.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json, re, statistics, time, urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / 'reports' / 'bengtemolla-double-timing.json'
OUT_MD = ROOT / 'reports' / 'bengtemolla-double-timing.md'
UA = 'Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

CASES = [
    {'year': 2022, 'event_id': 9587, 'round_id': 46204},
    {'year': 2023, 'event_id': 11274, 'round_id': 58343},
]

class SplitParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_split=False; self.in_row=False; self.in_cell=False
        self.depth=0; self.row=[]; self.cell=[]; self.rows=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='table' and 'splits-table' in (d.get('class') or ''):
            self.in_split=True; self.depth=1; return
        if self.in_split:
            if tag=='table': self.depth += 1
            if tag=='tr': self.in_row=True; self.row=[]
            elif tag in ('td','th') and self.in_row: self.in_cell=True; self.cell=[]
    def handle_data(self, data):
        if self.in_cell: self.cell.append(data)
    def handle_endtag(self, tag):
        if not self.in_split: return
        if tag in ('td','th') and self.in_cell:
            self.row.append(' '.join(''.join(self.cell).split())); self.in_cell=False
        elif tag=='tr' and self.in_row:
            if any(self.row): self.rows.append(self.row)
            self.in_row=False
        elif tag=='table':
            self.depth -= 1
            if self.depth<=0: self.in_split=False

def fetch(url, retries=3):
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.8'})
            with urllib.request.urlopen(req,timeout=30) as r: return r.read().decode('utf-8','replace')
        except Exception as exc:
            last=exc; time.sleep(0.6*(attempt+1))
    raise last

def parse_seconds(v):
    m=re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})',(v or '').strip())
    if not m: return None
    return int(m.group(1) or 0)*3600+int(m.group(2))*60+int(m.group(3))

def result_ids(event_id, round_id, max_results=60):
    ids=[]
    for page in range(1,4):
        doc=fetch(f'https://www.sportstiming.dk/event/{event_id}/app/results?round={round_id}&page={page}')
        page_ids=list(dict.fromkeys(re.findall(rf'/event/{event_id}/app/results/(\d+)',doc)))
        for rid in page_ids:
            if rid not in ids: ids.append(rid)
            if len(ids)>=max_results: return ids
        if len(page_ids)<50: break
    return ids

def split_pair(event_id, rid):
    doc=fetch(f'https://www.sportstiming.dk/event/{event_id}/app/results/{rid}')
    p=SplitParser(); p.feed(doc)
    by={}
    for r in p.rows:
        if len(r)>=9 and r[0] in {'32 km','Bengtemölla'}:
            by[r[0]]=r
    if not {'32 km','Bengtemölla'} <= set(by): return None
    a,b=by['32 km'],by['Bengtemölla']
    ea=parse_seconds(a[6]); eb=parse_seconds(b[6]); seg=parse_seconds(b[3])
    if ea is None or eb is None: return None
    return {
        'delta_seconds': eb-ea,
        'bengtemolla_segment_seconds': seg,
        'bengtemolla_segment_distance_source': b[1],
        'rank_unchanged': a[7].strip()==b[7].strip(),
    }

def percentile(values, q):
    if not values: return None
    s=sorted(values); i=(len(s)-1)*q; lo=int(i); hi=min(lo+1,len(s)-1); f=i-lo
    return s[lo]*(1-f)+s[hi]*f

def main():
    out=[]
    for case in CASES:
        ids=result_ids(case['event_id'],case['round_id'])
        pairs=[]; errors=0
        for rid in ids:
            try:
                item=split_pair(case['event_id'],rid)
                if item: pairs.append(item)
            except Exception:
                errors += 1
        deltas=[x['delta_seconds'] for x in pairs if x['delta_seconds'] is not None]
        segs=[x['bengtemolla_segment_seconds'] for x in pairs if x['bengtemolla_segment_seconds'] is not None]
        distances=sorted(set(x['bengtemolla_segment_distance_source'] for x in pairs))
        row={**case,'sampled_result_ids':len(ids),'valid_pairs':len(pairs),'fetch_or_parse_errors':errors,
             'segment_distance_source_values':distances,
             'delta_seconds':{
                 'min':min(deltas) if deltas else None,
                 'median':statistics.median(deltas) if deltas else None,
                 'p90':round(percentile(deltas,.9),1) if deltas else None,
                 'max':max(deltas) if deltas else None,
             },
             'segment_seconds_median':statistics.median(segs) if segs else None,
             'rank_unchanged_fraction':round(sum(1 for x in pairs if x['rank_unchanged'])/len(pairs),3) if pairs else None,
        }
        # Strong evidence only if the source itself reports ~0.1 km and the observed passage is normally very short.
        dist_text=' '.join(distances).lower().replace(',','.')
        short_distance=('100 meter' in dist_text or '0.1 km' in dist_text)
        row['interpretation']='prewarning_then_bengtemolla_supported' if deltas and short_distance and statistics.median(deltas)<=120 else 'needs_review'
        out.append(row)
        print(case['year'],row)
    payload={'schema_version':1,'question':'Is the 32 km timing point immediately before Bengtemölla, so Bengtemölla should be the canonical checkpoint?',
             'method':'Aggregate public Sportstiming split-table comparison; no runner identities stored.','years':out,
             'canonicalization_recommendation':'For 2022 and 2023, retain both raw source rows for provenance, but use the Bengtemölla elapsed time as the canonical Bengtemölla checkpoint if both years are classified prewarning_then_bengtemolla_supported.'}
    OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Bengtemölla double-timing diagnostic','',payload['method'],'',
           '| Year | Valid pairs | Source segment distance | Median delta | P90 delta | Rank unchanged | Interpretation |','|---:|---:|---|---:|---:|---:|---|']
    for r in out:
        d=r['delta_seconds']; lines.append(f"| {r['year']} | {r['valid_pairs']} | {', '.join(r['segment_distance_source_values'])} | {d['median']} s | {d['p90']} s | {r['rank_unchanged_fraction']} | `{r['interpretation']}` |")
    lines += ['',payload['canonicalization_recommendation'],'']
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__': main()
