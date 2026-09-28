export class DataLoader {
  constructor(base='data/', request=fetch) { this.base=base; this.request=(...args)=>request(...args); this.cache=new Map(); this.phase='none'; }
  async json(path) {
    if (!this.cache.has(path)) this.cache.set(path,this.request(this.base+path).then(r=>{if(!r.ok)throw Error('Data kunde inte läsas. Försök igen.');return r.json();}).catch(e=>{this.cache.delete(path);throw e;}));
    return this.cache.get(path);
  }
  async bootstrap(){ this.phase='bootstrap'; const b=await this.json('bootstrap.json'); if(b.engine_contract!=='loppanalys-engine-1.0')throw Error('Okänt datakontrakt');this.boot=b; return b; }
  async checked(path){const d=await this.json(path);if(d.payload_sha256!==this.boot.payload_sha256){this.cache.delete(path);throw Error('Data har uppdaterats. Ladda om sidan för en sammanhängande version.');}return d;}
  async race(key){if(!this.boot.race_catalog[key])throw Error('Upplagan saknas');this.phase='selected-race'; const d=await this.checked('races/'+encodeURIComponent(key)+'.json');if(d.race_key!==key)throw Error('Fel loppdata'); this.phase='ready'; return d;}
  async route(race){const c=this.boot.courses[race.course_version];if(!c?.assets?.route)throw Error('Lokal rutt saknas för denna upplaga');return this.checked(c.assets.route);}
  history(){return this.checked('history.json');}
}

