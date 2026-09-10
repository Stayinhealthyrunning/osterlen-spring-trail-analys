#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import html as html_lib
import json,re,urllib.parse,urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/sportstiming-result-structure.json'
MD=ROOT/'reports/sportstiming-result-structure.md'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0; +https://github.com/Stayinhealthyrunning/osterlen-spring-trail-analys)'
EVENT=16880
ROUND=97077
BASE=f'https://www.sportstiming.dk/event/{EVENT}/app/results'

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=15) as r:
        return r.read(1500000).decode('utf-8','replace')

def clean_text(s): return ' '.join(html_lib.unescape(re.sub(r'<[^>]+>',' ',s)).split())

def list_ids(page_html):
    ids=[]
    for m in re.finditer(rf'/event/{EVENT}/app/results/(\d+)',page_html):
        x=m.group(1)
        if x not in ids: ids.append(x)
    return ids

def structural_tokens(doc):
    tags=[]
    for m in re.finditer(r'<(table|thead|tbody|tr|th|td|dl|dt|dd|h[1-6]|div|span)\b([^>]*)>',doc,re.I):
        tag=m.group(1).lower(); attrs=m.group(2)
        cls=re.search(r'class=["\']([^"\']+)',attrs,re.I)
        ident=re.search(r'id=["\']([^"\']+)',attrs,re.I)
        token={'tag':tag}
        if cls: token['class']=cls.group(1)
        if ident: token['id']=ident.group(1)
        if len(token)>1 and token not in tags: tags.append(token)
    return tags[:200]

def label_candidates(doc):
    # Store labels/headings only when values can be separated; redact runner-specific visible values.
    out=[]
    for pat in [r'<th\b[^>]*>(.*?)</th>',r'<dt\b[^>]*>(.*?)</dt>',r'<label\b[^>]*>(.*?)</label>',r'<h[1-6]\b[^>]*>(.*?)</h[1-6]>']:
        for x in re.findall(pat,doc,re.I|re.S):
            t=clean_text(x)
            if t and len(t)<120 and t not in out: out.append(t)
    return out[:150]

def main():
    url=BASE+'?'+urllib.parse.urlencode({'round':ROUND,'page':1})
    page=fetch(url)
    ids=list_ids(page)
    details=[]
    for rid in ids[:3]:
        doc=fetch(f'{BASE}/{rid}')
        details.append({'result_id':rid,'html_bytes':len(doc.encode()),'labels':label_candidates(doc),'structural_tokens':structural_tokens(doc),
                        'contains_split_words':any(x in doc.lower() for x in ['mellemtid','mellantid','split','lap','varv']),
                        'links_to_tracking':('/tracking' in doc.lower()),'links_to_points':('/points' in doc.lower())})
    payload={'event_id':EVENT,'round_id':ROUND,'list_url':url,'list_html_bytes':len(page.encode()),'result_links_on_page':len(ids),'sample_result_ids':ids[:3],'details':details}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Sportstiming result structure sample','',f'- Event: {EVENT}',f'- Round: {ROUND}',f'- Result links found on page: {len(ids)}','', 'Runner-specific values are intentionally not mirrored in this structural diagnostic.','']
    for d in details:
        lines += [f"## Result id {d['result_id']}",'',f"- HTML: {d['html_bytes']} bytes",f"- Split-related words present: {d['contains_split_words']}",f"- Tracking link: {d['links_to_tracking']}",f"- Points link: {d['links_to_points']}",'','Labels/headings:']
        lines += [f'- {x}' for x in d['labels']]
        lines.append('')
    MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
