# Purge request values and optional flag compatibility

The portable service envelope now supports purge with required workspaceID:String and killAgents:Bool. The wire decoder reads killAgents as optional: absence becomes false, while a present invalid value throws. Canonical encoding always includes an explicit Bool, including false. The outer message identifier remains a separate optional payload key. This is a request value; it performs no purge, workspace lookup, process termination, authorization check or resource settlement.

## Source and native correlation

Current PreviewsMessagingHost identity matches prior seals.768 selected instruction bytes independently match LLVM output. Metadata and bounded raw-key getter evaluation recover workspaceID/killAgents. Decoder first calls required unarchiveValue for String, then unarchiveOptionalValue for Bool; selected metadata imports are actual Swift String and Bool. Error paths propagate rather than applying the capabilities decoder's tolerant fallback. Success masks the optional Bool byte with1 and stores a nonoptional field. The original encoder stores both workspace String and Bool under their exact keys; false is not omitted.

An owned public Swift observation measures Bool? size1 and bytes absent=[2], false=[0], true=[1]. The source mask therefore maps an absent flag to false on this pinned native profile. This reads only an initialized owned Swift value, not private object memory or a guessed callable ABI. The portable implementation uses an explicit missing-value default rather than adopting Swift's memory representation. Outer MessageType tag11 selects purge payload decoding and Content tag9 selects its serializer plus the common optional identifier archive tail; these internal tags are not numeric wire values.

## Original implementation

purge.rs provides PurgePayload with workspace_id and kill_agents, borrowed dictionary decode and canonical output. Missing workspace rejects; empty String remains valid. Missing killAgents becomes false. Present invalid values, including truthy-looking2 and String("true"), reject instead of silently falling back. The shared measured primitive Bool helper is reused by capabilities and purge: Boolean, numeric zero/one including canonical unsigned zero/one, and real zero/one. Other numbers/objects reject; arbitrary Objective-C objects and future runtime bridging remain outside this primitive profile. Capabilities retains its independent outer tolerant fallback. Purge decode errors propagate through ServiceEnvelope, preserving validation of the outer identifier before content decoding.

ServiceContent adds a public Purge variant. Exhaustive Rust matches must handle it. No native operation is dispatched and killAgents is treated only as reported request data. It does not authorize or execute agent termination.

## Verification

Eleven public Foundation controls serialize and parse original dictionaries, use actual String/Bool conditional casts and compose the recovered missing-false behavior. Cases cover absent flag, empty/Unicode workspace, explicit true/false, numeric0/1, rejected2/String/UInt64.max, missing/wrong workspace type and unknown extra fields. Complete canonical dictionaries include explicit false. These are public cast/serialization observations and original composition, not execution of the shipped private PurgePayload decoder or service dispatcher.

All267 Rust tests pass offline. Three new tests compare every complete native control and binary round trip; distinguish missing/default from invalid-present errors; verify required workspace/empty String, shared capability/purge numeric compatibility, outer routing, message identifier validation and namespace separation. Actual Node WASI preview1 executes those controls without filesystem preopens or inherited environment. Fresh disposable replay separately checks768 source bytes, the changed three-test suite, all11 Foundation dictionaries, actual owned Bool? layout and actual WASI. Native plist comparisons retain Bool/integer/real distinctions while ignoring dictionary ordering. Full267-test output is retained separately. Native8s and compiler/test60s deadlines bound checks. No new failed verification attempt occurred in this unit.

## Scope and continuation

Restored cancel-update checkpoint/seal and unchanged product pins; held exclusive controller lock and worked serially. Current targets were the pinned shipped image and owned public Foundation helper. Existing REA/Ghidra provider limitations were not retried unchanged; working offline analysis remained available. No Xcode MCP/private bridge, user Xcode/simulator process action, Apple app injection/re-signing, protection change or purchase occurred. Raw Apple disassembly remains local ignored research/raw; public original code/findings/own values only. User work and unrelated staging remain preserved.

The selected purge value/optional-flag subset is implemented. Other service kinds, private decoder/dispatcher runtime parity, actual purge/agent behavior, workspace identity/authorization, Canvas interaction/refresh/provider cleanup and global resource settlement remain open. Both milestones remain incomplete. Next correlate another missing protocol or usable native/rendering lifecycle boundary rather than treating successful request decoding as completed work.
