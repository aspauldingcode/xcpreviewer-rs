# Canvas registry selection and bounded input control

The owned Xcode 26.6 PreviewLab session produced two sanitized display-state
diagnostics. Selecting `Text and interaction` changed the reported fresh live
registry from `PreviewLab.swift#1[preview]` to `#2[preview]`. In both reports all
three registries were `Completed: Available`, all providers were `Completed: Not
attempted`, `buildingState` remained `Running`, and `isUpdateInProgress` was false.
The selected registry reported `isStale: false` and `livePreview: succeeded`;
the other two reported stale content and disabled live previews. These fields
must remain separate: availability and a toolbar Ready message alone do not
identify fresh rendered content. This is Xcode's UI diagnostic report, not an
independently observed transport or completion acknowledgment.

The exact fixture source remained unchanged. The owned workspace was raised,
Live mode was selected, and a durable baseline screenshot showed Count 0. A
single coordinate click and a 180 ms held click at the screenshot's Increment
button both left the next screenshot at Count 0. An initial malformed API call
was rejected before input. No source-state reset experiment followed: without
attributed successful input, state retention cannot be tested. This bounds the
simple background-window explanation but does not establish an Xcode state bug
or prove that either event reached the preview application.

The parser in `tools/re/reloop/canvasdiagnostics.py` reads only sanitized
display-state sections, bounds report size/nesting/registry count, rejects
missing, duplicated or malformed required state, and preserves report authority.
Three tests cover both measured reports, five corruption/ambiguity controls,
and a static-success control that must not become live success. A separate
verification process rehashed the evidence and checked the expected selected
registry independently of the producer's summary. Scientific delivery review
remains pending; no milestone acceptance changed.

Evidence: `research/evidence/canvas-input-2026-10-10/manifest.json`. Raw diagnostic
text, including device identifiers and environment paths, stays in ignored local
storage. No report was sent to Apple. REA server 6.2.0 was available with no
selected image; the approved private capture bridge remained offline. These
are separate prerequisites. The owned workspace was closed and the final Window
menu showed zero workspace windows. Next: independently delivered input or an
owned input-visible instrumentation control; compare exported preview pixels
against display pixels with explicit color provenance. Do not repeat unchanged
clicks or promote diagnostic lifecycle labels to native wire evidence.
