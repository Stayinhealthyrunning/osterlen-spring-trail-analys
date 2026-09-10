#!/usr/bin/env python3
"""Analyze public Trace de Trail map geometry without redistributing coordinate payloads.

Trace de Trail route pages expose a `dataTrace.geometry` string to render the public map.
GPX export itself requires login, so this tool deliberately does not call the GPX export
endpoint and does not persist the geometry coordinate series. Geometry is decoded only in
memory to derive reproducible factual diagnostics: hashes, distances, elevation metadata,
landmark positions and cross-year route-overlap metrics.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, math, re, urllib.request

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'config/course-source-manifest.json').read_text(encoding='utf-8'))
WAYPOINTS_PATH=ROOT/'data/source/tracedetrail/waypoints.json'
WAYPOINTS=json.loads(WAYPOINTS_PATH.read_text(encoding='utf-8')) if WAYPOINTS_PATH.exists() else {'routes':[]}
OUT=ROOT/'reports/tracedetrail-public-geometry-analysis.json'
OUT_MD=ROOT/'reports/tracedetrail-public-geometry-analysis.md'
UA='OST-analysis-research/1.0 (+https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'
R=6371008.8
ORIGIN=20037508.342789244


def fetch(trace_id):
    url=f'https://tracedetrail.fr/fr/trace/{trace_id}'
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.read(8_000_000).decode('utf-8','replace'),r.geturl()


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
            out.append({'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f','/':'/'}.get(n,n)); i+=2; continue
        if ch==q: return ''.join(out),i+1
        out.append(ch); i+=1
    raise ValueError('unterminated JS string')


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
    raise ValueError('unterminated JS structure')


def datatrace_object(html):
    m=re.search(r'(?<![A-Za-z0-9_])dataTrace\s*:\s*\{',html)
    if not m: raise ValueError('dataTrace object not found')
    start=html.find('{',m.start())
    return balanced(html,start)[0]


def top_properties(raw):
    """Parse simple top-level JS object fields used by dataTrace."""
    props={}; i=1
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
        if raw[i] in ('"',"'"):
            value,i=quoted(raw,i)
        elif raw[i] in '[{':
            value,i=balanced(raw,i)
        else:
            j=i; depth=0; q=None; esc=False
            while j<len(raw):
                ch=raw[j]
                if q:
                    if esc: esc=False
                    elif ch=='\\': esc=True
                    elif ch==q: q=None
                else:
                    if ch in ('"',"'"): q=ch
                    elif ch in '[{(': depth+=1
                    elif ch in ']})': depth=max(0,depth-1)
                    elif ch==',' and depth==0: break
                j+=1
            value=raw[i:j].strip(); i=j
            if re.fullmatch(r'-?\d+',value): value=int(value)
            elif re.fullmatch(r'-?\d+(?:\.\d+)',value): value=float(value)
            elif value=='true': value=True
            elif value=='false': value=False
            elif value in ('null','undefined'): value=None
        props[key]=value
    return props


def mercator_to_wgs(x,y):
    lon=x/ORIGIN*180.0
    lat=y/ORIGIN*180.0
    lat=180/math.pi*(2*math.atan(math.exp(lat*math.pi/180))-math.pi/2)
    return lat,lon


def hav(a,b):
    lat1,lon1=map(math.radians,a); lat2,lon2=map(math.radians,b)
    dlat=lat2-lat1; dlon=lon2-lon1
    h=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))


def decode_geometry(value):
    if not isinstance(value,str): raise ValueError('geometry is not a string')
    geom=json.loads(value)
    if not isinstance(geom,list) or len(geom)<2: raise ValueError('geometry is not a usable point array')
    pts=[]
    for p in geom:
        if not isinstance(p,dict) or p.get('lon') is None or p.get('lat') is None: continue
        lat,lon=mercator_to_wgs(float(p['lon']),float(p['lat']))
        pts.append({'lat':lat,'lon':lon,'x':p.get('x'),'y':p.get('y'),'dp':p.get('dp'),'dn':p.get('dn')})
    if len(pts)<2: raise ValueError('geometry contains too few valid points')
    return geom,pts


def cumulative(pts):
    c=[0.0]
    for a,b in zip(pts,pts[1:]): c.append(c[-1]+hav((a['lat'],a['lon']),(b['lat'],b['lon'])))
    return c


def resample(pts,step=50.0):
    c=cumulative(pts); total=c[-1]; targets=[]; d=0.0
    while d<total: targets.append(d); d+=step
    targets.append(total)
    out=[]; j=1
    for t in targets:
        while j<len(c)-1 and c[j]<t: j+=1
        a=max(0,j-1); b=j; span=c[b]-c[a]
        q=0.0 if span<=0 else (t-c[a])/span
        lat=pts[a]['lat']+(pts[b]['lat']-pts[a]['lat'])*q
        lon=pts[a]['lon']+(pts[b]['lon']-pts[a]['lon'])*q
        out.append((t,lat,lon))
    return out


def xy_samples(samples,lat0):
    co=math.cos(math.radians(lat0))
    return [(d,math.radians(lon)*R*co,math.radians(lat)*R) for d,lat,lon in samples]


def spatial_grid(samples,cell=250.0):
    grid=defaultdict(list)
    for d,x,y in samples: grid[(math.floor(x/cell),math.floor(y/cell))].append((d,x,y))
    return grid


def nearest_series(a,b,cell=250.0):
    lat0=sum([v[1] for v in a]+[v[1] for v in b])/(len(a)+len(b))
    aa=xy_samples(a,lat0); bb=xy_samples(b,lat0); grid=spatial_grid(bb,cell)
    out=[]
    for d,x,y in aa:
        cx,cy=math.floor(x/cell),math.floor(y/cell); candidates=[]
        for radius in range(0,8):
            for gx in range(cx-radius,cx+radius+1):
                for gy in range(cy-radius,cy+radius+1):
                    if radius and max(abs(gx-cx),abs(gy-cy))!=radius: continue
                    candidates.extend(grid.get((gx,gy),()))
            if candidates:
                # Once a full neighboring ring beyond the current best is covered, no
                # farther cell can improve enough for the corridor thresholds we use.
                best=min(math.hypot(x-x2,y-y2) for _,x2,y2 in candidates)
                if radius>=2 or best<cell*max(1,radius): break
        if not candidates:
            candidates=bb
        sep=min(math.hypot(x-x2,y-y2) for _,x2,y2 in candidates)
        out.append((d,sep))
    return out


def percentile(values,q):
    v=sorted(values)
    if not v: return None
    pos=(len(v)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return v[lo]
    return v[lo]+(v[hi]-v[lo])*(pos-lo)


def divergence(series,threshold=100.0,min_len=300.0):
    out=[]; start=None; last=None; vals=[]
    for d,sep in series:
        if sep>threshold:
            if start is None: start=d; vals=[]
            last=d; vals.append(sep)
        elif start is not None:
            if last-start>=min_len:
                out.append({'start_km':round(start/1000,2),'end_km':round(last/1000,2),'length_km':round((last-start)/1000,2),'median_separation_m':round(percentile(vals,.5),1),'max_separation_m':round(max(vals),1)})
            start=last=None; vals=[]
    if start is not None and last is not None and last-start>=min_len:
        out.append({'start_km':round(start/1000,2),'end_km':round(last/1000,2),'length_km':round((last-start)/1000,2),'median_separation_m':round(percentile(vals,.5),1),'max_separation_m':round(max(vals),1)})
    return out


def comparison(a,b):
    ra=resample(a['points'],50); rb=resample(b['points'],50)
    ab=nearest_series(ra,rb); ba=nearest_series(rb,ra)
    av=[x[1] for x in ab]; bv=[x[1] for x in ba]
    shared={}
    for t in (25,50,100,250):
        fa=sum(v<=t for v in av)/len(av); fb=sum(v<=t for v in bv)/len(bv)
        shared[str(t)]={'a_fraction':round(fa,4),'b_fraction':round(fb,4),'symmetric_min_fraction':round(min(fa,fb),4),'symmetric_mean_fraction':round((fa+fb)/2,4)}
    start=hav(a['start'],b['start']); finish=hav(a['finish'],b['finish']); dd=b['path_distance_km']-a['path_distance_km']
    s50=shared['50']['symmetric_min_fraction']; s100=shared['100']['symmetric_min_fraction']
    exact=a['geometry_sha256']==b['geometry_sha256']
    if exact: cls='exact_same_public_geometry'
    elif s50>=.98 and abs(dd)<=.5 and start<=100 and finish<=100: cls='same_course_geometry_strong'
    elif s100>=.95: cls='largely_same_corridor_with_changes'
    elif s100>=.70: cls='substantial_shared_corridor_but_material_changes'
    else: cls='materially_different_geometry'
    return {
      'a_trace_id':a['trace_id'],'b_trace_id':b['trace_id'],'family':a['family'],
      'a_year':a['year'],'b_year':b['year'],'geometry_hash_equal':exact,
      'distance_difference_km':round(dd,3),'start_separation_m':round(start,1),'finish_separation_m':round(finish,1),
      'shared_corridor_fraction_by_threshold_m':shared,
      'a_to_b_nearest_m':{'median':round(percentile(av,.5),1),'p95':round(percentile(av,.95),1),'max':round(max(av),1)},
      'b_to_a_nearest_m':{'median':round(percentile(bv,.5),1),'p95':round(percentile(bv,.95),1),'max':round(max(bv),1)},
      'a_divergence_intervals_over_100m':divergence(ab),
      'b_divergence_intervals_over_100m':divergence(ba),
      'classification':cls,
    }


def nearest_route_point(lat,lon,pts,cum):
    lat0=math.radians(lat); co=math.cos(lat0)
    def xy(p): return (math.radians(p['lon']-lon)*R*co,math.radians(p['lat']-lat)*R)
    best=None
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        ax,ay=xy(a); bx,by=xy(b); vx,vy=bx-ax,by-ay; den=vx*vx+vy*vy
        t=0 if den<=0 else max(0,min(1,-(ax*vx+ay*vy)/den)); xx=ax+t*vx; yy=ay+t*vy
        sep=math.hypot(xx,yy)
        if best is None or sep<best[0]: best=(sep,cum[i]+t*(cum[i+1]-cum[i]))
    return best


def waypoint_index():
    return {int(r['trace_id']):r.get('waypoints',[]) for r in WAYPOINTS.get('routes',[])}


def semantic(title):
    s=(title or '').lower()
    if 'bengtem' in s: return 'bengtemolla'
    if 'vantal' in s: return 'vantalangan'
    if 'stenshuvud' in s: return 'stenshuvud'
    return None


def geometry_record(ref,wpidx):
    tid=int(ref['trace_id']); html,final=fetch(tid); props=top_properties(datatrace_object(html))
    raw_geom=props.get('geometry'); raw_list,pts=decode_geometry(raw_geom); c=cumulative(pts)
    source_x=[p.get('x') for p in raw_list if isinstance(p,dict) and isinstance(p.get('x'),(int,float))]
    source_y=[p.get('y') for p in raw_list if isinstance(p,dict) and isinstance(p.get('y'),(int,float))]
    source_dp=[p.get('dp') for p in raw_list if isinstance(p,dict) and isinstance(p.get('dp'),(int,float))]
    source_dn=[p.get('dn') for p in raw_list if isinstance(p,dict) and isinstance(p.get('dn'),(int,float))]
    x_monotonic=all(b>=a for a,b in zip(source_x,source_x[1:])) if len(source_x)>1 else None
    landmarks=[]
    for wp in wpidx.get(tid,[]):
        if wp.get('lat') is None or wp.get('lon') is None: continue
        key=semantic(wp.get('title'))
        types=[str(x).lower() for x in wp.get('types',[])]
        if not key and not any(x in {'ravitoc','ravitaillement','basevie','bh'} for x in types): continue
        sep,dist=nearest_route_point(float(wp['lat']),float(wp['lon']),pts,c)
        landmarks.append({'source_pi_id':wp.get('source_pi_id'),'title':wp.get('title'),'semantic_key':key,'types':wp.get('types',[]),'projected_distance_km':round(dist/1000,3),'off_route_m':round(sep,1)})
    date=props.get('dateCompet')
    expected_year=int(ref['year'])
    source_year=None
    if isinstance(date,str):
        m=re.search(r'(\d{4})$',date); source_year=int(m.group(1)) if m else None
    return {
      'trace_id':tid,'family':ref['family'],'year':expected_year,'source_url':final,
      'source_date_compet':date,'source_date_year':source_year,'source_year_matches_manifest':source_year in (None,expected_year),
      'source_reported_distance_km':props.get('distance'),
      'geometry_sha256':hashlib.sha256(raw_geom.encode('utf-8')).hexdigest(),
      'geometry_point_count':len(pts),'path_distance_km':round(c[-1]/1000,3),
      'start':[round(pts[0]['lat'],6),round(pts[0]['lon'],6)],'finish':[round(pts[-1]['lat'],6),round(pts[-1]['lon'],6)],
      'source_x_count':len(source_x),'source_x_monotonic_non_decreasing':x_monotonic,
      'source_x_first':source_x[0] if source_x else None,'source_x_last':source_x[-1] if source_x else None,
      'source_y_min':min(source_y) if source_y else None,'source_y_max':max(source_y) if source_y else None,
      'source_dp_last':source_dp[-1] if source_dp else None,'source_dn_last':source_dn[-1] if source_dn else None,
      'source_alti_min':props.get('alti_min'),'source_alti_max':props.get('alti_max'),
      'landmarks':landmarks,
      # retained in-memory only for comparisons; removed before serialization
      'points':pts,
    }


def main():
    refs=[]
    seen=set()
    for src in MANIFEST.get('sources',[]):
        if src.get('trace_id') and src.get('family') in {'ultra60','trail22'}:
            key=(src['family'],int(src['year']) if not isinstance(src['year'],list) else tuple(src['year']),int(src['trace_id']))
            if key in seen: continue
            seen.add(key)
            years=src['year'] if isinstance(src['year'],list) else [src['year']]
            for y in years: refs.append({'family':src['family'],'year':int(y),'trace_id':int(src['trace_id'])})
    wpidx=waypoint_index(); records=[]; errors=[]
    for i,ref in enumerate(sorted(refs,key=lambda r:(r['family'],r['year'])),1):
        try:
            r=geometry_record(ref,wpidx); records.append(r)
            print(f"[{i}/{len(refs)}] {r['family']} {r['year']} trace {r['trace_id']} {r['path_distance_km']:.3f} km points={r['geometry_point_count']} date={r['source_date_compet']}")
        except Exception as exc:
            errors.append({**ref,'error':f'{type(exc).__name__}: {exc}'}); print('ERR',ref,exc)
    comparisons=[]
    for family in sorted({r['family'] for r in records}):
        rr=sorted([r for r in records if r['family']==family],key=lambda x:x['year'])
        for i in range(len(rr)):
            for j in range(i+1,len(rr)):
                comparisons.append(comparison(rr[i],rr[j]))
    serial=[]
    for r in records:
        x=dict(r); x.pop('points',None); serial.append(x)
    mismatches=[{'trace_id':r['trace_id'],'family':r['family'],'manifest_year':r['year'],'source_date_compet':r['source_date_compet']} for r in records if not r['source_year_matches_manifest']]
    payload={
      'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),
      'method_notes':[
        'Public dataTrace.geometry is decoded transiently in memory; full coordinate arrays are not stored in this repository.',
        'Trace geometry lon/lat fields are treated as Web Mercator metres and converted to WGS84 before Haversine route-length calculations.',
        'Cross-year comparison resamples routes every 50 m and computes symmetric nearest-route corridor fractions.',
        'Geometry hashes are SHA-256 of the decoded public geometry string and allow exact-equality checks without redistributing geometry.',
        'Landmark distances are derived by projecting public Trace de Trail waypoint coordinates onto the same transient route geometry.',
        'source_date_compet is checked against the manifest year; a mismatch is a provenance warning, not automatically proof that the geometry is wrong for the intended year.'
      ],
      'routes':serial,'comparisons':comparisons,'manifest_date_mismatches':mismatches,'errors':errors
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    lines=['# Trace de Trail public geometry analysis','',
           'Den publika kartgeometrin analyseras **endast transient**. Koordinatserien sparas inte i repot och den inloggningsskyddade GPX-exporten används inte.','',
           '## Banor','',
           '| Familj | År | Trace | datum i Trace | punkter | kartgeometri km | Trace km | geometry hash |',
           '|---|---:|---:|---|---:|---:|---:|---|']
    for r in sorted(serial,key=lambda x:(x['family'],x['year'])):
        mark=' ⚠' if not r['source_year_matches_manifest'] else ''
        lines.append(f"| `{r['family']}` | {r['year']} | {r['trace_id']} | {r['source_date_compet'] or '—'}{mark} | {r['geometry_point_count']} | {r['path_distance_km']:.3f} | {r['source_reported_distance_km']} | `{r['geometry_sha256'][:12]}` |")
    lines += ['','## Jämförelse mot närliggande tävlingsår','',
              '| Familj | År A | År B | exakt hash | inom 50 m | inom 100 m | Δ km | klassning |',
              '|---|---:|---:|:---:|---:|---:|---:|---|']
    byfam=defaultdict(list)
    for c in comparisons: byfam[c['family']].append(c)
    for family,cc in sorted(byfam.items()):
        years=sorted({c['a_year'] for c in cc}|{c['b_year'] for c in cc})
        adjacent=set(zip(years,years[1:]))
        for c in cc:
            if (c['a_year'],c['b_year']) not in adjacent: continue
            s=c['shared_corridor_fraction_by_threshold_m']
            lines.append(f"| `{family}` | {c['a_year']} | {c['b_year']} | {'✓' if c['geometry_hash_equal'] else '—'} | {100*s['50']['symmetric_min_fraction']:.1f}% | {100*s['100']['symmetric_min_fraction']:.1f}% | {c['distance_difference_km']:+.3f} | {c['classification']} |")
    lines += ['','## Namngivna checkpoints/serviceställen projekterade på kartgeometrin','',
              '| Familj | År | Landmark | km | restavstånd |',
              '|---|---:|---|---:|---:|']
    any_land=False
    for r in sorted(serial,key=lambda x:(x['family'],x['year'])):
        for lm in r.get('landmarks',[]):
            if not lm.get('semantic_key'): continue
            any_land=True
            lines.append(f"| `{r['family']}` | {r['year']} | {lm['semantic_key']} | {lm['projected_distance_km']:.3f} | {lm['off_route_m']:.1f} m |")
    if not any_land: lines.append('| — | — | — | — | — |')
    if mismatches:
        lines += ['','## Proveniensvarningar','']
        for m in mismatches: lines.append(f"- `{m['family']}` {m['manifest_year']}, trace {m['trace_id']}: `dateCompet={m['source_date_compet']}`.")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Completed routes={len(serial)} comparisons={len(comparisons)} mismatches={len(mismatches)} errors={len(errors)}')

if __name__=='__main__': main()
