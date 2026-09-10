#!/usr/bin/env python3
"""Fetch public Sportstiming app result data into a structured source snapshot.

This uses only public `/app/results` views that are directly reachable without
bypassing access controls. It stores semantic table structure rather than a raw
HTML mirror, and keeps source URLs + SHA-256 for provenance.
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
        super().__init__();self.tables=[];self.stack=[];self.current=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':self.stack.append(self.current);self.current={'class':a.get('class'),'id':a.get('id'),'rows':[]}
        elif tag=='tr' and self.current is not None:self.row=[]
        elif tag in ('td','th') and self.current is not None and self.row is not None:self.cell={'tag':tag,'class':a.get('class'),'text':[]}
    def handle_data(self,data):
        if self.cell is not None:self.cell['text'].append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.cell['text']=' '.join(html_lib.unescape(''.join(self.cell['text'])).split());self.row.append(self.cell);self.cell=None
        elif tag=='tr' and self.row is not None and self.current is not None:
            if any(c.get('text') for c in self.row):self.current['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.current is not None:
            done=self.current;self.current=self.stack.pop() if self.stack else None;self.tables.append(done)

def fetch(url,timeout=20,retries=3):
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read(1800000)
                return raw.decode('utf-8','replace'),hashlib.sha256(raw).hexdigest(),r.geturl()
        except Exception as exc:
            last=exc;time.sleep(0.5*(attempt+1))
    raise last

def catalog_item(year,family):
    cat=json.loads(CAT.read_text(encoding='utf-8'))
    for ed in cat['editions']:
        if ed['year']==year:
            for c in ed['classes']:
                if c.get('race_family')==family:return ed['event_id'],c
    raise SystemExit(f'No Sportstiming class found for {year} {family}')

def result_ids(doc,event):
    return list(dict.fromkeys(re.findall(rf'/event/{event}/app/results/(\d+)',doc)))

def crawl_ids(event,round_id,max_pages=200):
    all_ids=[];pages=[]
    for page in range(1,max_pages+1):
        q=urllib.parse.urlencode({'round':round_id,'page':page})
        url=f'https://www.sportstiming.dk/event/{event}/app/results?{q}'
        doc,digest,final=fetch(url)
        ids=result_ids(doc,event)
        new=[x for x in ids if x not in all_ids]
        pages.append({'page':page,'url':url,'final_url':final,'sha256':digest,'result_links':len(ids),'new_result_ids':len(new)})
        if not new:break
        all_ids.extend(new)
        # A page with fewer than the usual 50 visible rows is normally final.
        if len(ids)<50:break
    return all_ids,pages

def parse_detail(event,rid):
    url=f'https://www.sportstiming.dk/event/{event}/app/results/{rid}'
    doc,digest,final=fetch(url)
    p=TableParser();p.feed(doc)
    tables=[]
    for t in p.tables:
        rows=[]
        for row in t['rows']:
            clean=[{'tag':c['tag'],'class':c.get('class'),'text':c.get('text','')} for c in row]
            if any(c['text'] for c in clean):rows.append(clean)
        if rows:tables.append({'class':t.get('class'),'id':t.get('id'),'rows':rows})
    return {'sportstiming_result_id':rid,'source_url':url,'final_url':final,'source_sha256':digest,'tables':tables}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);ap.add_argument('--family',required=True)
    ap.add_argument('--limit',type=int,default=0,help='0 = all discovered results');ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--output');args=ap.parse_args()
    event,cls=catalog_item(args.year,args.family);round_id=cls['sportstiming_distance_id']
    ids,pages=crawl_ids(event,round_id)
    if args.limit>0:ids=ids[:args.limit]
    rows=[]
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:
        fut={pool.submit(parse_detail,event,rid):rid for rid in ids}
        for f in as_completed(fut):
            try:rows.append(f.result())
            except Exception as exc:rows.append({'sportstiming_result_id':fut[f],'error':repr(exc)})
    order={rid:i for i,rid in enumerate(ids)};rows.sort(key=lambda x:order.get(x['sportstiming_result_id'],999999))
    payload={'schema_version':1,'year':args.year,'race_family':args.family,'event_id':event,'sportstiming_distance_id':round_id,
             'source_label':cls['source_label'],'discovered_result_ids':len(ids),'list_pages':pages,'results':rows,
             'provenance_note':'Public Sportstiming /app views; structured source tables preserved without inventing missing fields.'}
    if args.output:path=ROOT/args.output
    else:path=ROOT/f'data/source/sportstiming/snapshots/{args.year}-{args.family}.json'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    errors=sum(1 for x in rows if x.get('error'))
    print(f'{args.year} {args.family}: discovered/stored {len(ids)} result ids, detail errors={errors}, output={path.relative_to(ROOT)}')
    raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
