export const flowSections=['overview','statistics','gender','age-analysis','segments','history','clubs','results','method'];
export const sections=[...flowSections,'compare'];
export function urlState(url,catalog,defaultRace){
 const u=new URL(url),p=u.searchParams,key=p.get('race'),hash=decodeURIComponent(u.hash.slice(1)),requested=sections.includes(hash)?hash:p.get('section');
 return {raceKey:catalog[key]?key:defaultRace,section:sections.includes(requested)?requested:'overview',profile:p.get('result'),compare:[...new Set((p.get('compare')||'').split(',').filter(Boolean))].slice(0,5)};
}
export function switched(state,raceKey){return {...state,raceKey,profile:null,compare:[],filters:{},segment:0,page:1,query:'',globalQuery:null,sort:'overall_place',dir:1,ageGroups:[],ageHeatStat:'median',clubNames:[],segmentFrom:null,segmentTo:null,segmentMetric:'time',segmentComparison:'class',standoutTab:'finish',historyReference:null,historySegment:null};}
export function stateURL(url,state){const u=new URL(url);u.search='';u.hash='';u.searchParams.set('race',state.raceKey);if(state.section&&state.section!=='overview'){u.searchParams.set('section',state.section);u.hash=state.section;}if(state.profile)u.searchParams.set('result',state.profile);if(state.compare.length)u.searchParams.set('compare',state.compare.join(','));return u;}
export function storage(namespace,backend){return {read(key,fallback){try{const x=JSON.parse(backend.getItem(namespace+':v1:'+key));return x??fallback;}catch{return fallback;}},write(key,value){try{backend.setItem(namespace+':v1:'+key,JSON.stringify(value));}catch{}}};}

