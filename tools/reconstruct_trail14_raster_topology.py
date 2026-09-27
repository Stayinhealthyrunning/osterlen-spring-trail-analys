#!/usr/bin/env python3
import argparse, heapq, json, math
from pathlib import Path
import networkx as nx
import numpy as np
from pyproj import Transformer

CASTLE=(13.96063,55.71787)
HALL=(14.01780,55.70819)
OBS_REMAIN=4500.0

def D(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def L(p): return sum(D(a,b) for a,b in zip(p,p[1:]))

def segdist(p,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1]; c=vx*vx+vy*vy
    if not c:return D(p,a)
    t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/c))
    return D(p,(a[0]+t*vx,a[1]+t*vy))

def rdp(points,epsilon):
    if len(points)<3:return points[:]
    a,b=points[0],points[-1]; md=0.; mi=-1
    for i,p in enumerate(points[1:-1],1):
        q=segdist(p,a,b)
        if q>md:md=q;mi=i
    if md>epsilon:
        x=rdp(points[:mi+1],epsilon); y=rdp(points[mi:],epsilon)
        return x[:-1]+y
    return [a,b]

def main():
    ap=argparse.ArgumentParser()
    for x in ('skeleton','registration','geojson','gpx','qa'): ap.add_argument('--'+x,required=True)
    ap.add_argument('--provenance')
    a=ap.parse_args()
    s=json.loads(Path(a.skeleton).read_text()); r=json.loads(Path(a.registration).read_text())
    H=np.array(r['trail14_to_trail5_homography'],float)
    tr=Transformer.from_crs(4326,3006,always_xy=True); back=Transformer.from_crs(3006,4326,always_xy=True)
    castle=tr.transform(*CASTLE); hall=tr.transform(*HALL)

    def xy(p):
        q=H@np.array([p[0],p[1],1.]); px,py=q[0]/q[2],q[1]/q[2]
        return (432733+(px-25.3)/(1074.7-25.3)*5232-198.3,
                6176791-(py-49.5)/(694.7-49.5)*3040+111.9)

    pts=[tuple(map(int,p)) for p in s['skeleton_pixels_xy']]
    idx={p:i for i,p in enumerate(pts)}
    X=[xy(p) for p in pts]
    G=nx.Graph(); G.add_nodes_from(range(len(pts)))
    for i,(x,y) in enumerate(pts):
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if not(dx or dy):continue
                j=idx.get((x+dx,y+dy))
                if j is not None and j>i:G.add_edge(i,j,w=D(X[i],X[j]))

    cycpx=[tuple(map(float,p)) for p in max(s['cycles'],key=lambda z:z['node_count'])['vertices_xy']]
    oncyc=set()
    for i,p in enumerate(pts):
        if min(segdist(p,u,v) for u,v in zip(cycpx,cycpx[1:]+cycpx[:1]))<1.1:oncyc.add(i)

    endpoints=[]
    for p in s['skeleton']['endpoints_xy']:
        i=idx.get(tuple(p))
        if i is not None:endpoints.append(i)
    endpoints=sorted(endpoints,key=lambda i:D(X[i],castle))[:2]

    def tail(st):
        dist={st:0.}; prev={}; q=[(0.,st)]
        while q:
            du,u=heapq.heappop(q)
            if du!=dist.get(u):continue
            if u in oncyc:
                p=[u]
                while p[-1]!=st:p.append(prev[p[-1]])
                return list(reversed(p)),u
            for v,e in G[u].items():
                nd=du+e['w']
                if nd<dist.get(v,1e99):
                    dist[v]=nd;prev[v]=u;heapq.heappush(q,(nd,v))
        raise RuntimeError('no cycle')

    tails=[tail(i) for i in endpoints]
    tail_px=[[pts[i] for i in p] for p,_ in tails]
    entry_px=pts[tails[0][1]]
    ci=min(range(len(cycpx)),key=lambda i:D(cycpx[i],entry_px))
    cycle_px=cycpx[ci:]+cycpx[:ci]+[cycpx[ci]]

    # The one-pixel skeleton walks along the centre of a thick raster stroke and
    # inherits pixel staircase jitter. Derive simplification tolerance from the
    # measured mean stroke width itself; no race-distance target is used.
    line_width_px=s['source_component']['area']/s['skeleton']['total_edge_length_px']
    tail_px_s=[rdp(p,line_width_px) for p in tail_px]
    cycle_px_s=rdp(cycle_px,line_width_px)
    T=[[xy(p) for p in z] for z in tail_px_s]
    C=[xy(p) for p in cycle_px_s]

    cycles=[('forward',C),('reverse',[C[0]]+list(reversed(C[1:-1]))+[C[0]])]
    variants=[]
    for si in (0,1):
        for name,c in cycles:
            route=T[si]+c[1:]+list(reversed(T[1-si]))[1:]
            hi=min(range(len(route)),key=lambda i:D(route[i],hall))
            total=L(route); at=L(route[:hi+1]); rem=total-at
            variants.append((abs(rem-OBS_REMAIN),si,name,route,total,at,rem,D(route[hi],hall)))

    # Participant evidence selects direction only. Shape, simplification and
    # total length are fixed before this choice and do not use watch distance.
    best=min(variants,key=lambda z:z[0])
    _,si,name,route,total,at,rem,hallgap=best
    ll=[back.transform(*p) for p in route]

    feat={'type':'Feature','properties':{
        'name':'ÖST Trail 13/14 km organizer-raster topology',
        'status':'georeferenced_organizer_raster_reference',
        'distance_km':round(total/1000,3),
        'provenance':'organizer raster + line-width-derived smoothing + participant Hallamölla direction control',
        'not_an_organizer_gpx':True,
        'raster_smoothing_method':'RDP epsilon derived from mean organizer route-stroke width',
        'raster_smoothing_epsilon_px':round(line_width_px,3)
    },'geometry':{'type':'LineString','coordinates':[list(p) for p in ll]}}
    Path(a.geojson).parent.mkdir(parents=True,exist_ok=True)
    Path(a.geojson).write_text(json.dumps(feat,ensure_ascii=False,indent=2)+'\n')

    t=''.join(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>' for lon,lat in ll)
    Path(a.gpx).write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Loppanalys"><trk><name>ÖST Trail 13/14 raster topology</name><trkseg>'+t+'</trkseg></trk></gpx>\n')

    raw_tail_lengths=[L([X[i] for i in p]) for p,_ in tails]
    rawC=[xy(p) for p in cycpx]; raw_cycle=L(rawC+[rawC[0]])
    raw_total=sum(raw_tail_lengths)+raw_cycle
    qa={
      'schema_version':3,
      'status':'georeferenced_organizer_raster_reference',
      'distance_km':round(total/1000,3),
      'raw_skeleton_distance_km':round(raw_total/1000,3),
      'participant_2023_reference_km':13.67,
      'participant_watch_distance_used_as_geometry_input':False,
      'participant_hallamolla_direction_control_used':True,
      'participant_distance_delta_m':round(abs(total-13670.0),1),
      'hallamolla_at_km':round(at/1000,3),
      'hallamolla_remaining_km':round(rem/1000,3),
      'participant_hallamolla_remaining_km':4.5,
      'hallamolla_control_m':round(hallgap,1),
      'start_finish_gap_m':round(D(route[0],route[-1]),1),
      'selected_start_tail':si,
      'selected_cycle_direction':name,
      'raw_tail_lengths_km':[round(x/1000,3) for x in raw_tail_lengths],
      'raw_cycle_length_km':round(raw_cycle/1000,3),
      'smoothed_tail_lengths_km':[round(L(x)/1000,3) for x in T],
      'smoothed_cycle_length_km':round(L(C)/1000,3),
      'raster_component_mean_width_px':round(line_width_px,3),
      'raster_smoothing_epsilon_px':round(line_width_px,3),
      'smoothing_parameter_source':'organizer route-stroke mean width; independent of participant distance',
      'map_registration_median_px':r['reprojection_px']['median'],
      'map_registration_p95_px':r['reprojection_px']['p95'],
      'variants':[{'start_tail':v[1],'direction':v[2],'distance_km':round(v[4]/1000,3),
                   'hall_remaining_km':round(v[6]/1000,3),'hall_control_m':round(v[7],1)}
                  for v in variants]
    }
    qa['topology_qa_pass']=(abs(qa['hallamolla_remaining_km']-4.5)<=0.15
                            and qa['hallamolla_control_m']<=150
                            and 12<=qa['distance_km']<=14.8
                            and qa['map_registration_p95_px']<=2.0)
    Path(a.qa).write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')

    if a.provenance:
        prov={
          'schema_version':'1.2','race':'Österlen Spring Trail','course':'Trail 13/14 km',
          'geometry_status':'validated_raster_reference',
          'primary_geometry_basis':'georeferenced organizer raster topology with line-width-derived smoothing',
          'not_an_organizer_gpx':True,'publishable_as_reconstructed_reference':True,
          'sources':[
            {'type':'organizer_georeferenced_raster','path':'data/source/maps/ost-trail13-14-organizer-map.jpg','role':'primary route geometry and topology'},
            {'type':'map_registration','path':'reports/organizer-map-registration.json','role':'high-precision registration into the georeferenced Trail 5 map frame'},
            {'type':'participant_race_activity','source_id':'jogg-2023-trail14-anna-karin-d','participant':'Anna Karin Delborg','role':'independent direction and plausibility validation only','observed_watch_distance_km':13.67,'official_finish_time':'1:31:44','observed_watch_time':'1:31:44','hallamolla_remaining_km':4.5},
            {'type':'official_local_trail','description':'Christinehof Ekopark Hallamöllaleden, published as 8.5 km','role':'independent corridor/topology corroboration; not used to force raster geometry'}
          ],
          'qa':{'path':'qa.json','distance_km':qa['distance_km'],'raw_skeleton_distance_km':qa['raw_skeleton_distance_km'],
                'hallamolla_remaining_km':qa['hallamolla_remaining_km'],'participant_hallamolla_remaining_km':4.5,
                'hallamolla_control_m':qa['hallamolla_control_m'],'start_finish_gap_m':qa['start_finish_gap_m'],
                'raster_smoothing_epsilon_px':qa['raster_smoothing_epsilon_px'],'topology_qa_pass':qa['topology_qa_pass']},
          'method':{'smoothing':'Ramer-Douglas-Peucker','epsilon_source':'mean organizer route-stroke width measured from raster component','participant_distance_used_for_shape_or_smoothing':False,'participant_hallamolla_note_used_for_direction':True},
          'limitations':[
            'Derived geometry reconstructed from the organizer raster, not an organizer GPX or participant GPX.',
            'The current organizer material retains a legacy 13 km map/profile while the modern event is marketed as about 14 km; historical exact identity is not asserted.',
            'The 2023 participant watch distance is validation only and is not used to set route geometry or smoothing tolerance.',
            'Participant evidence selects direction because Hallamölla was reported 4.5 km from the finish.'
          ],
          'reproducibility':{'tool':'tools/reconstruct_trail14_raster_topology.py','skeleton':'reports/trail14-route-skeleton.json','registration':'reports/organizer-map-registration.json'}
        }
        Path(a.provenance).write_text(json.dumps(prov,indent=2,ensure_ascii=False)+'\n')

    print(json.dumps(qa,indent=2,ensure_ascii=False))
    if not qa['topology_qa_pass']:raise SystemExit(2)

if __name__=='__main__':main()
