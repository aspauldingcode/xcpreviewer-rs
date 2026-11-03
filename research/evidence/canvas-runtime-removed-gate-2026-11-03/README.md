# Native zero-count gate explains the observed early return

Static expansion remains paused. The prior actual-deletion experiments reached the removed-event filter but could not explain why scene propagation stopped. This changed instrumentation qualifies and measures the **existing count gate**, rather than repeating an unchanged failure loop. Only a 188-byte window within the already recovered workspace handler was inspected locally to choose the needed probe points. No new function body was recovered; the private instruction listing stays local and only its hash plus sanitized interface findings are published.

## What was exercised

Two fresh guarded primary-source deletion/restoration captures run in Xcode PID 45749 under the controller lock. The first captures a single native handler sequence: removed-event block, filter entry, filter return, the count-test instruction with **x21 = 0**, empty-cleanup block, handler return. The register was loaded by the target from the filtered-array count immediately beforehand. The second changes the profile to omit the cleanup-block probe, and again sees the count register zero between filter return and handler return. Neither selected workspace/editor removed-location nor scene-update method is called in those invocations. Baselines have no removed-event block.

This supplies native evidence for the **zero-count early-return gate** in the sampled primary-file cases. It does not explain why the filter produced zero, decode input payload paths, establish nonempty propagation, or prove a resource was released. Deletion-to-payload attribution remains temporal correlation with the sole controlled file mutation; the event's path array was not decoded. The earlier auxiliary-member capture did not sample this register, so no zero-count measurement is retroactively assigned to it.

The new probes observe interior instructions, not additional functions or function returns. Both are gated by the same active workspace invocation and its earlier removed-event block, with a global bounded event budget. The count-only variant reduces the probe set; it is still instrumentation in the same previously attached Xcode process, not an uninstrumented/fresh-process control. No performance, observer-effect absence, general concurrency or exact frame/state claim follows.

## Outcomes and evidence levels

Both sessions complete source restoration, unload and detach, and exit **one** because the requested scene propagation was not observed within eight seconds. This exercises the canonical runner's missing-propagation outcome; it is not a native crash, script error or a passing full-removal test. The gate-specific recorded assertions pass for both profiles. No build, UI action, notification synthesis, forced result, protection change, Apple resigning or user process termination occurs.

Eight synthetic gate-evidence faults reject, including nonzero count, wrong invocation, missing/incorrectly enabled cleanup probe, reordered blocks and false propagation/restoration reports. Eight historical auxiliary-reader faults also reject with the updated reader. These are artifact-reader tests, not native positive nonempty controls. Existing standalone observer tests and native build/weak-load evidence remain separate.

* Static qualification: minimum local instructions needed to identify the native count register/zero continuation; no broader recovery or research-log expansion.
* Native runtime verification: actual count-zero instruction observation, one empty-cleanup execution, and real source deletion/restoration with the captured negative propagation outcome.
* Simulated replay: none accepted as native evidence; only deliberate recorded-artifact corruption for reader validation.
* Working functionality: an original pinned-host diagnostic harness. Full scene removal, object destruction, transport/render resource release and standalone WASM functionality are not accepted.

Exact original execution agents/sessions, normalized event logs, gate assertions, local-listing hash and postcondition receipts are included. Independent checks confirm original source and project hashes, controller available and Xcode alive. No raw listing, Apple binary, native object pointer or private memory dump is published. Full native acceptance remains 0/9 and tracked delivery 1/26 (3.8%).
