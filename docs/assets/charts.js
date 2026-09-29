import {bins,finite} from './analytics.js';
export const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function time(v){if(!finite(v))return '–';const n=Math.round(Math.abs(v));return (v<0?'−':'')+Math.floor(n/3600)+':'+String(Math.floor(n%3600/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');}
export function pace(v,unit='pace'){if(!finite(v)||v<=0)return '–';if(unit==='speed')return (3600/v).toFixed(1).replace('.',',')+' km/h';const n=Math.round(v);return Math.floor(n/60)+':'+String(n%60).padStart(2,'0')+' min/km';}
export const statusLabel=s=>({FINISHED:'Fullföljt',DNF:'DNF',DNS:'Startade inte',DSQ:'Diskvalificerad',UNKNOWN:'Okänd status'}[s]||String(s??'–'));
export const empty=t=>'<p class="empty">'+esc(t)+'</p>';
export const table=(heads,rows)=>'<div class="table-scroll"><table><thead><tr>'+heads.map(h=>'<th scope="col">'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';
export const tr=values=>'<tr>'+values.map(v=>'<td>'+v+'</td>').join('')+'</tr>';
export function info(id,text){return '<button class="info" aria-label="Metod" aria-controls="'+id+'" aria-describedby="'+id+'" aria-expanded="false" data-info="'+id+'">i</button><p class="tip" id="'+id+'" hidden>'+esc(text)+'</p>';}
const svg=(body,label,h=280)=>'<div class="chart-scroll"><svg class="chart" viewBox="0 0 740 '+h+'" role="img" aria-label="'+esc(label)+'">'+body+'</svg></div>';
export function histogram(values,step){
 const b=bins(values,step);if(!b.length)return empty('Inga publicerade måltider i urvalet.');
 const peak=Math.max(...b.map(x=>x.count),1),left=55,right=705,bottom=235,w=(right-left)/b.length;
 let s='';for(let i=0;i<=4;i++){const y=bottom-i*48;s+='<line class="axis" x1="'+left+'" x2="'+right+'" y1="'+y+'" y2="'+y+'"/><text x="43" y="'+(y+4)+'" text-anchor="end">'+Math.round(peak*i/4)+'</text>';}
 b.forEach((x,i)=>{const h=x.count/peak*192,xp=left+i*w+w*.12;s+='<rect tabindex="0" class="bar" x="'+xp+'" y="'+(bottom-h)+'" width="'+(w*.76)+'" height="'+h+'" rx="2" aria-label="'+x.count+' resultat, '+time(x.from)+' till '+time(x.to)+'"><title>'+x.count+' resultat · '+time(x.from)+'–'+time(x.to)+'</title></rect>';if(i%Math.max(1,Math.ceil(b.length/6))===0)s+='<text x="'+(left+(i+.5)*w)+'" y="263" text-anchor="middle">'+time(x.from).slice(0,-3)+'</text>';});
 return svg(s,'Fördelning av måltider');
}
export function sexHistogram(rows,step){
 const finished=rows.filter(r=>finite(r.finish_seconds)&&r.finish_seconds>0),values=finished.map(r=>r.finish_seconds),b=bins(values,step);
 if(!b.length)return empty('Inga publicerade måltider i urvalet.');
 const sexes=[...new Set(finished.map(r=>r.sex).filter(s=>s==='F'||s==='M'))],split=sexes.length===2;
 const count=(from,to,sex=null)=>finished.filter(r=>r.finish_seconds>=from&&r.finish_seconds<to&&(!sex||r.sex===sex)).length;
 const peak=Math.max(...b.map(x=>count(x.from,x.to)),1),left=55,right=705,bottom=235,w=(right-left)/b.length;
 let s='';for(let i=0;i<=4;i++){const y=bottom-i*48;s+='<line class="axis" x1="'+left+'" x2="'+right+'" y1="'+y+'" y2="'+y+'"/><text x="43" y="'+(y+4)+'" text-anchor="end">'+Math.round(peak*i/4)+'</text>';}
 b.forEach((x,i)=>{const total=count(x.from,x.to),xp=left+i*w+w*.1,totalH=total/peak*192;
  if(split){const fw=w*.31,mw=w*.31,fh=count(x.from,x.to,'F')/peak*192,mh=count(x.from,x.to,'M')/peak*192;s+='<rect class="bar-total" x="'+xp+'" y="'+(bottom-totalH)+'" width="'+(w*.8)+'" height="'+totalH+'" rx="3"><title>Totalt '+total+' · '+time(x.from)+'–'+time(x.to)+'</title></rect><rect tabindex="0" data-series="female" class="bar-female" x="'+(xp+w*.08)+'" y="'+(bottom-fh)+'" width="'+fw+'" height="'+fh+'" rx="2"><title>Kvinnor '+count(x.from,x.to,'F')+' · '+time(x.from)+'–'+time(x.to)+'</title></rect><rect tabindex="0" data-series="male" class="bar-male" x="'+(xp+w*.43)+'" y="'+(bottom-mh)+'" width="'+mw+'" height="'+mh+'" rx="2"><title>Män '+count(x.from,x.to,'M')+' · '+time(x.from)+'–'+time(x.to)+'</title></rect>';}
  else {const sex=sexes[0],cls=sex==='F'?'bar-female':sex==='M'?'bar-male':'bar';s+='<rect tabindex="0" class="'+cls+'" x="'+xp+'" y="'+(bottom-totalH)+'" width="'+(w*.8)+'" height="'+totalH+'" rx="2"><title>'+total+' resultat · '+time(x.from)+'–'+time(x.to)+'</title></rect>';}
  if(i%Math.max(1,Math.ceil(b.length/6))===0)s+='<text x="'+(left+(i+.5)*w)+'" y="263" text-anchor="middle">'+time(x.from).slice(0,-3)+'</text>';
 });
 const legend=split?'<div class="series-controls" aria-label="Visa sluttidsserier"><label><input type="checkbox" data-series-toggle="female" checked> <i class="female"></i>Kvinnor ('+finished.filter(r=>r.sex==='F').length+')</label><label><input type="checkbox" data-series-toggle="male" checked> <i class="male"></i>Män ('+finished.filter(r=>r.sex==='M').length+')</label><span class="legend-total"><i class="total"></i>Totalt</span></div>':'';
 return split?'<div class="interactive-chart finish-interactive">'+legend+svg(s,'Fördelning av måltider totalt, kvinnor och män')+'</div>':svg(s,'Fördelning av måltider');
}

export function finishPlaceScatter(rows){
 const points=rows.filter(r=>finite(r.finish_seconds)&&r.finish_seconds>0&&finite(r.overall_place)&&r.overall_place>0);
 if(points.length<2)return empty('För få fullföljare med publicerad totalplacering.');
 const min=Math.min(...points.map(r=>Number(r.finish_seconds))),max=Math.max(...points.map(r=>Number(r.finish_seconds))),maxPlace=Math.max(...points.map(r=>Number(r.overall_place))),left=70,right=700,top=28,bottom=235;
 const x=v=>left+(Number(v)-min)/(max-min||1)*(right-left),y=v=>top+(Number(v)-1)/(Math.max(1,maxPlace-1))*(bottom-top);
 let s='';
 for(let i=0;i<=4;i++){const value=min+(max-min)*i/4,xx=left+(right-left)*i/4;s+='<line class="axis" x1="'+xx+'" x2="'+xx+'" y1="'+top+'" y2="'+bottom+'"/><text x="'+xx+'" y="264" text-anchor="middle">'+time(value).slice(0,-3)+'</text>';}
 for(let i=0;i<=4;i++){const place=Math.max(1,Math.round(1+(maxPlace-1)*i/4)),yy=y(place);s+='<line class="axis" x1="'+left+'" x2="'+right+'" y1="'+yy+'" y2="'+yy+'"/><text x="58" y="'+(yy+4)+'" text-anchor="end">'+place+'</text>';}
 for(const r of points){const key=r.sex==='F'?'female':r.sex==='M'?'male':'unknown',cls=r.sex==='F'?'point-female':r.sex==='M'?'point-male':'point-total',label=esc((r.name||'Resultat')+' · '+time(r.finish_seconds)+' · plats '+r.overall_place);s+='<circle tabindex="0" role="button" data-result="'+esc(r.source_result_id)+'" data-series="'+key+'" class="scatter-point '+cls+'" cx="'+x(r.finish_seconds).toFixed(2)+'" cy="'+y(r.overall_place).toFixed(2)+'" r="4.2" aria-label="Öppna '+label+'"><title>'+label+'</title></circle>';}
 const hasF=points.some(r=>r.sex==='F'),hasM=points.some(r=>r.sex==='M'),hasUnknown=points.some(r=>r.sex!=='F'&&r.sex!=='M'),controls=[hasF?'<label><input type="checkbox" data-series-toggle="female" checked> <i class="female"></i>Kvinnor</label>':'',hasM?'<label><input type="checkbox" data-series-toggle="male" checked> <i class="male"></i>Män</label>':'',hasUnknown?'<label><input type="checkbox" data-series-toggle="unknown" checked> <i class="total"></i>Okänt kön</label>':''].filter(Boolean).join('');
 return '<div class="interactive-chart scatter-interactive">'+(controls?'<div class="series-controls" aria-label="Visa placeringsserier">'+controls+'</div>':'')+svg(s,'Sluttid mot totalplacering')+'</div>';
}
export function bands(stats,unit){
 const format=v=>unit==='time'?time(v):pace(v,unit);
 const values=stats.flatMap(s=>[s.q10,s.q25,s.median,s.q75,s.q90]).filter(finite);if(!values.length)return empty('För få kompletta passager för segmentmedian. Minst fem krävs.');
 const lo=Math.min(...values)*.9,hi=Math.max(...values)*1.08,y=v=>235-(v-lo)/(hi-lo||1)*190,x=i=>105+i*520/Math.max(1,stats.length-1);let s='';
 for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;s+='<line class="axis" x1="92" x2="692" y1="'+y(v)+'" y2="'+y(v)+'"/><text x="85" y="'+(y(v)+4)+'" text-anchor="end">'+esc(format(v).split(' ')[0])+'</text>';}
 stats.forEach((d,i)=>{const xx=x(i);if(finite(d.q10))s+='<line class="outer" x1="'+xx+'" x2="'+xx+'" y1="'+y(d.q10)+'" y2="'+y(d.q90)+'"/>';if(finite(d.q25))s+='<rect class="band" x="'+(xx-25)+'" width="50" y="'+y(d.q75)+'" height="'+(y(d.q25)-y(d.q75))+'"/>';if(finite(d.median))s+='<circle class="dot" cx="'+xx+'" cy="'+y(d.median)+'" r="6"/>';s+='<text x="'+xx+'" y="263" text-anchor="middle">'+(i+1)+'</text><rect class="hit" x="'+(xx-45)+'" y="25" width="90" height="220" data-segment="'+i+'" tabindex="0" role="button" aria-label="Delsträcka '+(i+1)+', n='+d.n+', median '+esc(format(d.median))+'"><title>'+esc(d.to.name)+' · n='+d.n+' · '+esc(format(d.median))+'</title></rect>';});
 return svg(s,'Median och spridning per delsträcka');
}
export function elevation(profile,anchors,selected=null){
 if(!profile?.some(p=>finite(p[1])))return empty('GPX-filen saknar höjdvärden för ruttpunkterna. Ingen höjdprofil har skapats.');
 const maxD=profile.at(-1)[0],lo=Math.min(...profile.map(p=>p[1]).filter(finite)),hi=Math.max(...profile.map(p=>p[1]).filter(finite)),x=d=>55+d/maxD*640,y=h=>200-(h-lo)/(hi-lo||1)*155;
 let path='',open=false;for(const p of profile){if(!finite(p[1])){open=false;continue;}path+=(open?'L':'M')+x(p[0])+','+y(p[1])+' ';open=true;}
 let s='<path class="line" d="'+path+'"/>';
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4;s+='<text x="48" y="'+(y(v)+4)+'" text-anchor="end">'+Math.round(v)+' m</text>';}
 Object.entries(anchors||{}).forEach(([key,d])=>{s+='<line class="axis" x1="'+x(d)+'" x2="'+x(d)+'" y1="30" y2="205"/><text x="'+x(d)+'" y="230" text-anchor="'+(d===0?'start':d===maxD?'end':'middle')+'">'+d.toFixed(1)+' km</text>';});
 if(selected&&finite(selected[0])&&finite(selected[1]))s+='<rect class="band" x="'+x(selected[0])+'" y="20" width="'+(x(selected[1])-x(selected[0]))+'" height="190"/>';
 return svg(s,'Höjdprofil längs aktuell rutt',250);
}

