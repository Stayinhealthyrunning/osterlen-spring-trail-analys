import {finished,median,finite} from './analytics.js';
export function plan(adapter,target,rows=adapter.records){
 if(!finite(target)||target<=0)return null;
 const distance=Number(adapter.race.nominal_distance_km),complete=rows.filter(r=>finished(r)&&adapter.boundary.slice(1).every((_,i)=>adapter.segment(r,i))),boundaries=adapter.boundary,segments=boundaries.slice(1);
 if(!adapter.race.capabilities.segment_analysis)return {pace:distance>0?target/distance:null,segments:[],n:0,method:'simple',targetSeconds:target,distanceKm:distance};
 const geometry=segments.map((cp,i)=>{const from=boundaries[i],km=finite(from.race_distance_km)&&finite(cp.race_distance_km)&&Number(cp.race_distance_km)>Number(from.race_distance_km)?Number(cp.race_distance_km)-Number(from.race_distance_km):null;return {name:cp.name,from:from.name,to:cp.name,distanceKm:km};});
 let weights,method;
 if(complete.length>=5){weights=segments.map((_,i)=>median(complete.map(r=>adapter.segment(r,i).seconds/r.finish_seconds)));method='observed';}
 else {weights=geometry.map(s=>finite(s.distanceKm)&&distance>0?s.distanceKm/distance:null);method='distance';}
 if(weights.some(v=>!finite(v)||v<=0))return {pace:distance>0?target/distance:null,n:complete.length,method,segments:[],targetSeconds:target,distanceKm:distance};
 const sum=weights.reduce((a,b)=>a+Number(b),0);let cumulativeSeconds=0,cumulativeDistanceKm=0;
 const planned=geometry.map((segment,i)=>{const seconds=target*Number(weights[i])/sum;cumulativeSeconds+=seconds;if(finite(segment.distanceKm))cumulativeDistanceKm+=Number(segment.distanceKm);return {...segment,seconds,cumulativeSeconds,cumulativeDistanceKm:finite(segment.distanceKm)?cumulativeDistanceKm:null,paceSecondsKm:finite(segment.distanceKm)&&segment.distanceKm>0?seconds/segment.distanceKm:null};});
 return {pace:distance>0?target/distance:null,n:complete.length,method,segments:planned,targetSeconds:target,distanceKm:distance};
}
