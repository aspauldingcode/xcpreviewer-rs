# One-shot invalidation fulfillment

Pinned arm64 PreviewsFoundationHost source qualification. This package contains original readers, hashes and sanitized findings. Raw Apple instruction text remains temporary and local.

Verified scope: 1,988 instruction bytes, ten selected calls, waiting/fulfilled state and outcome metadata, and two legal-state source summaries under normal callback return. Fresh copied-reader replay reproduces complete findings.

The concurrent storage specialization forwards to shared fulfillment code. Waiting copies prior observer/token storage to the result, calls the supplied trace builder, installs trace/callsite and marks state fulfilled. Already fulfilled invokes its configured handler and destroys OverfulfillHandle context; on normal no-error return, it returns zeroed storage. The outer invalidation caller checks the storage pointer after unlocking and skips dispatch when absent.

The supplied trace forwarder reaches an InvalidationTrace.Link builder/append path. It builds the new trace; the shared fulfill helper transfers observer storage. Full trace link contents and ownership are not mapped here.

The managed-token Void/Void specialization similarly distinguishes waiting and fulfilled. Waiting records fulfilled and returns outcome 0; fulfilled returns outcome 1 after normal handler/context cleanup. The previously recovered caller suppresses its callback for outcome 1 and otherwise calls it after unlock.

This qualifies source one-shot dispatch suppression for legal states and normal return. It does not establish actual repeated native invalidation, thread races, reentry, callback delivery, thrown errors, OverfulfillHandle cleanup effects, failure-policy behavior or final resource settlement. The source matrix is a summary of checked branches, not native execution or an independent behavioral oracle. Full acceptance remains open.

Run `python3 verify.py` against pinned Xcode. Disassembly is bounded to twenty seconds per range, fresh replay to fifty-five seconds, using the exclusive controller lock. REA identity aligned/no open session; prior UI/Ghidra failures not retried unchanged. No native private call, GUI action, product change or Rust-test rerun.
