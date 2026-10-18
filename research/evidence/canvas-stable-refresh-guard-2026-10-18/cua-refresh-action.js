// assess/authorize definitions must be the reviewed stable-guard.mjs functions.
// previous is assess(previousFullOwnedAX), captured before this fresh same-call check.
var freshStableAX = await xcode.getAXState({disableDiffing:true,emit:false});
var freshStable = assess(freshStableAX);
var refreshIndex = authorize(previous,freshStable,'refresh',Date.now(),Date.parse('2026-10-18T17:41:00Z'));
await xcode.click(refreshIndex);
var afterStableAX = await xcode.getAXState({disableDiffing:true});
