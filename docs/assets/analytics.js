// Null-safe quantiles and fixed bins adapted from Ultravasan Charts (Engine U4).
export const finite=v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v));
export const numeric=values=>values.filter(finite).map(Number);
export function quantile(values,q){const a=numeric(values).sort((a,b)=>a-b);if(!a.length)return null;const i=(a.length-1)*Math.max(0,Math.min(1,q));return a[Math.floor(i)]+(a[Math.ceil(i)]-a[Math.floor(i)])*(i%1);}
export const median=values=>quantile(values,.5);
export const finished=r=>r.status==='FINISHED'&&finite(r.finish_seconds)&&r.finish_seconds>0;
export const starter=r=>['FINISHED','DNF','DSQ'].includes(r.status);
export function distribution(values){const a=numeric(values),n=a.length;return {n,median:n>=5?median(a):null,q25:n>=10?quantile(a,.25):null,q75:n>=10?quantile(a,.75):null,q10:n>=20?quantile(a,.1):null,q90:n>=20?quantile(a,.9):null};}
export function bins(values,step){if(!(step>0))throw Error('Invalid bin size');const a=numeric(values);if(!a.length)return [];const start=Math.floor(Math.min(...a)/step)*step;const b=Array.from({length:Math.floor((Math.max(...a)-start)/step)+1},(_,i)=>({from:start+i*step,to:start+(i+1)*step,count:0}));a.forEach(v=>b[Math.floor((v-start)/step)].count++);return b;}
export function summary(rows){const f=rows.filter(finished),s=rows.filter(starter);return {total:rows.length,starters:s.length,finished:f.length,dnf:rows.filter(r=>r.status==='DNF').length,unknown:rows.filter(r=>r.status==='UNKNOWN').length,median:median(f.map(r=>r.finish_seconds))};}
export function filterRows(rows,f={}){return rows.filter(r=>(!f.sex||r.sex===f.sex)&&(!f.class_name||r.class_name===f.class_name)&&(!f.status||r.status===f.status)&&(!f.club||String(r.club||'').toLocaleLowerCase('sv').includes(f.club.toLocaleLowerCase('sv'))));}
export const normalizeGroup=v=>String(v||'').trim().replace(/\s+/g,' ').toLocaleLowerCase('sv');
export function groups(rows,field){const m=new Map();for(const r of rows){if(!r[field])continue;const k=normalizeGroup(r[field]);if(!m.has(k))m.set(k,{name:r[field],rows:[]});m.get(k).rows.push(r);}return [...m.values()].map(g=>({...g,...summary(g.rows),median:g.rows.filter(finished).length>=5?median(g.rows.filter(finished).map(r=>r.finish_seconds)):null})).sort((a,b)=>b.total-a.total);}
export function comparable(a,b,courses){if(a.race_key===b.race_key)return true;if(a.race_family!==b.race_family||!a.capabilities.course_history||!b.capabilities.course_history)return false;const ac=courses[a.course_version],bc=courses[b.course_version];return Boolean(ac&&bc&&(a.course_version===b.course_version||(ac.whole_course_comparison_group&&ac.whole_course_comparison_group===bc.whole_course_comparison_group)));}
export function distanceAtTime(anchors,time){if(!anchors.length)return null;if(time<anchors[0].time)return null;let previous=anchors[0];for(const next of anchors.slice(1)){if(time<=next.time)return previous.distance+(next.distance-previous.distance)*(time-previous.time)/(next.time-previous.time);previous=next;}return previous.distance;}

