// Offline integration proposal; no global state initialization or UI opening.
import {createSessionRegistry} from './session-registry.mjs';
import {createDriver} from './session-driver.mjs';
import {createSelectionOnly} from './selection-only.mjs';
import {assessReport} from './normalized-guard.mjs';
export function createSelectionRegistry(){
 const registry=createSessionRegistry();
 return Object.freeze({bind(config,clock,app,binding){
  const b={projects:[...binding.projects],sources:[...binding.sources]};
  const gate=registry.bind(config,clock);
  // Both guards read the same seconds clock; only action API converts to ms.
  const stopMs=gate.snapshot().stopWall*1000;
  const driver=createDriver({gate,app,binding:b,stopMs,clock:()=>clock().wall*1000});
  return createSelectionOnly({driver,assess:ax=>assessReport(ax,b)});
 }});
}
