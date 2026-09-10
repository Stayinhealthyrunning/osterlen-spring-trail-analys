#!/usr/bin/env python3
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import html as html_lib,json,re,urllib.request

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'reports/sportstiming-result-structure.json'
OUT=ROOT/'reports/sportstiming-table-sample.json'
MD=ROOT/'reports/sportstiming-table-sample.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.stack=[]; self.current=None; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':
            self.stack.append(self.current); self.current={'class':a.get('class'),'id':a.get('id'),'rows':[]}
        elif tag=='tr' and self.current is not None: self.row=[]
        elif tag in ('td','th') and self.current is not None and self.row is not None: self.cell={'tag':tag,'class':a.get('class'),'text':[]}
    def handle_data(self,data):
        if self.cell is not None: self.cell['text'].append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.cell['text']=' '.join(html_lib.unescape(''.join(self.cell['text'])).split()); self.row.append(self.cell); self.cell=None
        elif tag=='tr' and self.row is not None and self.current is not None:
            if any(c.get('text') for c in self.row): self.current['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.current is not None:
            done=self.current; self.current=self.stack.pop() if self.stack else None; self.tables.append(done)

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=15) as r:return r.read(1000000).decode('utf-8','replace')

def main():
    base=json.loads(IN.read_text(encoding='utf-8'))
    samples=[]
    for rid in base['sample_result_ids']:
        url=f"https://www.sportstiming.dk/event/{base['event_id']}/app/results/{rid}"
        doc=fetch(url); p=TableParser(); p.feed(doc)
        useful=[]
        for t in p.tables:
            rows=[]
            for row in t['rows']:
                texts=[c['text'] for c in row]
                if any(texts): rows.append(texts)
            if rows: useful.append({'class':t['class'],'id':t['id'],'rows':rows})
        samples.append({'result_id':rid,'tables':useful})
    OUT.write_text(json.dumps({'event_id':base['event_id'],'round_id':base['round_id'],'samples':samples},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming table sample','', 'Public result detail tables sampled to establish a stable parser.','']
    for s in samples:
        lines += [f"## Result {s['result_id']}",'']
        for i,t in enumerate(s['tables'],1):
            lines.append(f"### Table {i}: `{t['class'] or ''}`")
            lines.append('```text')
            for row in t['rows']: lines.append(' | '.join(row))
            lines += ['```','']
    MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__': main()
