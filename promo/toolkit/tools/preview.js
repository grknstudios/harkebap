const {chromium}=require('playwright');
const path=require('path');
const [,,dir,out,...times]=process.argv;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('console',m=>console.log('console:',m.text())); p.on('pageerror',e=>console.log('pageerror:',e.message));
await p.goto('file://'+path.resolve(dir,'index.html'));
await p.waitForFunction('window.READY===true||window.ERR',{timeout:120000});
const err=await p.evaluate('window.ERR'); if(err){console.log('ERR',err);process.exit(1);}
for(const t of times){await p.evaluate(t=>window.renderFrame(t),+t);await p.screenshot({path:`${out}/f_${t}.jpg`,type:'jpeg',quality:85});}
if(process.env.EVENTS){const e=await p.evaluate('window.getEvents()');require('fs').writeFileSync(process.env.EVENTS,JSON.stringify(e));console.log('events',e.length);}
await b.close();})();
