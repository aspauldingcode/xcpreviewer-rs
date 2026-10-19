// Offline integration proposal; no global state initialization or UI opening.
import {createSessionRegistry} from './session-registry.mjs';
import {createDriver} from './session-driver.mjs';
import {createSelectionOnly} from './selection-only.mjs';
import {assessReport} from './normalized-guard.mjs';
export function createSelectionRegistry(){
 const registry=createSessionRegistry();
 return Object.freeze({bind(config,clock,app,binding){
  const workspace=config?.workspace;
  if(typeof workspace!=='string'||!workspace.startsWith('/private/tmp/')||!workspace.endsWith('/PreviewLab.xcodeproj')||workspace.split('/').slice(1).some(x=>!x||x==='.'||x==='..'))throw Error('workspace binding');
  const source=workspace.slice(0,-'PreviewLab.xcodeproj'.length)+'Sources/PreviewLab/PreviewLab.swift';
  const expected={projects:[workspace,workspace.replace('/private/tmp/','/tmp/')],sources:[source,source.replace('/private/tmp/','/tmp/')]};
  for(const key of ['projects','sources'])if(!Array.isArray(binding?.[key])||binding[key].length!==2||binding[key].some((v,i)=>v!==expected[key][i]))throw Error(key+' binding');
  const b={projects:[...expected.projects],sources:[...expected.sources]};
  const gate=registry.bind(config,clock);
  // Both guards read the same seconds clock; only action API converts to ms.
  const stopMs=gate.snapshot().stopWall*1000;
  const driver=createDriver({gate,app,binding:b,stopMs,clock:()=>clock().wall*1000});
  return createSelectionOnly({driver,assess:ax=>assessReport(ax,b)});
 }});
}
