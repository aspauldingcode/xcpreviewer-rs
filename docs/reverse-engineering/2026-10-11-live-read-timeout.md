# Live verification deadline and worker quarantine

A failed live verification now terminates its owned worker before releasing the host's busy state. The last accepted snapshot remains available as cached bytes. Repeating verification rejects a terminated worker immediately through its observed threadId=-1; proposing a healthy replacement still advances revision and verifies successfully. This is an owned portable host policy, not native Canvas timeout behavior.

## Discriminating fixture and retained failure

The graph's only candidate still requires a reviewed binding, and native capture remains blocked by the offline approved bridge. No unfinished running/reconciliation wake or second writer exists. Following the completed public event controls, this experiment switches to a demanded portable isolation/cleanup boundary instead of another local signal permutation.

The control hand-authors a no-import WASM module with the host's exact four required exports and two fixed memory pages. Its capacity is16,384; valid render strides return the declared rendered extent without modifying the allocation. Invalid stride controls return0 and preserve bytes. Its pixels function returns0 twice, allowing proposal validation, then loops forever on the next live verification call. A healthy counterpart always returns0. These are host execution fixtures, not Swift source or native image oracles.

Both baseline executions accept the fixture and then hit a50ms live-read deadline. The existing finally block releases busy but retains one unresponsive worker. A repeated50ms read reaches another deadline and still leaves that worker alive. The snapshot remains exact. Replacement terminates the old worker and recovers, and final close clears workers. Frozen baseline source/results and an assessment with acceptance false retain this resource-cleanup failure.

The fix terminates the active worker in verifyLive's failure path, then rethrows the original error and releases busy. The common request function checks worker.threadId before installing a new request. Both fixed executions report zero workers after the first deadline, preserve cached revision1 bytes, reject repeated verification as unavailable, accept a healthy revision2 replacement, verify its bytes and close with workers0/busyfalse. The active metadata remains cached; worker removal does not manufacture a new publication. Failure of ordinary verification also quarantines execution; this finite control specifically exercises a hung pixels call.

## Evidence and validation

Evidence: `research/evidence/live-read-timeout-2026-10-11`; manifest `f09294fd8236fe8705832d0b04bdb1f366e5f08a32a2e5ae8ea3e22664f8c23f`. Existing local Node/V8 version, darwin/arm64 identity, frozen sources, exact control and actual waits are retained. Ordinary owned source and hand-authored WASM measurements require no shipped Apple artifact or runtime attachment; no REA/native transport claim follows.

Four producer executions exit0 under six-second subprocess caps,500ms proposal/recovery limits and50ms live verification limits. The verifier compares196,608 independent expected bytes: three complete16-KiB allocations per run, all0xc3, including untouched extent and tail. Seven resealed faults alter actual wait, retained worker, repeated error, recovered revision, close busy state, allocation byte4 and tail byte16,383; all reject despite new valid hashes. Current host equals frozen fixed source. Candidate tests also run the existing real worker swap/fault/close/reentrant-guard suite. No Rust code changes.

## Practical limits and next integration

Cached snapshot availability is separate from live execution availability. Direct verifyLive rejects after quarantine. The higher PreviewSession readiness projection currently derives ready from publication metadata and does not yet represent liveWorkers0 with cached frame. This checkpoint does not claim that demanded MCP consumers already receive an execution-unavailable readiness state. Next integrate that distinction into readiness/diagnostics and finite consumer recovery controls, preserving last accepted bytes and explicit refresh semantics.

No new browser, Linux, Windows, Swift rendering, native Canvas, performance or private protocol acceptance is claimed. R1/R2 native release accounting and both milestones remain open. Approved capture restoration remains an independent prerequisite.
