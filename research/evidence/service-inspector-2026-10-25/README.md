# Bounded service-message inspector

Original usable CLI for the recovered value subset: named file or stdin, readable
routing summary or normalized bplist00 stdout. No service is contacted. Unknown
fields are omitted; unsupported outer kinds reject. No identifier allocation.
Human strings are control-escaped and bounded to 256 Unicode scalars with byte
count/truncation flag. Native and WASI summaries are byte-identical across the
12 complete public Foundation controls. Full UInt64 values survive canonical
output and Foundation reparse. See the linked usage document for normalization,
limits and non-lossless behavior.

Validation: all 271 Rust tests; four new integration tests execute the CLI for
all eight supported outer kinds, legacy PID and audit token, absent/invalid
capabilities, wide seeds, unknown/invalid messages, namespace errors, escaped
Unicode/controls, long string truncation, file/stdin equivalence and 64 MiB+1
rejection. Twelve original fixture dictionaries pass public Foundation
serialization before native CLI and actual WASI, and both canonical outputs
pass Foundation reparse with type-sensitive complete value equality. Actual
WASI runs each case twice: canonical and summary (24 invocations), no filesystem
preopens or inherited environment. Explicit stdin/stdout handles only. Input,
output and expected values are reproduced by controls.py; no private dumps.

Current source is independently pinned and the predecessor's 768-byte source
check rerun; no new native semantic recovery is claimed. Source-derived purge
behavior and other routes retain their predecessor evidence scopes. The CLI
and its expected normalization composition are original. Public Foundation
operations do not call private service decoders. No Xcode, simulator or agent
process is selected, signalled, cancelled, purged or otherwise controlled.
REA/Ghidra server readiness remains previously inconclusive; no repeat import
or status loop was attempted. Current installed framework identities were
verified directly offline. Browser execution, private dispatcher/action parity,
provider lifecycle/resource settlement and both milestone contracts remain open.

Two verification failures are retained: the first test fixture used unsupported
inner requestScreenshot instead of the recovered render command; after fixing
it, all 271 tests passed. The first cross-runtime expected PID dictionaries
omitted canonical discriminant=pid; observed output correctly contained it,
matching the prior ProcessTarget contract. Expected controls were corrected;
no product codec was changed to hide that failure. Disposable replay rechecks
the four new integration tests, source identities/instructions and all 12
Foundation/24 WASI controls. Full 271-test output is retained separately.
