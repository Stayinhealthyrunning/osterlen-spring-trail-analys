#!/usr/bin/env python3
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import html as html_lib,json,re,urllib.request

ROOT=Path(__file__).resolve().parents[1]
EVENTS=json.loads((ROOT/'data/source/sportstiming/events.json').read_text(encoding='utf-8'))['events']
OUT=ROOT/'data/source/sportstiming/points-tracking-inventory.json'
REPORT=ROOT/'reports/sportstiming-points-tracking.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'

class TextParser(HTMLParser):
    def __init__(self):super().__init__();self.text=[];self.links=[];self.selects=[];self.sel=None;self.opt=None;self.buf=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='select':self.sel={'attrs':a,'options':[]};self.selects.append(self.sel)
        elif tag=='option' and self.sel is not None:self.opt={'value':a.get('value'),'text':''};self.sel['options'].append(self.opt);self.buf=[]
    def handle_data(self,data):
        if self.opt is not None:self.buf.append(data)
        self.text.append(data)
    def handle_endtag(self,tag):
        if tag=='option' and self.opt is not None:self.opt['text']=' '.join(''.join(self.buf).split());self.opt=None;self.buf=[]
        elif tag=='select':self.sel=None

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:return {'status':r.status,'url':r.geturl(),'html':r.read(1200000).decode('utf-8','replace')}
    except Exception as exc:return {'status':None,'url':url,'html':'','error':repr(exc)}

def summarize(kind,result):
    doc=result['html'];p=TextParser();p.feed(doc)
    text=' '.join(html_lib.unescape(' '.join(p.text)).split())
    # Preserve only candidate timing/point phrases, not the complete page or participant lists.
    phrases=[]
    for term in ['point','punkt','mellantid','mellemtid','split','start','finish','mål','bengtem','solevi','vantal','tracking']:
        for m in re.finditer(rf'(.{{0,90}}\b{re.escape(term)}\b.{{0,140}})',text,re.I):
            s=' '.join(m.group(1).split())
            if s and s not in phrases:phrases.append(s)
            if len(phrases)>=40:break
    return {'kind':kind,'http_status':result['status'],'final_url':result['url'],'html_bytes':len(doc.encode()),
            'selects':p.selects[:30],'candidate_phrases':phrases[:40],
            'relevant_links':list(dict.fromkeys([h for h in p.links if any(x in h.lower() for x in ['point','track','split','result'])]))[:100],
            'error':result.get('error')}

def main():
    editions=[]
    for ev in EVENTS:
        base=ev['url'].rsplit('/results',1)[0]
        views=[]
        for kind in ('points','tracking'):
            views.append(summarize(kind,fetch(f'{base}/app/{kind}')))
        editions.append({'year':ev['year'],'event_id':ev['event_id'],'views':views})
    OUT.write_text(json.dumps({'schema_version':1,'editions':editions},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming points/tracking inventory','', 'Public `/app/points` and `/app/tracking` views inspected without bypassing access controls.','']
    for e in editions:
        lines += [f"## {e['year']} (event {e['event_id']})",'']
        for v in e['views']:
            lines += [f"### {v['kind']}",f"- HTTP: {v['http_status']}",f"- HTML: {v['html_bytes']} bytes",f"- Selects: {len(v['selects'])}",f"- Relevant links: {len(v['relevant_links'])}"]
            if v['candidate_phrases']:
                lines.append('- Candidate text:')
                lines += [f"  - {x}" for x in v['candidate_phrases'][:10]]
            lines.append('')
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':main()
