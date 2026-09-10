#!/usr/bin/env python3
"""Turn the conservative Sportstiming discovery report into a compact fact sheet.

The output remains evidence, not a normalized race catalog: it quotes only short labels,
distances and start times found on public event-root pages and keeps the source year/event id.
"""
from pathlib import Path
import json, re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/sportstiming-event-discovery.json'
OUT_JSON=ROOT/'reports/sportstiming-event-facts.json'
OUT_MD=ROOT/'reports/sportstiming-event-facts.md'

DIST_RE=re.compile(r'(?<!\d)(?:60|22|21|14|13|5)\s*km\+?',re.I)
TIME_RE=re.compile(r'(?:Startar\s+kl\.?|start(?:tid)?\s*[:]?)[\s]*(\d{1,2}[.:]\d{2})',re.I)
DATE_RE=re.compile(r'(?:den\s+)?(\d{1,2})\s+(april|apr)\s+(20\d{2})',re.I)

# Race-label words deliberately narrow to avoid collecting pricing/general event prose.
RACE_WORDS=('ultra','verkeån','fogarolli','naturloppet','ekopark','duo','craft','coros','trail')

def clean(s): return re.sub(r'\s+',' ',s).strip()

def main():
    data=json.loads(SRC.read_text(encoding='utf-8'))
    events=[]
    lines=['# Sportstiming event facts','',
           'Compact extraction from the public event-root pages. These are source facts/candidates, not yet normalized race records.','']
    for event in data['events']:
        root=next((p for p in event['pages'] if p['url'].rstrip('/').endswith(f"/event/{event['event_id']}")),event['pages'][0])
        snippets=[]
        for raw in root.get('metadata_snippets',[]):
            s=clean(raw)
            low=s.lower()
            if (DIST_RE.search(s) or TIME_RE.search(s)) and any(w in low for w in RACE_WORDS):
                if s not in snippets: snippets.append(s)
        distances=sorted(set(m.group(0).replace(' ','').lower() for s in snippets for m in DIST_RE.finditer(s)))
        times=sorted(set(m.group(1).replace('.',':') for s in snippets for m in TIME_RE.finditer(s)))
        dates=sorted(set(f"{m.group(3)}-{4:02d}-{int(m.group(1)):02d}" for s in root.get('metadata_snippets',[]) for m in DATE_RE.finditer(s)))
        item={
          'year':event['year'],'event_id':event['event_id'],'event_title':root.get('title'),
          'root_status':root.get('status'),'root_challenge':root.get('challenge'),
          'participants_challenge':event['pages'][1].get('challenge') if len(event['pages'])>1 else None,
          'results_challenge':event['pages'][2].get('challenge') if len(event['pages'])>2 else None,
          'distance_tokens':distances,'start_time_tokens':times,'date_tokens':dates,
          'evidence_snippets':snippets[:40]
        }
        events.append(item)
        lines += [f"## {item['year']} — event {item['event_id']}",'',
                  f"Event root: {item['root_status']}; participant page challenged: {item['participants_challenge']}; result page challenged: {item['results_challenge']}.",'',
                  f"Distances found: {', '.join(distances) if distances else '—'}  ",
                  f"Start times found: {', '.join(times) if times else '—'}  ",
                  f"Dates found: {', '.join(dates) if dates else '—'}",'']
        for s in snippets[:20]: lines.append(f'- {s}')
        lines.append('')
    OUT_JSON.write_text(json.dumps({'events':events},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    OUT_MD.write_text('\n'.join(lines),encoding='utf-8')
    print(f'events={len(events)}')

if __name__=='__main__': main()
