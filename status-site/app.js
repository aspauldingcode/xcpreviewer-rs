'use strict';
const $ = id => document.getElementById(id);
const text = (id, value) => { $(id).textContent = value; };
const el = (tag, value, cls) => { const n = document.createElement(tag); if (value !== undefined) n.textContent = value; if (cls) n.className = cls; return n; };
(async () => {
 try {
  const response = await fetch('status.json', {cache:'no-store'});
  if (!response.ok) throw new Error(`Status data unavailable (${response.status})`);
  const d = await response.json();
  if (d.schema_version !== 1 || d.recovery.areas.length !== 9 || new Set(d.recovery.areas.map(a=>a.id)).size !== 9) throw new Error('Invalid recovery denominator');
  const accepted = d.recovery.areas.filter(a=>a.status === 'accepted');
  for (const a of accepted) for (const key of ['source','native_controls','contract','replay','target_coverage']) if (!a.acceptance?.[key]) throw new Error(`Missing acceptance evidence: ${a.id}/${key}`);
  const percent = Math.floor(100*accepted.length/d.recovery.areas.length);
  text('accepted-percent', percent); text('accepted-count', `${accepted.length} of ${d.recovery.areas.length} required areas fully accepted`); $('recovery-progress').value = percent;
  const one = d.milestones.find(m=>m.number===1), two = d.milestones.find(m=>m.number===2);
  if (!one || !two || one.total_issues < 1 || one.closed_issues > one.total_issues) throw new Error('Invalid milestone counts');
  const issuePercent = Math.floor(100*one.closed_issues/one.total_issues);
  const allIssues = d.milestones.reduce((sum,m)=>sum+m.total_issues,0), closedIssues = d.milestones.reduce((sum,m)=>sum+m.closed_issues,0);
  const releaseReady = accepted.length === 9 && ['linux','macos','windows','standalone_swiftui_wasm','full_product_conformance'].every(key=>d.overall.release_acceptance[key]);
  const trackedPercent = Math.floor(1000*closedIssues/allIssues)/10;
  const overallPercent = trackedPercent === 100 && !releaseReady ? 99.9 : trackedPercent;
  text('overall-percent', overallPercent); $('overall-progress').value=overallPercent;
  text('overall-count', `${closedIssues} of ${allIssues} delivery tasks closed · ${releaseReady ? 'release acceptance qualified' : 'full release acceptance pending'}`);
  text('issue-percent', issuePercent); $('issue-progress').value=issuePercent;
  text('issue-count', `${one.closed_issues} of ${one.total_issues} tracking issues closed`); text('issue-note',one.note);
  text('wasm-count', `${two.closed_issues} of ${two.total_issues} tracking issues closed · implementation gated`);
  $('milestone-one').href = `${d.repository}/milestone/1`; $('milestone-two').href = `${d.repository}/milestone/2`;
  const updated = new Date(d.updated_at); if (!Number.isFinite(updated.getTime())) throw new Error('Invalid snapshot date');
  $('updated').dateTime=d.updated_at; text('updated',updated.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}));
  text('freshness',Date.now()-updated.getTime()>48*60*60*1000 ? 'Snapshot over 48 hours old' : 'Updates at verified checkpoints');
  text('focus',d.current_focus); text('formula',d.recovery.formula);
  if (d.runtime_validation) {
   const r=d.runtime_validation;
   text('runtime-count',`${r.normal_native_passes} normal native controls passed · ${r.observed_negative_controls} negative control produced a diagnostic failure`);
   text('runtime-summary',r.summary); text('runtime-ui',r.ui_summary); text('runtime-unknown',r.unknown);
   $('runtime-evidence').href=r.evidence_url; $('runtime-validation').hidden=false;
  }
  d.recovery.areas.forEach((a,i)=>{
   const detail=el('details',undefined,'area'), summary=el('summary');
   summary.append(el('span',String(i+1).padStart(2,'0'),'area-number'),el('span',a.title,'area-title'),el('span',a.status==='accepted'?'Accepted':a.evidence_level,'area-status'),el('span','›','area-arrow'));
   const body=el('div',undefined,'area-body'), proven=el('div'), pending=el('div');
   proven.append(el('h3','Qualified so far'),el('p',a.verified_summary)); if (a.evidence_url) { const link=el('a','Review scoped evidence ↗'); link.href=a.evidence_url; proven.append(link); } pending.append(el('h3','Still required'),el('p',a.remaining)); body.append(proven,pending); detail.append(summary,body); $('areas').append(detail);
  });
  d.recent.forEach(x=>{const row=el('article',undefined,'log');row.append(el('time',x.date),el('h3',x.title),el('p',x.detail));$('recent').append(row);});
  d.recovery.requirements.forEach(x=>$('requirements').append(el('li',x)));
  d.targets.forEach(x=>$('targets').append(el('li',x)));
  text('publication',d.publication.evidence_availability);
  d.history.forEach(x=>{const row=el('div',undefined,'history-row');row.append(el('span',x.date),el('strong',`${Math.floor(100*x.accepted_areas/x.required_areas)}% gate accepted`),el('span',x.note));$('history').append(row);});
  document.documentElement.dataset.status='ready';
 } catch (error) {
  text('freshness','Status unavailable'); text('focus',error.message); $('focus').classList.add('error'); document.documentElement.dataset.status='error';
 }
})();
