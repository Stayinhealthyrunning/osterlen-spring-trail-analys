#!/usr/bin/env python3
"""Inspect the public Trace de Trail `dataTrace` object at top level.

The page embeds a large JavaScript object rather than strict JSON. This diagnostic
records property names, value types, lengths and tiny prefixes so route-geometry
fields can be identified without mirroring the complete third-party payload.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, urllib.request

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'config/course-source-manifest.json').read_text(encoding='utf-8'))
OUT=ROOT/'reports/tracedetrail-datatrace-structure.json'
OUT_MD=ROOT/'reports/tracedetrail-datatrace-structure.md'
UA='OST-analysis-research/1.0 (+https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

def fetch(trace_id):
    url=f'https://tracedetrail.fr/fr/trace/{trace_id}'
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=40) as r:
        return r.read(8_000_000).decode('utf-8','replace')

def quoted(text,start):
    q=text[start]; i=start+1; out=[]
    while i<len(text):
        ch=text[i]
        if ch=='\\':
            if i+1>=len(text): break
            n=text[i+1]
            if n=='u' and i+5<len(text):
                try: out.append(chr(int(text[i+2:i+6],16))); i+=6; continue
                except ValueError: pass
            out.append({'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f'}.get(n,n)); i+=2; continue
        if ch==q: return ''.join(out),i+1
        out.append(ch); i+=1
    raise ValueError('unterminated string')

def balanced(text,start):
    op=text[start]; cl='}' if op=='{' else ']'; depth=0; q=None; esc=False
    for i in range(start,len(text)):
        ch=text[i]
        if q:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==q: q=None
            continue
        if ch in ('"',"'"): q=ch; continue
        if ch==op: depth+=1
        elif ch==cl:
            depth-=1
            if depth==0: return text[start:i+1],i+1
    raise ValueError('unterminated balanced value')

def data_trace_object(html):
    m=re.search(r'(?<![A-Za-z0-9_])dataTrace\s*:\s*\{',html)
    if not m: return None
    start=html.find('{',m.start())
    raw,_=balanced(html,start)
    return raw

def parse_top(raw):
    if not raw or raw[0]!='{': return []
    i=1; props=[]
    while i<len(raw)-1:
        while i<len(raw) and (raw[i].isspace() or raw[i]==','): i+=1
        if i>=len(raw)-1: break
        if raw[i] in ('"',"'"):
            key,i=quoted(raw,i)
        else:
            m=re.match(r'[A-Za-z_$][A-Za-z0-9_$]*',raw[i:])
            if not m: i+=1; continue
            key=m.group(0); i+=len(key)
        while i<len(raw) and raw[i].isspace(): i+=1
        if i>=len(raw) or raw[i] != ':': continue
        i+=1
        while i<len(raw) and raw[i].isspace(): i+=1
        if i>=len(raw): break
        start=i; decoded=None
        if raw[i] in ('"',"'"):
            decoded,i=quoted(raw,i); kind='string'; raw_len=i-start
            val_len=len(decoded)
            prefix=decoded[:140]
            sha=hashlib.sha256(decoded.encode('utf-8')).hexdigest()
            nested=None
            s=decoded.lstrip()
            if s.startswith(('{','[')):
                try:
                    obj=json.loads(decoded)
                    nested={'json_type':type(obj).__name__,'count':len(obj) if isinstance(obj,(list,dict)) else None,
                            'keys':sorted(map(str,obj.keys()))[:80] if isinstance(obj,dict) else None}
                except Exception: nested={'json_type':'invalid_or_non_json'}
        elif raw[i] in '[{':
            val,i=balanced(raw,i); kind='object' if val[0]=='{' else 'array'; raw_len=len(val); val_len=raw_len; prefix=val[:140]; sha=hashlib.sha256(val.encode()).hexdigest(); nested=None
        else:
            j=i; q=None; depth=0
            while j<len(raw):
                ch=raw[j]
                if ch in '[{(': depth+=1
                elif ch in ']})': depth=max(0,depth-1)
                elif ch==',' and depth==0: break
                j+=1
            val=raw[i:j].strip(); i=j; kind='scalar'; raw_len=len(val); val_len=raw_len; prefix=val[:140]; sha=hashlib.sha256(val.encode()).hexdigest(); nested=None
        rec={'key':key,'kind':kind,'value_length':val_len,'raw_length':raw_len,'sha256':sha,'prefix':prefix}
        if nested: rec['decoded_json_summary']=nested
        if kind=='scalar' and re.fullmatch(r'-?\d+(?:\.\d+)?',prefix): rec['numeric_value']=float(prefix) if '.' in prefix else int(prefix)
        props.append(rec)
    return props

def main():
    refs={}
    for s in MANIFEST.get('sources',[]):
        if s.get('trace_id'):
            refs.setdefault(int(s['trace_id']),[]).append({'family':s.get('family'),'year':s.get('year')})
    rows=[]; errors=[]
    for tid in sorted(refs):
        try:
            html=fetch(tid); raw=data_trace_object(html)
            props=parse_top(raw) if raw else []
            rows.append({'trace_id':tid,'manifest_refs':refs[tid],'data_trace_found':raw is not None,'data_trace_length':len(raw or ''),'properties':props})
            print(tid,'properties',len(props),'large',[(p['key'],p['value_length']) for p in props if p['value_length']>5000][:8])
        except Exception as exc:
            errors.append({'trace_id':tid,'error':f'{type(exc).__name__}: {exc}'})
    report={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'rows':rows,'errors':errors,
            'note':'Only top-level property metadata and short prefixes are stored; complete dataTrace payloads are not mirrored.'}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    keys={}
    for r in rows:
        for p in r['properties']:
            k=p['key']; e=keys.setdefault(k,{'count':0,'kinds':set(),'max_length':0,'example_prefix':p['prefix']})
            e['count']+=1; e['kinds'].add(p['kind']); e['max_length']=max(e['max_length'],p['value_length'])
    lines=['# Trace de Trail `dataTrace` structure','',
           'Top-level property inventory from public route pages. Full payloads are not copied.','',
           '| Property | Seen in traces | Kind | Max value length | Example prefix |',
           '|---|---:|---|---:|---|']
    for k,e in sorted(keys.items(),key=lambda kv:(-kv[1]['max_length'],kv[0])):
        pref=e['example_prefix'].replace('|','\\|').replace('\n',' ')[:80]
        lines.append(f"| `{k}` | {e['count']} | {', '.join(sorted(e['kinds']))} | {e['max_length']} | `{pref}` |")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
