# Owned source-file polling loop

`SourceFileLoop` polls an owned source file for a finite interval, reads at most
4,097 bytes, deduplicates by content hash, and coalesces queued builds to the
latest observed source. `SourceRevisionHost.invalidate()` invalidates tickets on
missing, empty, non-ASCII or oversized inputs while retaining the last good
instance/frame. Unsupported build failures also retain the last good frame.
Source identity and frame publication remain atomic through the existing host.

Actual atomic file replacements exercise initial publication, a delayed obsolete
build superseded by a newer edit, unsupported/non-ASCII/oversized edits, deletion,
recovery, and closure during an in-flight build. A separate automatic deadline
aborts an in-flight builder. The fixture builder cooperatively honors AbortSignal.
Closure clears polling/deadline timers and waits for that builder and the host.
A file edit during live verification is queued until the host is idle, avoiding
dropping the latest edit because the serial host rejects concurrent proposals.

The builder contract requires cooperative abort and settlement. This implementation
does not forcibly terminate an arbitrary or noncooperative builder. Current tests
use pinned prebuilt modules and independent expected allocations from the prior
source/native corpus. No fresh compiler is invoked by the watcher yet. A bounded
subprocess compilation adapter with process-tree cleanup is the next step.

An initial test observed a revision while old-worker cleanup was still running;
its failure is retained. The fixed test waits for settled, non-busy state before
live verification. The first canonical run passes fifteen checks; the second,
`20261011T040407Z-primary-live-wasm-swap-6a7fe1c3`, adds serialization and passes
sixteen. Fresh-process verification and separate byte comparisons cover every
84 independent and80 reused-native allocations, plus the saved 16,384-byte
watcher frame. Three accepted revisions, seven retention/close controls, explicit
builder abort and automatic deadline abort pass.

Evidence and seals:
`research/evidence/source-file-loop-2026-10-10` and
`research/evidence/source-file-loop-serialization-2026-10-10`.
These are owned filesystem/reconstruction controls. OS file event semantics,
general SwiftUI state migration, browser execution, native Xcode Canvas sequencing
and scientific delivery acceptance remain open. No Xcode workspace was opened.
