#!/usr/bin/env python3
"""Collect reproducible public metadata/POIs and inspect route geometry from Trace de Trail.

The public route page embeds information needed to render its map. This tool extracts
factual waypoint data and inspects the public `dataTrace` payload without attempting
an authenticated GPX download. Only normalized factual route data may be emitted once
its structure is understood.
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
TRACE_SUMMARY_OUT=ROOT/'data/source/tracedetrail/trace-payload-summary.json'
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

def parse_js_quoted(text,start):
    quote=text[start]; i=start+1; buf=[]
    while i<len(text):
        ch=text[i]
        if ch=='\\':
            if i+1>=len(text): break
            nxt=text[i+1]
            if nxt=='u' and i+5<len(text):
                try: buf.append(chr(int(text[i+2:i+6],16))); i+=6; continue
                except ValueError: pass
            mapping={'"':'"',"'":"'",'\\':'\\','/':'/','n':'\n','r':'\r','t':'\t','b':'\b','f':'\f'}
            buf.append(mapping.get(nxt,nxt)); i+=2; continue
        if ch==quote: return ''.join(buf),i+1
        buf.append(ch); i+=1
    return None,None

def extract_js_value(html,key):
    """Extract a simple JS object-property value after `key:`.

    Supports quoted strings and balanced JSON-like arrays/objects. The latter is used
    for structural inspection only; failure is recorded rather than guessed around.
    """
    m=re.search(r'(?<![A-Za-z0-9_])(?:["\']?'+re.escape(key)+r'["\']?)\s*:\s*',html)
    if not m: return None,None,None
    start=m.end()
    while start<len(html) and html[start].isspace(): start+=1
    context=' '.join(html[max(0,m.start()-120):min(len(html),start+360)].split())[:500]
    if start>=len(html): return None,context,'value_missing'
    if html[start] in ('"',"'"):
        value,end=parse_js_quoted(html,start)
        return value,context,None if value is not None else 'unterminated_quoted_value'
    if html[start] not in '[{':
        end=html.find(',',start)
        if end<0: end=min(len(html),start+1000)
        return html[start:end].strip(),context,None
    opener=html[start]; closer='}' if opener=='{' else ']'
    depth=0; quote=None; escaped=False
    for i in range(start,len(html)):
        ch=html[i]
        if quote:
            if escaped: escaped=False
            elif ch=='\\': escaped=True
            elif ch==quote: quote=None
            continue
        if ch in ('"',"'"): quote=ch; continue
        if ch==opener: depth+=1
        elif ch==closer:
            depth-=1
            if depth==0: return html[start:i+1],context,None
    return None,context,'unterminated_balanced_value'

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

def structural_summary(value,depth=0,max_depth=4):
    if depth>=max_depth:
        if isinstance(value,dict): return {'type':'object','count':len(value),'keys':sorted(map(str,value.keys()))[:80]}
        if isinstance(value,list): return {'type':'array','count':len(value)}
        return {'type':type(value).__name__}
    if isinstance(value,dict):
        out={'type':'object','count':len(value),'keys':sorted(map(str,value.keys()))[:120]}
        children={}
        for k,v in list(value.items())[:80]:
            if isinstance(v,(dict,list)): children[str(k)]=structural_summary(v,depth+1,max_depth)
        if children: out['children']=children
        return out
    if isinstance(value,list):
        out={'type':'array','count':len(value)}
        if value:
            out['item_types']=sorted({type(x).__name__ for x in value})
            out['first_item']=structural_summary(value[0],depth+1,max_depth)
        return out
    return {'type':type(value).__name__}

def collect_string_hints(value,path='$',out=None,limit=120):
    if out is None: out=[]
    if len(out)>=limit: return out
    if isinstance(value,dict):
        for k,v in value.items():
            collect_string_hints(v,f'{path}.{k}',out,limit)
            if len(out)>=limit: break
    elif isinstance(value,list):
        for i,v in enumerate(value[:50]):
            collect_string_hints(v,f'{path}[{i}]',out,limit)
            if len(out)>=limit: break
    elif isinstance(value,str):
        s=value.strip(); lower=s.lower()
        if any(t in lower for t in ('linestring','coordinates','polyline','geom','trace')) or (len(s)>200 and re.search(r'-?\d+[.,]\d+[,; ]+-?\d+[.,]\d+',s)):
            out.append({'path':path,'length':len(s),'sha256':hashlib.sha256(s.encode('utf-8')).hexdigest(),'prefix':s[:120]})
    return out

def decode_embedded(html,key):
    raw,context,extract_error=extract_js_value(html,key)
    if raw is None: return None,None,extract_error,context
    # Quoted data payloads often contain a JSON string. Unquoted payloads may already
    # be an object/array. Try JSON first; then one extra JSON-string decode.
    try:
        decoded=json.loads(raw)
        if isinstance(decoded,str) and decoded.lstrip().startswith(('{','[')):
            try: decoded=json.loads(decoded)
            except Exception: pass
        return raw,decoded,None,context
    except Exception as exc:
        return raw,None,f'{type(exc).__name__}: {exc}',context

def fetch_trace(trace_id):
    url=f'https://tracedetrail.fr/fr/trace/{trace_id}'
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=40) as r:
        body=r.read(8_000_000); final=r.geturl(); ctype=r.headers.get('Content-Type','')
    html=body.decode('utf-8',errors='replace')

    pi_raw,pi_decoded,pi_error,pi_context=decode_embedded(html,'dataPi')
    pi=[]; raw_keys=[]
    if isinstance(pi_decoded,list):
        raw_keys=sorted({str(k) for e in pi_decoded if isinstance(e,dict) for k in e.keys()})
        pi=[normalize_pi(e) for e in pi_decoded if isinstance(e,dict)]

    trace_raw,trace_decoded,trace_error,trace_context=decode_embedded(html,'dataTrace')
    trace_summary=structural_summary(trace_decoded) if trace_decoded is not None else None
    trace_hints=collect_string_hints(trace_decoded) if trace_decoded is not None else []

    p=Collector(); p.feed(html)
    links=[]
    for item in p.links:
        href=urljoin(final,item['href'])
        if 'gpx' in href.lower() or any('gpx' in str(v).lower() for v in item.values() if v): links.append({**item,'href':href})
    forms=[]
    for f in p.forms:
        text=json.dumps(f,ensure_ascii=False).lower()
        if 'gpx' in text or 'export' in text or 'download' in text: forms.append({**f,'action':urljoin(final,f.get('action') or final)})
    literals=sorted(set(re.findall(r'["\']([^"\']{1,240})["\']',html)))
    endpoint_literals=[x for x in literals if ('gpx' in x.lower() or ('trace' in x.lower() and any(t in x.lower() for t in ('download','export'))))][:300]
    js_data_keys=sorted(set(re.findall(r'\b(data[A-Z][A-Za-z0-9_]*)\s*:',html)))[:200]
    return {
      'trace_id':trace_id,'url':url,'final_url':final,'status':200,'content_type':ctype,
      'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),
      'data_pi_found':pi_raw is not None,'data_pi_error':pi_error,'data_pi_count':len(pi),
      'data_pi_raw_keys':raw_keys,'waypoints':pi,
      'data_trace_found':trace_raw is not None,'data_trace_bytes':len(trace_raw.encode('utf-8')) if trace_raw is not None else 0,
      'data_trace_sha256':hashlib.sha256(trace_raw.encode('utf-8')).hexdigest() if trace_raw is not None else None,
      'data_trace_error':trace_error,'data_trace_structure':trace_summary,'data_trace_string_hints':trace_hints,
      'data_trace_context':trace_context,
      'gpx_related_links':links[:100],'gpx_related_forms':forms[:100],
      'gpx_endpoint_literals':endpoint_literals,'js_data_keys':js_data_keys,
    }

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    refs={}
    for s in manifest['sources']:
        tid=s.get('trace_id')
        if tid: refs.setdefault(int(tid),[]).append({'family':s.get('family'),'year':s.get('year'),'status':s.get('status')})
    traces=[]; errors=[]
    for tid in sorted(refs):
        try:
            item=fetch_trace(tid); item['manifest_refs']=refs[tid]; traces.append(item)
            print(tid,'poi',item['data_pi_count'],'dataTrace',item['data_trace_found'],item['data_trace_bytes'],'bytes',item['data_trace_error'])
        except Exception as exc:
            errors.append({'trace_id':tid,'error':f'{type(exc).__name__}: {exc}','manifest_refs':refs[tid]}); print('ERR',tid,exc)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'policy':'Public page metadata/waypoints and structural inspection of embedded dataTrace; no authenticated GPX download and no complete third-party page archived.','traces':traces,'errors':errors}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    poi={'generated_at':report['generated_at'],'source':'Trace de Trail public dataPi payloads','routes':[
      {'trace_id':t['trace_id'],'manifest_refs':t['manifest_refs'],'waypoints':t['waypoints']} for t in traces
    ]}
    POI_OUT.parent.mkdir(parents=True,exist_ok=True); POI_OUT.write_text(json.dumps(poi,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'generated_at':report['generated_at'],'source':'Trace de Trail public embedded dataTrace payloads','routes':[
      {'trace_id':t['trace_id'],'manifest_refs':t['manifest_refs'],'found':t['data_trace_found'],'bytes':t['data_trace_bytes'],
       'sha256':t['data_trace_sha256'],'parse_error':t['data_trace_error'],'structure':t['data_trace_structure'],
       'geometry_string_hints':t['data_trace_string_hints'],'context':t['data_trace_context']} for t in traces
    ]}
    TRACE_SUMMARY_OUT.parent.mkdir(parents=True,exist_ok=True); TRACE_SUMMARY_OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if errors: print(f'Completed with {len(errors)} fetch errors')

if __name__=='__main__': main()
