# Native PreviewType and hosted-location value codecs

This unit reconstructs the complete selected wire value enums, not scene routing or the complete shell update. Actual shipped PreviewType and PreviewType.HostLocation decoders, encoders, metadata accessors and destruction witnesses execute in an owned ARM64 helper. No private Swift module import, Xcode/simulator attach/action/modification/termination, app re-signing or protection change occurs. Both milestones remain incomplete.

## Recovered value contracts

PreviewType has closed tags `static` and `hosted`. Static reads no hostLocation and canonical encoding omits it, even if the inactive input member is malformed. Hosted requires hostLocation to decode as the nested location dictionary.

HostLocation has closed tags `mainScene`, `simDisplayScene`, `external`, `nsPreview` and `injectedScene`. Only injectedScene requires `sceneIdentifier`, a String that may be empty. The four payload-free locations ignore malformed inactive sceneIdentifier values. Unknown fields are dropped on re-encoding; unknown tags, missing tags, wrong tag types, absent active payloads and malformed active payloads fail. Original scene String data survives, including composed/decomposed Unicode, embedded NUL and supplementary characters. Internal reflection spells the associated argument `(identifier: String)`; its wire key is `sceneIdentifier`. These names are intentionally distinguished.

The original Rust preview_type module provides PreviewType/HostLocation decode, discriminant and active-field encoding methods with explicit nested errors. These types are distinct from pipeline CanvasMode and request_projection::HostLocation; no conversion or scene-selection policy is inferred between them. Derived Rust structural equality compares original wire representations; native enum/String equality and hash identity are not qualified by this unit.

The `preview-type` and `host-location` inspection commands emit their canonical selected value dictionaries. Summaries expose tags and scene String byte count without its contents. Full shell/setup/product/seed schemas and downstream routing remain separate work. Existing bounded binary-plist limits apply before enum decoding.

## Executed native controls

41 native dictionary-input decode attempts produce 26 accepted decoder/encoder compositions and 15 native rejections. PreviewType contributes 12 accepts/eight errors; direct HostLocation contributes 14 accepts/seven errors. Every tag is covered, including active injected-scene Strings with empty, Unicode, NUL and supplementary characters. Inactive malformed members are tested on static and all four payload-free locations. Complete type-sensitive output dictionaries match Rust and WASI.

Both enum metadata objects are verified kind513 with size/stride/alignment16/16/8. Actual module paths/export offsets, disk SHA/UUID, PropertyList representation and destruction witnesses are checked. Direct enum destruction offsets are 0x2774c and 0x27ac4. Native decoders consume the initialized PropertyList input on success/error. Consumed temporary buffers are deallocated without double destruction; failed result buffers are never read or destroyed, and captured Swift errors are released. On success, canonical dictionary values are copied before direct native PropertyList and enum destruction. Direct returns: 26 enum destructions, 26 encoded PropertyList destructions and 15 Swift error releases. Independent input/output references may retain objects, so no unique ownership/final release/heap quiescence/global settlement claim follows.

The original bridge forwards x0/x1, indirect result x8 and self x20 with isolated x21 error handling. Native subprocesses have eight-second deadlines, clear DYLD_* overrides and leave loaded frameworks present until owned helper exit. Foundation/Swift/Messaging runtime image UUIDs are compared on fresh replay. No native crash, timeout, load or layout failure occurred.

## Source evidence, validation and failures

5,976 selected instruction bytes qualify the prior box/String conversion foundations, both enum discriminant/key/value codecs, metadata accessors and selected destruction witnesses. Reflection names all cases and the injected-scene labelled String tuple; imported String metadata/witness bindings confirm the active field decoder. Raw Apple disassembly stays in ignored local storage; public evidence contains original helpers/fixtures, sanitized findings and hashes only. Source observations and actual runtime results remain separate.

362 Rust tests pass, including two actual native fixture/API tests.44 inspector cases include 26 accepts, 15 actual native-matched errors and three additional scope/profile rejections (two non-dictionary tops and an over-depth inactive member).70 actual WASI invocations and26 Foundation reparses pass. Non-dictionary top tests are not claimed as directly executed native dictionary-constructor inputs; depth is a portable reader restriction. Fresh disposable replay rebuilds/runs source checks, focused tests, native41 cases/runtime UUID checks, WASI and reparses. WASI preview1 is exercised; browser WASM remains unproven.

The first disposable replay failed because its inherited focused-test count expected three tests instead of this unit's two. The harness count was corrected; the original failure log is preserved as replay-initial-failure.log. No native replay had run before that assertion.

Two source-verifier assumptions failed and were corrected: an associated argument was initially assumed to be a bare String typeref, but is a labelled String tuple; then a fixed byte length omitted the trailing NUL. The exact observed tuple bytes are now checked using their literal length. These were static verification errors, not native decoder failures. Failure expressions and corrections are preserved in failures.json. REA command/catalog identity remains matched with session closed/provider null and server-reported alignment unknown. Unchanged Ghidra/provider limitations were not retried; native Canvas UI/provider quarantine remains active.

Next: implement remaining shell/setup/product/seed value dependencies and trace instance/updater branches into complete payload construction, qualifying optional controls at each boundary. Actual transport/resources, outer request identity, Canvas lifecycle/refresh/rendering, provider terminal state and global settlement remain open.
