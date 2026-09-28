export const sections=['overview','results','dynamics','segments','course','compare','history','method'];
export function urlState(url,catalog,defaultRace){
 const p=new URL(url).searchParams; const key=p.get('race');
 return {raceKey:catalog[key]?key:defaultRace,section:sections.includes(p.get('section'))?p.get('section'):'overview',profile:p.get('result'),compare:[...new Set((p.get('compare')||'').split(',').filter(Boolean))].slice(0,5)};
}
export function switched(state,raceKey){return {...state,raceKey,profile:null,compare:[],filters:{},segment:0,page:1,query:'',globalQuery:null,sort:'overall_place',dir:1};}
export function stateURL(url,state){const u=new URL(url);u.search='';u.searchParams.set('race',state.raceKey);u.searchParams.set('section',state.section);if(state.profile)u.searchParams.set('result',state.profile);if(state.compare.length)u.searchParams.set('compare',state.compare.join(','));return u;}
export function storage(namespace,backend){return {read(key,fallback){try{const x=JSON.parse(backend.getItem(namespace+':v1:'+key));return x??fallback;}catch{return fallback;}},write(key,value){try{backend.setItem(namespace+':v1:'+key,JSON.stringify(value));}catch{}}};}

