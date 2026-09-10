#!/usr/bin/env python3
"""Build the modern ÖST race-edition catalog from curated official-program facts.

This catalog deliberately leaves `course_version` and `timing_split_status` unresolved
until geometric and Sportstiming evidence exists. It is a staging contract for the
future generic analysis engine, not a substitute for official result data.
"""
from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'config/race-catalog.json'

YEARS={
  2018:{'event_id':4950,'first':'2018-04-14','second':'2018-04-15','host':'dk',
        'names':{'ultra60':'Simris Alg Ultra 60km+','trail22':'Verkeån trail 21km+','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 13 km'},
        'times':{'ultra60':'10:00','trail22':'11:00','trail5':'10:45','trail14':'12:30'}},
  2019:{'event_id':5719,'first':'2019-04-13','second':'2019-04-14','host':'dk',
        'names':{'ultra60':'Simris Alg Ultra 60km+','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Verkeån trail 21km+','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 13 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'10:45','trail14':'12:30'}},
  2022:{'event_id':9587,'first':'2022-04-09','second':'2022-04-10','host':'dk',
        'names':{'ultra60':'Ultra 60km+','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Teleservice trail 21km+','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 13 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'11:00','trail14':'12:30'}},
  2023:{'event_id':11274,'first':'2023-04-15','second':'2023-04-16','host':'dk',
        'names':{'ultra60':'Ultra 60km+','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Fogarolli trail 21km+','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 13 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'11:00','trail14':'12:30'}},
  2024:{'event_id':12349,'first':'2024-04-13','second':'2024-04-14','host':'se',
        'names':{'ultra60':'60 k ÖST ultra med COROS','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Fogarolli trail 21km+','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 14 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'11:00','trail14':'12:30'}},
  2025:{'event_id':15015,'first':'2025-04-12','second':'2025-04-13','host':'se',
        'names':{'ultra60':'CRAFT Ultra 60 k','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Fogarolli trail 22 K','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 14 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'11:00','trail14':'12:30'}},
  2026:{'event_id':16880,'first':'2026-04-18','second':'2026-04-19','host':'dk',
        'names':{'ultra60':'CRAFT Ultra 60 k','duo60':'Duo Trail (relay 2 x 30 km)','trail22':'Fogarolli trail 22 K','trail5':'Naturloppet 5km+','trail14':'Ekopark trail 14 km'},
        'times':{'ultra60':'10:00','duo60':'10:00','trail22':'11:00','trail5':'11:00','trail14':'12:30'}},
}

TRACE_IDS={
  'ultra60':{2018:43970,2019:69381,2022:172147,2023:203147,2024:251126,2025:272846,2026:322315},
  'trail22':{2018:7897,2019:69864,2022:165617,2023:203146,2024:237224,2025:280053,2026:322314},
}
CANONICAL={'ultra60':60,'duo60':60,'trail22':22,'trail14':14,'trail5':5}
HISTORIC={
  **{('trail22',y):21 for y in (2018,2019,2022,2023,2024)},
  **{('trail22',y):22 for y in (2025,2026)},
  **{('trail14',y):13 for y in (2018,2019,2022,2023)},
  **{('trail14',y):14 for y in (2024,2025,2026)},
}
PM_2026={
  'ultra60':'https://www.osterlentrail.se/race-pm-60km.html',
  'duo60':'https://www.osterlentrail.se/loumlpar-pm-duo-trail.html',
  'trail22':'https://www.osterlentrail.se/race-pm-22km.html',
  'trail14':'https://www.osterlentrail.se/race-pm-14km.html',
  'trail5':'https://www.osterlentrail.se/race-pm-5km.html',
}

def main():
    races=[]
    for year,meta in YEARS.items():
        for family in ('ultra60','duo60','trail22','trail14','trail5'):
            if family not in meta['names']: continue
            long_day=family in {'ultra60','duo60','trail22'}
            race={
              'race_key':f'ost-{year}-{family}',
              'event_key':'osterlen-spring-trail',
              'year':year,
              'race_family':family,
              'race_type':'relay' if family=='duo60' else 'individual',
              'source_event_key':str(meta['event_id']),
              'sportstiming_event_id':meta['event_id'],
              'source_race_name':meta['names'][family],
              'race_date':meta['first'] if long_day else meta['second'],
              'scheduled_start_local':meta['times'][family],
              'timezone':'Europe/Stockholm',
              'nominal_distance_km':HISTORIC.get((family,year),CANONICAL[family]),
              'canonical_family_distance_km':CANONICAL[family],
              'course_version':None,
              'route_family_ref':'ultra60' if family=='duo60' else family,
              'trace_id':TRACE_IDS.get(family,{}).get(year),
              'data_status':'source_catalogued',
              'timing_split_status':'unknown',
              'schedule_status':'verified_program',
              'source_urls':[
                f"https://www.sportstiming.{meta['host']}/event/{meta['event_id']}",
                'https://www.osterlentrail.se/resultat.html',
              ],
            }
            if year==2026: race['source_urls'].append(PM_2026[family])
            if family=='duo60':
                race.update({'route_race_key':f'ost-{year}-ultra60','relay_legs':2,'exchange_name':'Bengtemölla'})
            races.append(race)
    payload={
      'schema_version':1,
      'status':'pre_engine_source_catalog',
      'facts_basis':'Curated from public Sportstiming event roots, official ÖST result archive and race PMs.',
      'rules':[
        'course_version remains null until explicit GPX review',
        'timing_split_status remains unknown until Sportstiming split data is verified',
        'Duo reuses the same-year Ultra 60 geometry',
        'The source race label is preserved separately from the normalized race family',
      ],
      'races':races,
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {OUT.relative_to(ROOT)}: {len(races)} race editions')

if __name__=='__main__': main()
