#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import html as html_lib,json,urllib.parse,urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/sportstiming-list-table-sample.md'
URL='https://www.sportstiming.dk/event/16880/app/results?'+urllib.parse.urlencode({'round':'97077','page':1})
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0)'

class P(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.cur=None;self.stack=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='table':self.stack.append(self.cur);self.cur={'class':a.get('class'),'rows':[]}
        elif tag=='tr' and self.cur is not None:self.row=[]
        elif tag in ('td','th') and self.row is not None:self.cell=[]
    def handle_data(self,d):
        if self.cell is not None:self.cell.append(d)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:self.row.append(' '.join(html_lib.unescape(''.join(self.cell)).split()));self.cell=None
        elif tag=='tr' and self.row is not None:
            if any(self.row):self.cur['rows'].append(self.row)
            self.row=None
        elif tag=='table' and self.cur is not None:
            t=self.cur;self.cur=self.stack.pop() if self.stack else None;self.tables.append(t)

req=urllib.request.Request(URL,headers={'User-Agent':UA})
with urllib.request.urlopen(req,timeout=15) as r:doc=r.read(1200000).decode('utf-8','replace')
p=P();p.feed(doc)
lines=['# Sportstiming filtered list table sample','',f'URL: `{URL}`','']
for i,t in enumerate(p.tables,1):
    if not t['rows']:continue
    lines += [f'## Table {i} `{t["class"] or ""}`','```text']
    for row in t['rows'][:12]:lines.append(' | '.join(row))
    lines += ['```','']
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
