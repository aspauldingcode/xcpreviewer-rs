import {assess} from './guard.mjs';
// Research proposal. All proof/visual/receipt records are trusted reviewed inputs,
// not authentication. The current unavailable frame record rejects before UI I/O.
export async function deliver(app,ctx){
 const need=(x,m)=>{if(!x)throw Error(m)};const f=ctx.frame;
 need(f?.status==='documented'&&f.api==='cua App.click(Vec2)'&&typeof f.source==='string'&&f.source.length>0,'coordinate frame unavailable');
 need(f.origin?.length===2&&f.origin.every(x=>x===0)&&['screenshot-pixels','logical-points'].includes(f.units),'unsupported frame');
 need(Number.isFinite(ctx.now())&&ctx.now()<ctx.stop,'deadline');
 need([1,2].includes(ctx.clickNumber)&&ctx.receipt.stage===ctx.clickNumber,'receipt stage');
 need(ctx.receipt.identity.view===ctx.visual.view&&ctx.receipt.identity.pid===ctx.receipt.live_identity.pid&&ctx.visual.count===ctx.clickNumber-1,'view/count/PID');
 need(ctx.receipt.live_identity.identity[2]===ctx.expectedBinaryPath&&ctx.receipt.live_identity.state==='L','exact executable');
 const snap=await app.getAXStateAndScreenshot({disableDiffing:true,emit:false});
 assess(snap.state,ctx.binding);
 const hash=await ctx.digest(snap.screenshot);need(hash===ctx.visual.screenshot_sha256,'fresh screenshot mismatch');
 const g=ctx.geometry;const numeric=(x,n)=>Array.isArray(x)&&x.length===n&&x.every(z=>typeof z==='number'&&Number.isFinite(z));
 need(numeric(g.raw_point,2)&&numeric(g.image_size,2)&&numeric(g.button_box,4)&&numeric(g.editor_box,4),'geometry');
 const inside=(q,b)=>b[0]<q[0]&&q[0]<b[2]&&b[1]<q[1]&&q[1]<b[3];
 const window=[0,0,...g.image_size];need(g.image_size.every(x=>x>0),'image size');
 for(const box of [g.button_box,g.editor_box])need(0<box[0]&&box[0]<box[2]&&box[2]<g.image_size[0]&&0<box[1]&&box[1]<box[3]&&box[3]<g.image_size[1],'box');
 const mapped=g.raw_point.map(x=>x*2);need(inside(g.raw_point,window)&&inside(mapped,window)&&inside(g.raw_point,g.editor_box)&&inside(mapped,g.button_box),'candidate containment');
 // geometry.py's finite checks are a prerequisite. The actual documented frame
 // must additionally match the proposed factor2/origin0 transform.
 need(f.units==='logical-points'&&f.screenshot_scale===2,'candidate transform not documented');
 need(ctx.now()<ctx.stop,'late action');
 await app.click(g.raw_point);
 return {sent:true,clickNumber:ctx.clickNumber};
}
