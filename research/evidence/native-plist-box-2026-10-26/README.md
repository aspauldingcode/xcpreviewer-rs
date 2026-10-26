# Owned-process native PlistValueBox conformance

Actual shipped MessagingHost/FoundationHost value methods now execute in an owned
ARM64 helper. No private Swift module import, Xcode/simulator attach, Apple app
modification/re-signing, system protection change or UI/provider action. Both
frameworks load with a fixed rpath in this process. Every selected symbol's dladdr
module path and offset matches pinned disk images; DYLD environment overrides are
removed for native runs. Each native execution has an8-second deadline.

The source-guided C/ARM64 bridge forwards explicit arguments in x0/x1, resilient
indirect result in x8, borrowed self context in x20 and Swift error result in x21.
It saves/restores the frame/x20/x21, starts error at zero and returns that error
pointer through C x0. A Clang-imported C header fixes the helper-side convention.
Native metadata accessors are independently pinned. Runtime assertions require
struct kind512,field0 offset0,size/stride8,alignment8 for PropertyList/PlistValueBox,
matching the public Swift Dictionary representation. Native VWT destroy/copy/take
function offsets and the String protocol witness are checked before value calls.
String/Optional<String> outputs use their actual Swift core types/layouts. No
invented private type declaration or unchecked hidden context is used.

1,488 source bytes qualify codec/getter/metadata/ownership paths. Actual take witness
copies one word without retaining; source buffer was initialized with its own
Dictionary ownership, then deallocated without deinitializing consumed contents.
Box init transfers that word. Encoding copies via the pinned native retain witness;
the helper copies the encoded public Dictionary before explicit native PropertyList
destruction. Box destruction delegates to its PropertyList destroy witness. Typed
String results move from initialized native output buffers; errors never read an
uninitialized result. Each returned Swift error receives swift_errorRelease.

Per selected native run:11 box initializations,11 encodes,11 required String reads,
11 optional String reads,11 direct Box destroy-witness calls,11 direct encoded
PropertyList destroy-witness calls and12 error-release calls return. Counters record
direct helper calls; internal/nested ARC operations are not counted. Native box
codec retains empty/unknown/Bool/Int/Data/Date/nested dictionaries. Typed results
confirm empty String is present, required missing fails, optional missing is absent,
and present malformed types fail. Twelve errors are expected typed rejections,
not probe failures. A heap-backed Unicode String was added after the initial ten-input probe. Native error descriptions/classes/wrapping are not compared.

The derived33-case fixture contains11 wire roundtrips and22 typed outcomes, with
21 accepts/12 rejects. Complete type-sensitive native results agree with original
Rust code and54 actual WASI runs;21 Foundation reparses and bounded summaries pass.
348 Rust tests pass, including a new actual-private-method fixture/CLI check.
The existing implementation required no behavioral correction for these cases.
A fresh disposable replay rebuilds/runs the native helper, compares its full result
and counters with the recorded run, derives the fixture again, then checks Rust/
WASI/reparses. Source-only verification never claims runtime invocation.

This closes the prior private-module-access gap for these finite value methods
through a pinned owned-process ABI bridge. It does not establish native generic
HashableBox equality/hash/identity, complete control-state transport, preview
request execution, Canvas lifecycle/rendering/provider behavior, memory quiescence
or global resource settlement. Explicit destroy/release returns and helper exit
are scoped ownership evidence only. Libraries remain loaded until helper exit;
framework/runtime caches and other resources are not audited. The portable raw
outer-key collision restriction remains separate and was not exercised as a native
rejection. Browser WASM is not proven; WASI is exercised.

No native probe verification failures, load failures, crashes or timeouts observed.
The fixture installer initially refused an already-owned directory when adding the
heap String case; idempotent directory handling corrected that tooling failure.
Draft symbol spellings were checked against actual inventories before invocation;
value-witness ranges follow actual table entries rather than folded display names.
REA command/catalog identity matched; session closed/provider null. Controller lock
held. Only original helper C/Swift/assembly, sanitized findings and owned fixture
values are published. Raw Apple assembly remains local/ignored. Both milestone
contracts remain incomplete.

Next: use this proven bounded owned-process route for useful HashableBox/control
state mappings and other typed protocol methods only after exact ABI/layout/owner
verification. Continue structured preview identity, remaining request/localization/
context/service fields and actual UI/transport/resource correlation.
