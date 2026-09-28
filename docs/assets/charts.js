import {bins,finite} from './analytics.js';
export const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function time(v){if(!finite(v))return '–';const n=Math.round(Math.abs(v));return (v<0?'−':'')+Math.floor(n/3600)+':'+String(Math.floor(n%3600/60)).padStart(2,'0')+':'+String(n%60).padStart(2,'0');}
export function pace(v,unit='pace'){if(!finite(v)||v<=0)return '–';if(unit==='speed')return (3600/v).toFixed(1).replace('.',',')+' km/h';const n=Math.round(v);return Math.floor(n/60)+':'+String(n%60).padStart(2,'0')+' min/km';}
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

