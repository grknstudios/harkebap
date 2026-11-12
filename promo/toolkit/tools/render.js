const {chromium}=require('playwright');const {spawn}=require('child_process');const path=require('path');
const [,,dir,start,end,out]=process.argv;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+path.resolve(dir,'index.html'));await p.waitForFunction('window.READY===true||window.ERR',{timeout:120000});
const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-r','30',out],{stdio:['pipe','ignore','inherit']});
for(let f=+start;f<+end;f++){await p.evaluate(t=>window.renderFrame(t),f/30);const buf=await p.screenshot({type:'jpeg',quality:93});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(f%300===0)console.log(out,f);}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();})();
