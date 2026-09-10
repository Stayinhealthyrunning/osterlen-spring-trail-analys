#!/usr/bin/env python3
"""Fetch public Sportstiming app result data into a structured source snapshot.

Uses only public `/app/results` views that are directly reachable without bypassing
access controls. Individual races are stored from `/app/results/<id>` and relay
teams from `/app/results/team/<id>`. Source list rows, detail tables, URLs and
SHA-256 digests are retained so a later parser can be improved without re-fetching.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
import argparse, hashlib, html as html_lib, json, re, time, urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/source/sportstiming/class-catalog.json'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.stack=[]; self.current=None; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table': self.stack.append(self.current); self.current={'class':a.get('class'),'id':a.get('id'),'rows':[]}
        elif tag=='tr' and self.current is not None: self.row=[]
        elif tag in ('td','th') and self.current is not None and self.row is not None: self.cell={'tag':tag,'class':a.get('class'),'text':[],'links':[]}
        elif tag=='a' and self.cell is not None and a.get('href'): self.cell['links'].append(a['href'])
    def handle_data(self,data):
        if self.cell is not None:self.cell['text'].append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.cell['text']=' '.join(html_lib.unescape(''.join(self.cell['text'])).split()); self.row.append(self.cell); self.cell=None
        elif tag=='tr' and self.row is not None and self.current is not None:
            if any(c.get('text') or c.get('links') for c in self.row): self.current['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.current is not None:
            done=self.current; self.current=self.stack.pop() if self.stack else None; self.tables.append(done)

def fetch(url,timeout=25,retries=4):
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read(2_500_000)
                return raw.decode('utf-8','replace'),hashlib.sha256(raw).hexdigest(),r.geturl()
        except Exception as exc:
            last=exc; time.sleep(0.75*(attempt+1))
    raise last

def catalog_item(year,family):
    cat=json.loads(CAT.read_text(encoding='utf-8'))
    for ed in cat['editions']:
        if ed['year']==year:
            for c in ed['classes']:
                if c.get('race_family')==family:return ed['event_id'],c
    raise SystemExit(f'No Sportstiming class found for {year} {family}')

def clean_cell(c):
    return {'tag':c.get('tag'),'class':c.get('class'),'text':c.get('text',''),'links':c.get('links',[])}

def discover_page_entries(doc,event,entity_type):
    p=TableParser(); p.feed(doc)
    if entity_type=='team': pat=re.compile(rf'/event/{event}/app/results/team/(\d+)')
    else: pat=re.compile(rf'/event/{event}/app/results/(\d+)$')
    entries=[]
    for table in p.tables:
        header=[]
        for row in table.get('rows',[]):
            if row and all(c.get('tag')=='th' for c in row):
                header=[c.get('text','') for c in row]
                continue
            rid=None
            for cell in row:
                for href in cell.get('links',[]):
                    m=pat.search(href)
                    if m: rid=m.group(1); break
                if rid: break
            if rid:
                entries.append({'sportstiming_result_id':rid,'entity_type':entity_type,'list_headers':header,'list_row':[clean_cell(c) for c in row]})
    # Fallback if table markup changes but links remain.
    if not entries:
        regex=rf'/event/{event}/app/results/team/(\d+)' if entity_type=='team' else rf'/event/{event}/app/results/(\d+)'
        for rid in dict.fromkeys(re.findall(regex,doc)):
            entries.append({'sportstiming_result_id':rid,'entity_type':entity_type,'list_headers':[],'list_row':[]})
    return entries

def crawl_entries(event,round_id,entity_type,max_pages=300):
    all_entries=[]; seen=set(); pages=[]
    for page in range(1,max_pages+1):
        q=urllib.parse.urlencode({'round':round_id,'page':page})
        url=f'https://www.sportstiming.dk/event/{event}/app/results?{q}'
        doc,digest,final=fetch(url)
        entries=discover_page_entries(doc,event,entity_type)
        new=[]
        for e in entries:
            rid=e['sportstiming_result_id']
            if rid not in seen: seen.add(rid); new.append(e); all_entries.append(e)
        pages.append({'page':page,'url':url,'final_url':final,'sha256':digest,'result_links':len(entries),'new_result_ids':len(new)})
        if not new: break
        if len(entries)<50: break
    return all_entries,pages

def parse_detail(event,entry):
    rid=entry['sportstiming_result_id']; entity_type=entry['entity_type']
    suffix=f'team/{rid}' if entity_type=='team' else rid
    url=f'https://www.sportstiming.dk/event/{event}/app/results/{suffix}'
    doc,digest,final=fetch(url)
    p=TableParser(); p.feed(doc)
    tables=[]
    for t in p.tables:
        rows=[]
        for row in t['rows']:
            clean=[clean_cell(c) for c in row]
            if any(c['text'] or c['links'] for c in clean): rows.append(clean)
        if rows: tables.append({'class':t.get('class'),'id':t.get('id'),'rows':rows})
    return {**entry,'source_url':url,'final_url':final,'source_sha256':digest,'tables':tables}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--year',type=int,required=True); ap.add_argument('--family',required=True)
    ap.add_argument('--limit',type=int,default=0,help='0 = all discovered results'); ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--output'); args=ap.parse_args()
    event,cls=catalog_item(args.year,args.family); round_id=cls['sportstiming_distance_id']
    entity_type='team' if args.family=='duo60' else 'athlete'
    entries,pages=crawl_entries(event,round_id,entity_type)
    if args.limit>0: entries=entries[:args.limit]
    rows=[]
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:
        fut={pool.submit(parse_detail,event,e):e['sportstiming_result_id'] for e in entries}
        for f in as_completed(fut):
            try: rows.append(f.result())
            except Exception as exc: rows.append({'sportstiming_result_id':fut[f],'entity_type':entity_type,'error':repr(exc)})
    order={e['sportstiming_result_id']:i for i,e in enumerate(entries)}; rows.sort(key=lambda x:order.get(x['sportstiming_result_id'],999999))
    payload={'schema_version':2,'year':args.year,'race_family':args.family,'entity_type':entity_type,'event_id':event,'sportstiming_distance_id':round_id,
             'source_label':cls['source_label'],'discovered_result_ids':len(entries),'list_pages':pages,'results':rows,
             'provenance_note':'Public Sportstiming /app views; list rows and structured detail tables preserved without inventing missing fields.'}
    path=ROOT/(args.output or f'data/source/sportstiming/snapshots/{args.year}-{args.family}.json')
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    errors=sum(1 for x in rows if x.get('error'))
    print(f'{args.year} {args.family}: discovered/stored {len(entries)} {entity_type} result ids, detail errors={errors}, output={path.relative_to(ROOT)}')
    raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
