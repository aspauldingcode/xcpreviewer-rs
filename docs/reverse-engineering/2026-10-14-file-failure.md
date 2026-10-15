# Opaque builder failure diagnostics

A builder can reject with a value that cannot be converted to a string. Previously the file loop diagnostic handler threw a conversion TypeError, losing the original failure event and leaving the settled drain rejected. The retained frame survived, but live verification also rejected until another edit replaced the drain.

The handler now uses a fixed fallback diagnostic if string conversion fails. Opaque and ordinary Error controls each run before and after the change. Fixed controls retain the prior frame, permit live verification immediately after failure, and accept a subsequent source C edit. Ordinary Error diagnostics remain unchanged. This does not mask noncooperative builders or add a builder deadline.

Two bounded source-control programs consumed two declared acquisition slots, with four scenarios using actual owned prebuilt WASM execution. Eight full allocations match pinned independent expectations: 131,072 bytes, including 672 row-padding bytes and 127,488 allocation-tail bytes. The independent sealed reader rejects eight resealed faults. Current nested-observation, real-file edit/close and capped short-read regressions cover retained neighboring behavior. No native acquisition was repeated.

This qualifies reconstruction failure handling, not native Canvas transport, refresh or state migration. Private capture bridge remains absent; REA availability is a separate prerequisite. Both milestones and issues #15, #19, #22 and #25 remain open. Evidence: `research/evidence/file-failure-diagnostic-2026-10-14`, manifest SHA-256 `7f73ae4818113ec427534df0e5cfcf0f9384360ebd03559bff38178f59a9caeb`.
