import {finite,finished,distribution,median} from './analytics.js';
export function adapt(doc,boot){
 const race=doc.race,records=race.records,byId=new Map(records.map(r=>[String(r.source_result_id),r]));
 const checkpoints=doc.checkpoints.slice().sort((a,b)=>a.sequence_no-b.sequence_no),boundary=checkpoints.filter(c=>c.analysis_boundary);
 const splits=new Map();for(const s of doc.splits){const key=String(s.source_result_id);if(!splits.has(key))splits.set(key,[]);splits.get(key).push(s);}
 const passages=r=>(splits.get(String(r.source_result_id))||[]).slice().sort((a,b)=>checkpoints.findIndex(c=>c.key===a.checkpoint)-checkpoints.findIndex(c=>c.key===b.checkpoint));
 function observation(r,key){
  if(key==='start')return r.status==='DNS'||r.status==='UNKNOWN'?null:{elapsed_seconds:0,place_overall:null,calculated:true};
  const found=passages(r).find(s=>s.checkpoint===key);
  if(key==='finish'&&!finished(r))return null;
  if(found)return found;
  return key==='finish'&&finished(r)?{elapsed_seconds:r.finish_seconds,place_overall:r.overall_place,from_result:true}:null;
 }
 function segment(r,i){const a=boundary[i],b=boundary[i+1],from=observation(r,a.key),to=observation(r,b.key);
  if(!from||!to||to.elapsed_seconds<=from.elapsed_seconds)return null;
  const km=finite(a.race_distance_km)&&finite(b.race_distance_km)?b.race_distance_km-a.race_distance_km:null;
  return {seconds:to.elapsed_seconds-from.elapsed_seconds,km,pace:km>0?(to.elapsed_seconds-from.elapsed_seconds)/km:null,gain:finite(from.place_overall)&&finite(to.place_overall)?from.place_overall-to.place_overall:null};
 }
 function segmentStats(rows){
  const complete=rows.filter(r=>finished(r)&&boundary.slice(1).every(c=>observation(r,c.key)));
  return boundary.slice(1).map((cp,i)=>{
   const values=complete.map(r=>({r,s:segment(r,i)})).filter(x=>x.s);
   const paces=values.map(x=>x.s.pace);
   const retention=values.filter(x=>x.s.pace>0).map(x=>100*(x.r.finish_seconds/race.nominal_distance_km)/x.s.pace);
   return {from:boundary[i],to:cp,...distribution(paces),time:distribution(values.map(x=>x.s.seconds)),gain:median(values.map(x=>x.s.gain)),retention:retention.length>=5?median(retention):null,
    dnf:rows.filter(r=>r.status==='DNF'&&passages(r).at(-1)?.checkpoint===boundary[i].key).length,complete:complete.length};
  });
 }
 return {race,records,byId,checkpoints,boundary,passages,observation,segment,segmentStats,
  course:boot.courses[race.course_version]||null,
  members:r=>doc.team_members.filter(m=>String(m.team_source_result_id)===String(r.source_result_id)).sort((a,b)=>a.source_sequence-b.source_sequence),
  anchors(r,route){if(!race.capabilities.replay||race.course_version!==route.course_version)return [];let last=-1;return checkpoints.filter(c=>c.replay_anchor).map(c=>{const o=observation(r,c.key),distance=route.anchors[c.key];return o&&finite(distance)?{time:o.elapsed_seconds,distance}:null;}).filter(a=>{if(!a||a.time<=last)return false;last=a.time;return true;});}
 };
}

