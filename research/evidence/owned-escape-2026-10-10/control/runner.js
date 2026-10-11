const fs=require('node:fs'),{runOwned}=require(process.argv[2]);
(async()=>{let record,error=null;try{record=await runOwned(process.argv[3],[process.argv[4],process.argv[5],process.argv[6]],{supervisorPython:process.argv[3],timeout:3000});}catch(e){record=e.record;error=String(e);}
fs.writeFileSync(process.argv[5]+'/node-result.json',JSON.stringify({record,error}));})();
