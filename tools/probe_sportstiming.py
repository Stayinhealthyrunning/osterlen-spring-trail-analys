#!/usr/bin/env python3
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json, re, urllib.request, urllib.error

ROOT=Path(__file__).resolve().parents[1]
EVENTS=json.loads((ROOT/'data/source/sportstiming/events.json').read_text(encoding='utf-8'))['events']
OUT_JSON=ROOT/'reports/sportstiming-probe.json'
OUT_MD=ROOT/'reports/sportstiming-probe.md'
PATHS=['results','participants','app/results','app/participants','embed/results','embed/participants','embedtabs/results','embedtabs/participants']
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
    try:
        with urllib.request.urlopen(req,timeout=7) as r:
            body=r.read(500000).decode('utf-8','replace')
            return r.status, r.geturl(), body
    except urllib.error.HTTPError as e:
        body=e.read(150000).decode('utf-8','replace')
        return e.code, e.geturl(), body
    except Exception as e:
        return None,url,repr(e)

def summarize(body):
    low=body.lower(); title=None
    m=re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
    if m: title=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',m.group(1))).strip()
    scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)',body,re.I)
    links=re.findall(r'href=["\']([^"\']+)',body,re.I)
    return {
      'title':title,
      'human_check':('verify you\'re human' in low or 'confirm you\'re human' in low or 'just a quick check' in low),
      'contains_results_words': any(x in low for x in ['resultat','resultater','results']),
      'contains_participant_words': any(x in low for x in ['deltagare','deltager','participants']),
      'script_srcs':scripts[:30],
      'candidate_api_links':[x for x in links if any(t in x.lower() for t in ['api','json','csv','download'])][:30],
      'body_bytes_sampled':len(body.encode('utf-8','replace'))
    }

def probe(item):
    year,event_id,base,path=item
    url=f'{base}/{path}'
    status,final,body=fetch(url)
    return {'year':year,'event_id':event_id,'path':path,'url':url,'http_status':status,'final_url':final,**summarize(body)}

def main():
    work=[]
    for ev in EVENTS:
        base=ev['url'].rsplit('/results',1)[0]
        for p in PATHS: work.append((ev['year'],ev['event_id'],base,p))
    rows=[]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures=[pool.submit(probe,item) for item in work]
        for future in as_completed(futures): rows.append(future.result())
    rows.sort(key=lambda r:(r['year'],PATHS.index(r['path'])))
    OUT_JSON.write_text(json.dumps({'generated_by':'tools/probe_sportstiming.py','rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming public endpoint probe','','This report only tests public event views. It does not attempt to bypass authentication or human-verification controls.','','| Year | Path | HTTP | Human check | Title |','|---:|---|---:|:---:|---|']
    for r in rows:
        lines.append(f"| {r['year']} | `{r['path']}` | {r['http_status'] if r['http_status'] is not None else 'ERR'} | {'yes' if r['human_check'] else 'no'} | {r['title'] or ''} |")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
