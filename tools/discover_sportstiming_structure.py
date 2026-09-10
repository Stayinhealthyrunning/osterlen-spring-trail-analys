#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
import json, re, urllib.request

ROOT=Path(__file__).resolve().parents[1]
EVENTS=json.loads((ROOT/'data/source/sportstiming/events.json').read_text(encoding='utf-8'))['events']
OUT=ROOT/'reports/sportstiming-structure.json'
MD=ROOT/'reports/sportstiming-structure.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.forms=[]; self.selects=[]; self._form=None; self._select=None; self._option=None; self._text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='form': self._form={'attrs':a,'inputs':[]}; self.forms.append(self._form)
        elif tag=='input' and self._form is not None: self._form['inputs'].append(a)
        elif tag=='select': self._select={'attrs':a,'options':[]}; self.selects.append(self._select)
        elif tag=='option' and self._select is not None: self._option={'value':a.get('value'),'attrs':a,'text':''}; self._select['options'].append(self._option); self._text=[]
    def handle_data(self,data):
        if self._option is not None: self._text.append(data)
    def handle_endtag(self,tag):
        if tag=='form': self._form=None
        elif tag=='select': self._select=None
        elif tag=='option' and self._option is not None:
            self._option['text']=' '.join(''.join(self._text).split()); self._option=None; self._text=[]

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=15) as r: return r.read(1500000).decode('utf-8','replace')

def clean_links(links,event_id):
    out=[]
    for h in links:
        if not h or h.startswith(('#','javascript:','mailto:','tel:')): continue
        if str(event_id) in h or '/results/' in h or '/participants/' in h or 'page=' in h:
            out.append(h)
    return list(dict.fromkeys(out))[:300]

def link_patterns(links):
    patterns={}
    for h in links:
        p=re.sub(r'/results/\d+', '/results/{result_id}', h)
        p=re.sub(r'([?&]page=)\d+', r'\1{page}', p)
        patterns[p]=patterns.get(p,0)+1
    return [{'pattern':k,'count':v} for k,v in sorted(patterns.items(), key=lambda x:(-x[1],x[0]))[:30]]

def main():
    rows=[]
    for ev in EVENTS:
        url=ev['url'].rsplit('/results',1)[0]+'/app/results'
        html=fetch(url); p=P(); p.feed(html)
        links=clean_links(p.links,ev['event_id'])
        attrs=sorted(set(re.findall(r'\b(?:data-[\w-]+|ng-[\w-]+|hx-[\w-]+)=',html,re.I)))
        urls=sorted(set(re.findall(r'["\']([^"\']*(?:ajax|api|resultlist|search|json)[^"\']*)["\']',html,re.I)))[:100]
        rows.append({'year':ev['year'],'event_id':ev['event_id'],'url':url,'html_bytes':len(html.encode()),
                     'forms':p.forms,'selects':p.selects,'relevant_links':links,'link_patterns':link_patterns(links),
                     'structural_attributes':attrs,'candidate_endpoint_strings':urls})
    OUT.write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming structure discovery','', 'Public `/app/results` views are reachable without the human-verification page. This report stores form/select/link structure, not a raw HTML mirror.','']
    for r in rows:
        lines += [f"## {r['year']} (event {r['event_id']})",'',f"- HTML sampled: {r['html_bytes']} bytes",f"- Forms: {len(r['forms'])}",f"- Selects: {len(r['selects'])}",f"- Relevant links: {len(r['relevant_links'])}",'']
        for n,s in enumerate(r['selects'],1):
            vals=[f"{o.get('value')}={o.get('text')}" for o in s['options'] if o.get('text')]
            if vals: lines.append(f"- Select {n} attrs `{s.get('attrs')}`: " + '; '.join(vals[:30]))
        if r['link_patterns']:
            lines += ['','Link patterns:'] + [f"- `{p['pattern']}` × {p['count']}" for p in r['link_patterns'][:10]]
        if r['candidate_endpoint_strings']:
            lines += ['','Candidate endpoint strings:'] + [f"- `{x}`" for x in r['candidate_endpoint_strings'][:10]]
        lines.append('')
    MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
