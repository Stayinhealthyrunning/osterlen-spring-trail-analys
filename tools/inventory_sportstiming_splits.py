#!/usr/bin/env python3
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import html as html_lib,json,re,urllib.parse,urllib.request

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/source/sportstiming/class-catalog.json'
OUT=ROOT/'data/source/sportstiming/split-inventory.json'
REPORT=ROOT/'reports/sportstiming-split-inventory.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.current=None;self.row=None;self.cell=None;self._stack=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':self._stack.append(self.current);self.current={'class':a.get('class',''),'rows':[]}
        elif tag=='tr' and self.current is not None:self.row=[]
        elif tag in ('td','th') and self.current is not None and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(html_lib.unescape(''.join(self.cell)).split()));self.cell=None
        elif tag=='tr' and self.row is not None and self.current is not None:
            if any(self.row):self.current['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.current is not None:
            t=self.current;self.current=self._stack.pop() if self._stack else None;self.tables.append(t)

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=15) as r:return r.read(1200000).decode('utf-8','replace')

def result_ids(html,event):
    return list(dict.fromkeys(re.findall(rf'/event/{event}/app/results/(\d+)',html)))

def split_table(doc):
    p=TableParser();p.feed(doc)
    for t in p.tables:
        if 'splits-table' in t['class']:return t['rows']
    return []

def normalize_split_schema(rows):
    if not rows:return {'has_split_table':False,'rows':[]}
    data=[]
    for row in rows:
        if not row:continue
        first=row[0].strip()
        # Header rows are kept separately; race passage rows normally begin with distance/label.
        if first and first not in {'Distans',''} and not ('Mellantid' in ' '.join(row) and 'Total tid' in ' '.join(row)):
            data.append({'label':first,'cells':row})
    return {'has_split_table':True,'rows':data,'raw_row_count':len(rows)}

def main():
    cat=json.loads(CAT.read_text(encoding='utf-8'))
    inventory=[]
    for edition in cat['editions']:
        event=edition['event_id']
        for cls in edition['classes']:
            fam=cls.get('race_family')
            if not fam:continue
            rid=cls['sportstiming_distance_id']
            url=f'https://www.sportstiming.dk/event/{event}/app/results?'+urllib.parse.urlencode({'round':rid,'page':1})
            try:
                page=fetch(url); ids=result_ids(page,event)
                detail_id=ids[0] if ids else None
                schema={'has_split_table':False,'rows':[]}
                if detail_id:
                    schema=normalize_split_schema(split_table(fetch(f'https://www.sportstiming.dk/event/{event}/app/results/{detail_id}')))
                pages=[int(x) for x in re.findall(r'[?&]page=(\d+)',page)]
                inventory.append({'year':edition['year'],'event_id':event,'race_family':fam,'sportstiming_distance_id':rid,
                                  'source_label':cls['source_label'],'first_page_result_links':len(ids),'max_pagination_link':max(pages) if pages else 1,
                                  'sample_result_id':detail_id,**schema})
            except Exception as exc:
                inventory.append({'year':edition['year'],'event_id':event,'race_family':fam,'sportstiming_distance_id':rid,
                                  'source_label':cls['source_label'],'error':repr(exc)})
    payload={'schema_version':1,'method':'First filtered result sampled for each Sportstiming distance ID. Presence/labels establish source split schema; they do not prove 100% split coverage for all runners.','inventory':inventory}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming split inventory','',payload['method'],'','| Year | Race | Source class | First-page links | Sample split rows |','|---:|---|---|---:|---|']
    for x in inventory:
        labels=', '.join(r['label'] for r in x.get('rows',[])) or ('ERROR' if x.get('error') else 'none')
        lines.append(f"| {x['year']} | `{x['race_family']}` | {x['source_label']} | {x.get('first_page_result_links','–')} | {labels} |")
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':main()
