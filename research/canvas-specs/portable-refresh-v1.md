# Portable preview refresh — bounded original feature contract

This describes a local portable preview feature. It makes no claim of Xcode Canvas parity, native transport compatibility or SwiftUI state preservation. No target code, assets, implementation structure or private binary details are provided.

## Public interface

Create a JavaScript session using a caller-provided asynchronous build callback. Expose `poll(source)`, `refresh(source)`, `status()`, `frame()` and `close()`. Sources are strings. Build receives the source and an AbortSignal and returns a candidate frame. A separate caller-provided asynchronous validation callback decides whether the candidate is acceptable. Candidate representation is caller-defined. Defaults must not silently accept an unvalidated candidate. Document errors and return values.

This callback API is a researcher-authored original product design. Observed local preview behavior motivates the publication rules below; API shape and implementation strategy are not recovered target interfaces. String-wide source handling, asynchronous callbacks, validation, cancellation and concurrency rules are original design requirements, not claims of behavior verified in a native target. The motivating refresh observations cover supported regular ASCII source in an owned portable preview.

## Observable rules

1. Initial session has no accepted frame and revision zero. A successful build and validation publish a frame and increase revision by one. Each attempted build receives a strictly increasing generation. Failed attempts consume generations, not revisions.
2. Polling unchanged source after observing it does not build again. An explicit refresh rebuilds unchanged source. Polling a changed source attempts a build.
3. Build or validation failure retains the previously accepted frame and revision, exposes current failure, and records failure history. Refresh of that same rejected source retries. A later successful refresh restores readiness while retaining historical failure information.
4. Only validated candidates can become accepted. A validation callback returning false or throwing rejects the candidate. Failed validation cannot replace the last accepted frame.
5. Close is terminal, clears frame availability and requests cancellation of an in-flight build. A late completion after close must never publish. Poll and refresh after close fail. Repeated close is harmless.
6. Concurrent build requests fail explicitly without starting another build or consuming another generation. Status and frame inspection remain available while building. Failed concurrent requests must not damage the in-flight operation.
7. Refresh creates a new rendering attempt. User-state preservation and migration are outside this contract. Native compiler deadlines, file observation, JSON-RPC, frame pixel validation algorithms and native resource lifetimes are outside this slice.

## Acceptance examples

- Poll A succeeds: revision1/generation1. Poll A again: unchanged, build count1. Refresh A succeeds: revision2/generation2.
- Starting from that frame, refresh B rejects twice: attempted generations3 and4, accepted revision2/frame A retained. Refresh A succeeds: revision3/generation5, readiness ready, prior failures retained.
- A validation failure preserves accepted frame; validation must be awaited before publication.
- While build is pending, another refresh fails busy; resolving original candidate may publish once if still open.
- Close during a pending build aborts its signal. Even a noncooperative callback resolving later cannot publish or restore availability. Closed refresh fails.
- Independent sessions do not share revision, generation, failures or frames.

## Attribution and scope

Implementation must be original and dependency-free, with no bundled icons, fonts or other media assets. Use standard JavaScript and Node's built-in test runner. Tests should exercise the above behavior from the public API. No repository source, research reports, decompilation, private traces or historical implementation may enter the implementation context. Implement in a separate new directory with this file as its only project input.

A fresh agent context and a separate output directory provide context separation. They do not by themselves enforce filesystem/tool access isolation; do not label the result a sandbox-enforced clean-room reconstruction. Record exact inputs and this limitation. This slice does not pass either project's milestone or replace the existing reconstruction until integration is separately reviewed.
