// Research proposal: execute only during separately reviewed fresh-session initialization.
// Never recreate missing state to resume an active or failed native experiment.
if(!Object.hasOwn(globalThis,'xcpreviewerOwnedRegistry'))globalThis.xcpreviewerOwnedRegistry=createSessionRegistry();
if(!globalThis.xcpreviewerOwnedRegistry||typeof globalThis.xcpreviewerOwnedRegistry.bind!=='function'||!Object.isFrozen(globalThis.xcpreviewerOwnedRegistry))throw Error('registry context invalid');
