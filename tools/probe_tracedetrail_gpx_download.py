#!/usr/bin/env python3
"""Discover Trace de Trail's normal public GPX download mechanism.

Fetches one public trace page and same-origin JavaScript assets, retaining only
request-related snippets needed to reproduce the public route-only download.
"""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json, re, time, urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT_JSON=ROOT/'reports/tracedetrail-gpx-download-probe.json'
OUT_MD=ROOT/'reports/tracedetrail-gpx-download-probe.md'
TRACE_ID=272846
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class P(HTMLParser):
    def __init__(self): super().__init__(); self.scripts=[]; self.buttons=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='script' and d.get('src'): self.scripts.append(d['src'])
        if tag in ('button','a'):
            text={k:d.get(k) for k in ('id','class','href','onclick','data-id','data-trace','data-traceid','type','name','value') if d.get(k) is not None}
            if any('gpx' in str(v).lower() for v in text.values()): self.buttons.append({'tag':tag,**text})
        if tag=='a' and d.get('href'): self.links.append(d['href'])

def fetch(url,max_bytes=8_000_000):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/javascript,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=40) as r:
        b=r.read(max_bytes); return b.decode('utf-8','replace'),r.geturl(),r.headers.get('Content-Type','')

def snippets(text,token,span=500,limit=20):
    out=[]
    for m in re.finditer(re.escape(token),text,re.I):
        s=max(0,m.start()-span); e=min(len(text),m.end()+span)
        x=' '.join(text[s:e].split())
        if x not in out: out.append(x)
        if len(out)>=limit: break
    return out

def main():
    page=f'https://tracedetrail.fr/fr/trace/{TRACE_ID}'
    html,final,ctype=fetch(page)
    p=P();p.feed(html)
    scripts=[]
    for src in p.scripts:
        u=urljoin(final,src)
        if urlparse(u).netloc not in {'tracedetrail.fr','www.tracedetrail.fr'}: continue
        try:
            body,fu,ct=fetch(u,5_000_000)
        except Exception as exc:
            scripts.append({'url':u,'error':f'{type(exc).__name__}: {exc}'}); continue
        toks={}
        for token in ('downloadGpx','submitDownload:function','download:function(param)','getFile/','checkDownload','gpx'):
            span=4000 if token in ('submitDownload:function','download:function(param)','checkDownload') else 700
            ss=snippets(body,token,span=span,limit=8)
            if ss:toks[token]=ss
        if toks: scripts.append({'url':u,'final_url':fu,'content_type':ct,'bytes':len(body.encode('utf-8')),'snippets':toks})
        time.sleep(.05)
    page_tokens={}
    for token in ('downloadGpx','traceDownloads','platform','base_url','carto.initialize','traceID'):
        ss=snippets(html,token,span=1200,limit=12)
        if ss: page_tokens[token]=ss
    payload={'schema_version':2,'trace_id':TRACE_ID,'page_url':page,'final_url':final,'page_bytes':len(html.encode('utf-8')),
             'gpx_related_elements':p.buttons,'page_snippets':page_tokens,'script_hits':scripts,
             'note':'Request-flow snippets only; no complete third-party JS or GPX body mirrored.'}
    OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Trace de Trail GPX download probe','',f'- Trace: {TRACE_ID}',f'- GPX-related page elements: {len(p.buttons)}',f'- Script assets with request-flow hits: {len(scripts)}','']
    for b in p.buttons: lines.append(f"- element: `{json.dumps(b,ensure_ascii=False)}`")
    lines+=['','## Script hits','']
    for s in scripts:
        lines.append(f"### {s.get('url')}")
        if s.get('error'): lines.append(f"- error: {s['error']}")
        for token,ss in s.get('snippets',{}).items():
            lines.append(f'- `{token}`:')
            for x in ss[:3]: lines.append(f'  - `{x[:3500]}`')
        lines.append('')
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
