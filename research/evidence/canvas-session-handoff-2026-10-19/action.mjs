import {assessReport,authorize} from './normalized-guard.mjs';
export async function guardedClick(app,previous,binding,kind,stop,clock=Date.now){
 const ax=await app.getAXState({disableDiffing:true});
 if(typeof ax!=='string'||ax.length>262144)throw Error('AX shape');
 const fresh=assessReport(ax,binding);
 const index=authorize(previous,fresh,kind,clock(),stop);
 await app.click(index);
 return app.getAXState({disableDiffing:true});
}
