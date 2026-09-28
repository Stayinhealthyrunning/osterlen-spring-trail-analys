import {finished,median,finite} from './analytics.js';
export function plan(adapter,target,rows=adapter.records){
 if(!finite(target)||target<=0)return null;
 const distance=adapter.race.nominal_distance_km;
 const complete=rows.filter(r=>finished(r)&&adapter.boundary.slice(1).every((_,i)=>adapter.segment(r,i)));
 const segments=adapter.boundary.slice(1);
 if(!adapter.race.capabilities.segment_analysis)return {pace:distance>0?target/distance:null,segments:[],n:0,method:'simple'};
 if(complete.length>=5){
  const weights=segments.map((_,i)=>median(complete.map(r=>adapter.segment(r,i).seconds/r.finish_seconds)));
  const sum=weights.reduce((a,b)=>a+b,0);
  return {pace:target/distance,n:complete.length,method:'observed',segments:segments.map((cp,i)=>({name:cp.name,seconds:target*weights[i]/sum}))};
 }
 return {pace:distance>0?target/distance:null,n:complete.length,method:'distance',segments:segments.map((cp,i)=>{
 const from=adapter.boundary[i].race_distance_km,to=cp.race_distance_km;
 return {name:cp.name,seconds:finite(from)&&finite(to)&&to>from&&distance>0?target*(to-from)/distance:null};
 })};
}

