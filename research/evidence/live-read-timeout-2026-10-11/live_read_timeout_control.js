const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {LiveWasmHost}=require(process.argv[2]);const out=process.argv[3],fixed=process.argv[4]==='fixed';
const section=(id,v)=>[id,v.length,...v],name=s=>[s.length,...Buffer.from(s)];
function moduleBytes(hang){
 const bodies=[[0,0x41,0x80,0x80,1,0x0b],hang?[0,0x23,0,0x41,1,0x6a,0x24,0,0x23,0,0x41,2,0x4b,0x04,0x40,0x03,0x40,0x0c,0,0x0b,0x0b,0x41,0,0x0b]:[0,0x41,0,0x0b],[0,0x20,0,0x41,4,0x4f,0x20,0,0x41,0x80,2,0x4d,0x71,0x04,0x7f,0x20,0,0x05,0x41,0,0x0b,0x0b]];
 return Buffer.from([0,97,115,109,1,0,0,0,...section(1,[2,0x60,0,1,0x7f,0x60,1,0x7f,1,0x7f]),...section(3,[3,0,0,1]),...section(5,[1,1,2,2]),...section(6,[1,0x7f,1,0x41,0,0x0b]),...section(7,[4,...name('capacity'),0,0,...name('pixels'),0,1,...name('render'),0,2,...name('memory'),2,0]),...section(10,[3,...bodies.flatMap(b=>[b.length,...b])])]);
}
(async()=>{const h=new LiveWasmHost(),expected=Buffer.alloc(16384,0xc3),rows=[];let firstError,secondError;
 try{
 const first=await h.propose(moduleBytes(true),expected,1,1,4,500);fs.writeFileSync(path.join(out,'first.raw'),first.frame);
 try{await h.verifyLive(50);}catch(e){firstError=String(e);}assert.match(firstError,/deadline/);rows.push(h.status());assert.deepEqual(h.snapshot().frame,expected);fs.writeFileSync(path.join(out,'retained.raw'),h.snapshot().frame);
 try{await h.verifyLive(50);}catch(e){secondError=String(e);}rows.push(h.status());
 if(fixed){assert.equal(rows[0].liveWorkers,0);assert.match(secondError,/unavailable/);}else{assert.equal(rows[0].liveWorkers,1);assert.match(secondError,/deadline/);}
 const second=await h.propose(moduleBytes(false),expected,1,1,4,500);assert.equal(second.revision,2);const checked=await h.verifyLive(500);assert.deepEqual(checked.frame,expected);fs.writeFileSync(path.join(out,'recovered.raw'),checked.frame);rows.push(h.status());
 }finally{await h.close();}assert.deepEqual(h.status(),{liveWorkers:0,busy:false,closed:true,revision:2});
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({fixed,first_error:firstError,second_error:secondError,rows,final:h.status(),snapshot_after_close:h.snapshot()},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
