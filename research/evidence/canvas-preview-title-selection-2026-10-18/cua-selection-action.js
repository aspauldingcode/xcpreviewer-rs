// assess and authorizeSelection are the separately reviewed pure module functions.
var freshSelectionAX=await xcode.getAXState({disableDiffing:true,emit:false});
var freshSelection=assess(freshSelectionAX);
var selectionIndex=authorizeSelection(previousSelection,freshSelection,Date.now(),Date.parse('2026-10-18T17:52:00Z'));
await xcode.click(selectionIndex);
var afterSelectionAX=await xcode.getAXState({disableDiffing:true});
