# Owned weak controls and native EditorScene observations

The attempted owned weak-helper load into Xcode was rejected by library validation (different Team IDs). The current agent **does not load that helper** and does not read native weak references. It observes existing EditorScene class method entry/return events and class-name predicates, with capture-local address tokens. Snapshots are historical observation ledgers, not liveness queries. The false weak-access flag describes this agent, not every possible runtime route.

Build and run the three owned weak/FD controls under the controller lock:

`python3 tools/re/native-canvas-weak-runtime/build.py --output /private/tmp/FRESH_BUILD`

Use its build.json paths for a bounded source-only native capture:

`python3 tools/re/native-canvas-weak-runtime/session.py --output /private/tmp/FRESH_CAPTURE --pid PID --library /absolute/owned/libCanvasWeakProbe_HASH.dylib --control /absolute/owned/control --source /absolute/owned/PreviewLab.swift --file-cycle`

The library argument identifies the standalone fixture build and is hashed; the current Xcode agent never loads it. Reverify process/executable, pinned framework and owned source. The helper locks the controller, runs owned controls, attaches the observational agent, adds/restores a known declaration and records source hashes. The capture has a 240-second session deadline, bounded native/ack operations, twenty address tokens and two hundred recorded calls maximum. Conditional source restoration preserves concurrent user edits. No user Xcode/simulator process is terminated. Baseline source fingerprint is intentionally specific to the owned fixture.

UI pin/window-close tests were not exercised because CUA reported the Mac locked. The file-only route needs no GUI input and performed real owned source edits. It does not verify rendered output or per-instance project binding. Two captures observed 20/22 setter intervals; no selected destructor/removed-file method entries occurred. A token is not persistent identity, a newly observed token is not allocation, and no destructor hit does not prove retention/leak or absence of other deallocation paths. No weak lifetime or native resource-release claim follows.

verify.py and mutations.py check saved artifacts only. See research/evidence/canvas-runtime-scene-observation-2026-11-03 for the rejected helper-load receipt, UI limitation, native source controls and original helper exit-status correction. Do not repeat the rejected load unchanged, weaken protections or re-sign Apple apps. Other weak-reference approaches remain unqualified.
