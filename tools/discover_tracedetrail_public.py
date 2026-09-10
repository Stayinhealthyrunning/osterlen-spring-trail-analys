#!/usr/bin/env python3
"""Collect reproducible public metadata/POIs from Trace de Trail references.

This intentionally does not download or commit third-party GPX bodies. It extracts the
public `dataPi` waypoint payload already in the route page and discovers GPX-related links,
forms and endpoint-looking literals for later provenance/reuse review.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import hashlib, json, math, re, urllib.request

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'config/course-source-manifest.json'
OUT=ROOT/'reports/tracedetrail-public-discovery.json'
POI_OUT=ROOT/'data/source/tracedetrail/waypoints.json'
UA='OST-analysis-research/1.0 (+https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class Collector(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.forms=[]; self.inputs=[]; self._form=None
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'):
            self.links.append({'href':d['href'],'download':d.get('download'),'class':d.get('class'),'id':d.get('id'),'title':d.get('title')})
        if tag=='form':
            self._form={'action':d.get('action'),'method':(d.get('method') or 'GET').upper(),'id':d.get('id'),'class':d.get('class'),'inputs':[]}
            self.forms.append(self._form)
        if tag in {'input','button','select'}:
            item={k:d.get(k) for k in ('type','name','value','id','class','formaction') if d.get(k) is not None}
            self.inputs.append(item)
            if self._form is not None: self._form['inputs'].append(item)
    def handle_endtag(self,tag):
        if tag=='form': self._form=None

def extract_escaped_json_string(html,key):
    marker=re.compile(r'"?'+re.escape(key)+r'"?\s*:\s*"')
    m=marker.search(html)
    if not m: return None
    i=m.end(); buf=[]
    while i<len(html):
        ch=html[i]
        if ch=='\\':
            if i+1>=len(html): break
            nxt=html[i+1]
            if nxt=='u' and i+5<len(html):
                try: buf.append(chr(int(html[i+2:i+6],16))); i+=6; continue
                except ValueError: pass
            mapping={'"':'"','\\':'\\','/':'/','n':'\n','r':'\r','t':'\t','b':'\b','f':'\f'}
            buf.append(mapping.get(nxt,nxt)); i+=2; continue
        if ch=='"': return ''.join(buf)
        buf.append(ch); i+=1
    return None

def mercator_to_wgs84(x,y):
    origin=20037508.342789244
    lon=x/origin*180.0; lat=y/origin*180.0
    lat=180/math.pi*(2*math.atan(math.exp(lat*math.pi/180))-math.pi/2)
    return round(lat,7),round(lon,7)

def clean_text(v,max_len=500):
    if not isinstance(v,str): return None
    v=re.sub(r'<[^>]+>',' ',v); v=re.sub(r'\s+',' ',v).strip()
    return v[:max_len] if v else None

def normalize_pi(entry):
    x=entry.get('abs'); ymerc=entry.get('ord')
    try: lat,lon=mercator_to_wgs84(float(x),float(ymerc))
    except Exception: lat=lon=None
    title=clean_text(entry.get('infobulleTitre')) or clean_text(entry.get('passageLabel')) or clean_text(entry.get('labels'))
    types=[str(entry[k]).strip() for k in ('type','type2','type3') if entry.get(k) not in (None,'')]
    out={
      'source_pi_id':entry.get('piID'),'title':title,'types':types,
      'lat':lat,'lon':lon,'elevation_m':entry.get('y'),
      'planned_time':clean_text(entry.get('bh'),100),'planned_time_detail':clean_text(entry.get('bhd'),100),
    }
    for key,val in entry.items():
        lk=str(key).lower()
        if any(term in lk for term in ('dist','km','passage')) and key not in {'passageLabel','passageDescription','passageDescription2'}:
            if isinstance(val,(int,float,str)) and str(val).strip():
                out.setdefault('source_distance_fields',{})[str(key)]=val
    return {k:v for k,v in out.items() if v not in (None,[],{})}

def fetch_trace(trace_id):
    url=f'https://tracedetrail.fr/fr/trace/{trace_id}'
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=40) as r:
        body=r.read(8_000_000); final=r.geturl(); ctype=r.headers.get('Content-Type','')
    html=body.decode('utf-8',errors='replace')
    raw=extract_escaped_json_string(html,'dataPi')
    pi=[]; raw_keys=[]; pi_error=None
    if raw is not None:
        try:
            decoded=json.loads(raw)
            if isinstance(decoded,list):
                raw_keys=sorted({str(k) for e in decoded if isinstance(e,dict) for k in e.keys()})
                pi=[normalize_pi(e) for e in decoded if isinstance(e,dict)]
        except Exception as exc: pi_error=f'{type(exc).__name__}: {exc}'
    p=Collector(); p.feed(html)
    links=[]
    for item in p.links:
        href=urljoin(final,item['href'])
        if 'gpx' in href.lower() or any('gpx' in str(v).lower() for v in item.values() if v):
            links.append({**item,'href':href})
    forms=[]
    for f in p.forms:
        text=json.dumps(f,ensure_ascii=False).lower()
        if 'gpx' in text or 'export' in text or 'download' in text:
            forms.append({**f,'action':urljoin(final,f.get('action') or final)})
    literals=sorted(set(re.findall(r'["\']([^"\']{1,240})["\']',html)))
    endpoint_literals=[x for x in literals if ('gpx' in x.lower() or ('trace' in x.lower() and any(t in x.lower() for t in ('download','export'))))][:300]
    js_data_keys=sorted(set(re.findall(r'\b(data[A-Z][A-Za-z0-9_]*)\s*:',html)))[:200]
    return {
      'trace_id':trace_id,'url':url,'final_url':final,'status':200,'content_type':ctype,
      'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),
      'data_pi_found':raw is not None,'data_pi_error':pi_error,'data_pi_count':len(pi),
      'data_pi_raw_keys':raw_keys,'waypoints':pi,
      'gpx_related_links':links[:100],'gpx_related_forms':forms[:100],
      'gpx_endpoint_literals':endpoint_literals,'js_data_keys':js_data_keys,
    }

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    refs={}
    for s in manifest['sources']:
        tid=s.get('trace_id')
        if tid:
            refs.setdefault(int(tid),[]).append({'family':s.get('family'),'year':s.get('year'),'status':s.get('status')})
    traces=[]; errors=[]
    for tid in sorted(refs):
        try:
            item=fetch_trace(tid); item['manifest_refs']=refs[tid]; traces.append(item)
            print(tid,'poi',item['data_pi_count'],'gpx-links',len(item['gpx_related_links']),'literals',len(item['gpx_endpoint_literals']))
        except Exception as exc:
            errors.append({'trace_id':tid,'error':f'{type(exc).__name__}: {exc}','manifest_refs':refs[tid]}); print('ERR',tid,exc)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'policy':'Public page metadata/waypoints only; no third-party GPX body archived.','traces':traces,'errors':errors}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    poi={'generated_at':report['generated_at'],'source':'Trace de Trail public dataPi payloads','routes':[
      {'trace_id':t['trace_id'],'manifest_refs':t['manifest_refs'],'waypoints':t['waypoints']} for t in traces
    ]}
    POI_OUT.parent.mkdir(parents=True,exist_ok=True); POI_OUT.write_text(json.dumps(poi,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors: print(f'Completed with {len(errors)} fetch errors')

if __name__=='__main__': main()
