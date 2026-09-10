#!/usr/bin/env python3
from pathlib import Path
import json,re,urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/sportstiming-client-structure.json'
MD=ROOT/'reports/sportstiming-client-structure.md'
URL='https://www.sportstiming.dk/js/resultlist.js?2.0'
UA='Mozilla/5.0 (compatible; OST-analysis-research/1.0)'
req=urllib.request.Request(URL,headers={'User-Agent':UA})
with urllib.request.urlopen(req,timeout=15) as r:
    js=r.read(1000000).decode('utf-8','replace')

# Extract only request/config-relevant snippets, not a redistributed copy of the script.
interesting=[]
for pattern in [r'\$\.ajax\s*\(\s*\{.*?\}\s*\)',r'function\s+ResultListDoSearch\s*\([^)]*\)\s*\{.*?\n\}',r'\.selectDistance.*?(?:\n|;)',r'\.selectGender.*?(?:\n|;)',r'\.selectCategory.*?(?:\n|;)',r'\.selectCountry.*?(?:\n|;)']:
    for m in re.finditer(pattern,js,re.I|re.S):
        text=' '.join(m.group(0).split())
        if len(text)>1400: text=text[:1400]+'…'
        if text not in interesting: interesting.append(text)

strings=[]
for s in re.findall(r'["\']([^"\']{1,220})["\']',js):
    low=s.lower()
    if any(k in low for k in ['result','search','distance','gender','category','country','page','ajax','participant']):
        strings.append(s)
strings=list(dict.fromkeys(strings))[:120]
payload={'source_url':URL,'bytes':len(js.encode()),'request_related_snippets':interesting[:50],'relevant_string_literals':strings}
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Sportstiming client request structure','',f'Source inspected: `{URL}`','',f'JavaScript size: {payload["bytes"]} bytes','', 'Only request/configuration snippets are retained; the complete third-party script is not mirrored.','', '## Request-related snippets','']
for x in payload['request_related_snippets']: lines.append(f'- `{x}`')
lines+=['','## Relevant string literals','']
for x in strings: lines.append(f'- `{x}`')
MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
