# Correction: interior cleanup point, not a separate function

The prior declaration-lifecycle bundle labeled PreviewsUI+0x23ef0 as a preview-state destruction entry and attempted a function-return probe there. **That interpretation was wrong.** The existing state-source README explicitly identifies this address as a continuation of the CanvasContent destruction function that begins at 0x23d68. A semantic source-fragment boundary had been mistaken for a function boundary. The historical probe's 1,400 hits are interior-PC observations, not 1,400 calls to a distinct function; its captured “caller_offset” 0x23ee8 is an interior link-register observation, not caller/callee evidence. Missing onLeave events from this invalid probe do not demonstrate non-return or an independently missing state-function return.

Original traces, readers, report and manifest remain unchanged in the prior sealed bundle, with a supplemental ERRATA.md. Its valid collector/provider/registry ordering, genuine CanvasContent entry/return pairs and actual 3→4→3 tab/render sequence remain scoped evidence. corrected-historical-interpretation.json reclassifies the old interior hits without treating them as function entries. Canonical declaration agent no longer installs that invalid probe; its reader handles the historical label explicitly. No new native functions were recovered.

## Corrected runtime controls

After requalifying the owned PreviewLab window/source and existing Xcode PID 45749, two bounded captures associated the interior state-cleanup PC with a genuine owning-function invocation:

- sampled-rpc: 20 edit-phase and 8 restore-phase complete chains.
- sampled-post-ack: 20 edit-phase and 2 restore-phase complete chains using the final posted-message/bounded-ack helper.

Each sampled chain is **function entry at 0x23d68 → interior PC at 0x23ef0 → owning function return**, on the same observed thread and invocation ID. There is no separate state-function entry/return or interior caller claim. The code samples at most twenty owner invocations per phase, so these are not total native call counts. Real source declaration additions/restorations occurred; individual calls may also reflect ordinary value-copy activity. The tests do not identify objects, decode state tags, verify every cleanup branch or prove final reference/resource release. No new rendered-UI control was performed here; the earlier visible declaration lifecycle remains separate evidence.

The current helper replaces synchronous phase RPC with posted messages plus a bounded acknowledgement wait. That focused combination was actually exercised in sampled-post-ack. The canonical seven-function declaration variant uses the same phase-message schema but was not separately rerun in this checkpoint; syntax and retained-artifact regressions pass. The parameterized new driver preserves the executed fixed-path control sequence.

## Preserved unsuccessful attempts

The initial idle capture reached its 120-second session deadline without a requested source edit and exercised no owner/point chain. It is not a passing native control.

The following unscoped tail-site attempt logged 165,702 point hits with no observed owner and overloaded the event stream. Its controller exceeded the source-restoration wait and subsequent 15-second child-wait deadlines. The helper later recorded restoration and normal session cleanup, and independent checks found exact source bytes, controller availability and Xcode alive. The exact delay mechanism and origin of out-of-owner hits are not established; no native crash, hang or shared-tail implementation is inferred. The attempt is excluded from passing controls. Its full 32,262,550-byte trace remains local; SHA-256, counts, original agent/helper and bounded extracts preserve the failure without publishing a bulk dump. The next route removed the tail-site probe and bounded recorded owner intervals.

## Evidence and practical limits

Existing source artifacts supply the minimum boundary qualification; their hashes are recorded. An exact-address arm64 nm lookup at 0x23d68 plus installed swift-demangle independently identifies the owning symbol as the destroy value witness for PreviewsUI.DisplayableContent.Preview.CanvasContent in the same pinned image. Only this already-targeted address was qualified. Pinned image hashes, loaded UUIDs and executable/source guards are unchanged. Exclusive native controller locking and bounded sessions were used. Final source SHA-256 is 128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef; controller available and Xcode left running. No agent-initiated Xcode/simulator termination, protection change, Apple re-signing or new permission was used.

verify.py checks actual source/edit hashes, UUID receipts, valid ownership/order, per-phase sample limits, matching genuine returns and cleanup. Eight synthetic mutations reject wrong owner, point after return, missing return, wrong thread, false function boundary, false restoration, resource overclaim and invalid sampling limit. Reader checks do not execute native code. Original executed helpers/agents/drivers and traces are retained; newer checker adds duplicate-ID/source-hash checks against those same captures. Raw Apple code, binaries, caches and private dumps are not published.

This corrects a material interpretation error and qualifies a selected native control-flow path. Object deallocation, weak native lifetimes, transport/render resources, Canvas interaction/state, other targets and standalone WASM remain unverified. Fifteen observer-suite controls are separate prior component evidence. Full native areas remain 0/9; tracked delivery remains 1/26 (3.8%).
