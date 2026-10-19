// Owned child ignores one requested SIGTERM, writes a delayed marker, then exits0.
import fs from 'node:fs';
const [folder,nonce]=process.argv.slice(2);let stopped=false;
const hard=setTimeout(()=>process.exit(72),3000);
process.on('SIGTERM',()=>{
 if(stopped)return;stopped=true;
 fs.writeFileSync(folder+'/term.json',JSON.stringify({pid:process.pid,nonce,signal:'SIGTERM'}),{flag:'wx'});
 setTimeout(()=>{
  const bytes=Buffer.alloc(1024,0xa5);
  for(let y=0;y<3;y++)for(let x=0;x<5;x++)for(let c=0;c<4;c++)bytes[y*32+x*4+c]=(x*13+y*7+c*31)&255;
  fs.writeFileSync(folder+'/marker.raw',bytes,{flag:'wx'});
  fs.writeFileSync(folder+'/done.json',JSON.stringify({pid:process.pid,nonce,intended_exit:0}),{flag:'wx'});
  clearTimeout(hard);process.exit(0);
 },250);
});
process.stdout.write(JSON.stringify({owned_child_pid:process.pid,nonce})+'\n',()=>fs.writeFileSync(folder+'/ready.json',JSON.stringify({pid:process.pid,ppid:process.ppid,nonce}),{flag:'wx'}));
