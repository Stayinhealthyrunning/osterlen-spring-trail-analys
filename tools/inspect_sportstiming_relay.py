#!/usr/bin/env python3
"""Inspect public Sportstiming Duo/relay result-list structure without storing runner names.

The individual importer discovers `/app/results/<id>` links. Duo lists currently do not,
so this diagnostic records table schemas, link patterns and anonymized row shapes for the
relay classes in scope. It is intended to support a dedicated relay adapter.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone
import hashlib, html as html_lib, json, re, urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[1]
CAT=json.loads((ROOT/'data/source/sportstiming/class-catalog.json').read_text(encoding='utf-8'))
OUT=ROOT/'reports/sportstiming-relay-structure.json'
OUT_MD=ROOT/'reports/sportstiming-relay-structure.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.cur=None; self.stack=[]; self.row=None; self.cell=None; self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table': self.stack.append(self.cur); self.cur={'class':a.get('class'),'id':a.get('id'),'rows':[]}
        elif tag=='tr' and self.cur is not None: self.row=[]
        elif tag in ('td','th') and self.row is not None: self.cell={'tag':tag,'class':a.get('class'),'text':[],'links':[]}
        elif tag=='a' and a.get('href'):
            rec={'href':a['href'],'class':a.get('class'),'id':a.get('id')}
            self.links.append(rec)
            if self.cell is not None: self.cell['links'].append(rec)
    def handle_data(self,d):
        if self.cell is not None: self.cell['text'].append(d)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.cell['text']=' '.join(html_lib.unescape(''.join(self.cell['text'])).split())
            self.row.append(self.cell); self.cell=None
        elif tag=='tr' and self.row is not None and self.cur is not None:
            if any(c.get('text') or c.get('links') for c in self.row): self.cur['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.cur is not None:
            done=self.cur; self.cur=self.stack.pop() if self.stack else None; self.tables.append(done)

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(1_800_000); return raw.decode('utf-8','replace'),r.geturl(),hashlib.sha256(raw).hexdigest()

def token_shape(text):
    text=text or ''
    # Preserve formatting clues but never names/content. Letters become A/a, digits 9.
    out=[]
    for ch in text[:180]:
        if ch.isupper(): out.append('A')
        elif ch.islower(): out.append('a')
        elif ch.isdigit(): out.append('9')
        elif ch.isspace(): out.append(' ')
        else: out.append(ch)
    return ''.join(out)

def link_pattern(href):
    href=href or ''
    s=re.sub(r'\d+','{id}',href)
    return s[:300]

def duo_classes():
    out=[]
    for ed in CAT.get('editions',[]):
        c=next((x for x in ed.get('classes',[]) if x.get('race_family')=='duo60'),None)
        if c: out.append({'year':int(ed['year']),'event_id':int(ed['event_id']),'distance_id':str(c['sportstiming_distance_id']),'source_label':c.get('source_label')})
    return out

def inspect(item):
    q=urllib.parse.urlencode({'round':item['distance_id'],'page':1})
    url=f"https://www.sportstiming.dk/event/{item['event_id']}/app/results?{q}"
    doc,final,digest=fetch(url); p=P(); p.feed(doc)
    tables=[]
    for t in p.tables:
        rr=[]
        for row in t.get('rows',[])[:8]:
            rr.append([{
              'tag':c.get('tag'),'class':c.get('class'),'text_shape':token_shape(c.get('text')),
              'text_length':len(c.get('text') or ''),
              'link_patterns':sorted({link_pattern(x.get('href')) for x in c.get('links',[])})
            } for c in row])
        if rr: tables.append({'class':t.get('class'),'id':t.get('id'),'row_count_seen':len(t.get('rows',[])),'sample_row_shapes':rr})
    patterns=sorted({link_pattern(x.get('href')) for x in p.links if any(k in (x.get('href') or '').lower() for k in ('result','team','relay','participant','contest','runner'))})
    # Only tiny code-context fragments around relay/team/result tokens; no names.
    contexts=[]
    for token in ('relay','team','resultid','participantid','roundid'):
        for m in list(re.finditer(token,doc,re.I))[:5]:
            s=' '.join(doc[max(0,m.start()-160):min(len(doc),m.end()+220)].split())
            # Remove visible tag text aggressively while retaining attributes/JS shape.
            s=re.sub(r'>[^<>]{2,120}<','><',s)
            contexts.append({'token':token,'snippet':s[:500]})
    return {**item,'url':url,'final_url':final,'source_sha256':digest,'html_bytes':len(doc.encode('utf-8')),'tables':tables,'candidate_link_patterns':patterns[:100],'code_contexts':contexts[:40]}

def main():
    rows=[]; errors=[]
    for item in duo_classes():
        try:
            r=inspect(item); rows.append(r); print(item['year'],'tables',len(r['tables']),'patterns',len(r['candidate_link_patterns']))
        except Exception as exc:
            errors.append({**item,'error':f'{type(exc).__name__}: {exc}'})
    report={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'privacy':'Runner/team names are not stored; visible text is reduced to token shapes and lengths.','editions':rows,'errors':errors}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming Duo relay structure','',
           'Strukturdiagnostik för att bygga en separat relay-adapter. Löpar-/lagnamn sparas inte i denna rapport.','',
           '| År | Round | tabeller | kandidatlänkmönster | HTML kB |',
           '|---:|---:|---:|---:|---:|']
    for r in rows: lines.append(f"| {r['year']} | {r['distance_id']} | {len(r['tables'])} | {len(r['candidate_link_patterns'])} | {r['html_bytes']/1024:.1f} |")
    if errors: lines += ['','## Fel','']+[f"- {e['year']}: {e['error']}" for e in errors]
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
