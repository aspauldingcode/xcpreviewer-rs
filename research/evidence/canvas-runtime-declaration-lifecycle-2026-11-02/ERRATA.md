# Boundary correction added after the original sealed capture

The original report's preview-state-destroy probe at 0x23ef0 is an **interior continuation of CanvasContent destruction**, not a distinct function entry. Its onLeave probe was invalid, and the interior link-register value was incorrectly labeled as caller evidence. The 1,400 recorded hits remain observations of that PC; no separate state-function call/return claim follows. Collector/reconciliation ordering, genuine CanvasContent intervals and UI declaration lifecycle observations are unaffected.

See [corrected interpretation, failed attempt and bounded native control-flow tests](../canvas-runtime-destroy-boundary-2026-11-03/README.md). Original artifacts and manifest remain unchanged; this supplemental erratum is outside that original seal. Current tooling removes the invalid probe and reports the historical PC hits separately. Object/resource release remains unverified.
