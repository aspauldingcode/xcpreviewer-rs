# Initial findings — 2026-10-08

## Scope and confidence

Inspected the installed Xcode 26.6 (17F113) and macOS 26.5.1 (25F80) on arm64. The [evidence index](../../research/evidence/xcode-26.6-macos-26.5.1.json) pins file hashes and Mach-O UUIDs. Full symbol tables, strings, disassembly, runtime dumps, and Ghidra projects remain local under ignored `research/` directories.

**Observed** means a symbol, instruction sequence, or runtime result supports the statement. **Inferred** means an architectural interpretation still needs a live session or deeper control-flow analysis. **Unknown** means not established in this investigation. No live Xcode preview messages have been intercepted or replayed.

## 1. The preview agent is a loader stub

The macOS agent is located at:

```
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/Library/Xcode/Agents/XCPreviewAgent.app/Contents/MacOS/XCPreviewAgent
```

Corresponding iPhoneOS and iPhoneSimulator agents are in their platform directories, with an unversioned `XCPreviewAgent` executable inside the app bundle. All three were inventoried, along with their `libPreviewsJITStubExecutor.a` archives.

**Observed:** the macOS agent's direct dependencies do not include a framework named `XCPreviewAgent`. Its strings and the JIT stub archive expose entry-point resolution, debug dylib loading, and JIT interposition. Useful investigation anchors include:

| Anchor | Evidence | Interpretation |
| --- | --- | --- |
| `___debug_blank_executor_main` | JIT stub exported symbol | Stub executable entry |
| `_getDebugDylibHandle` | JIT stub symbol | Debug library resolution |
| `_getDebugDylibEntryPoint` | JIT stub symbol | Application entry lookup |
| `__previews_injection_jit_link_entrypoint` | Agent string | Dynamically looked-up preview JIT hook |
| `__debug_main_executable_dylib_entry_point` | Agent string | Entry-point lookup candidate |
| `__PREVIEWS_JIT_LINK` | Agent string | Environment-dependent branch to trace |
| `__PREVIEWS_INTERPOSED_DEBUG_DLIB` | Agent string, spelling preserved | Interposed debug library branch to trace |
| `__PREVIEWS_EXECUTABLE_DYLIB_NAME` | Agent string | Executable dylib name input to trace |
| `__PREVIEWS_AGENT_SKIP_USER_ENTRY_POINT` | Agent string | Branch that keeps a run loop alive |

A string's presence does not establish that its branch ran. The loader hooks are native Mach-O/Swift mechanisms; no WASM execution path was established.

Apple documents the app stub, `NAME.debug.dylib`, and `__preview.dylib` layout and explains early interposition through the preview dylib. This is consistent with the observed loader symbols. [Apple: build product layout changes](https://developer.apple.com/documentation/xcode/understanding-build-product-layout-changes)

## 2. Host and OS sides have distinct modules

**Observed:** Xcode includes these host-side frameworks in `Contents/SharedFrameworks`:

`PreviewsFoundationHost`, `PreviewsMessagingHost`, `PreviewsDeveloperTools`, `PreviewsModel`, `PreviewsPipeline`, `PreviewsPlatforms`, `PreviewsScenes`, `PreviewsSyntax`, `PreviewsUI`, `PreviewsXcodeUI`, `PreviewsXROSMessaging`, and `PreviewsXROSServices`.

The macOS SDK exposes stubs for OS-side modules including `PreviewsFoundationOS`, `PreviewsMessagingOS`, `PreviewsServices`, `PreviewsInjection`, `PreviewsOSSupport`, and UI companions. SDK `.tbd` files establish exported signatures, not implementations.

**Observed:** `dlopen` successfully loads `PreviewsServices` and `PreviewsMessagingOS` using their `/System/Library/PrivateFrameworks/…` install paths, even though the dylib files are absent as ordinary filesystem files. Runtime enumeration provides loaded image UUIDs. Their implementations are available through the system dyld shared cache; extracting the entire cache is unnecessary for initial runtime metadata work.

**Observed:** each of two separate helper processes enumerated 36 classes from relevant images. One process loaded OS modules, the other loaded `PreviewsMessagingHost` and its dependencies. These counts are not the number of all Swift types: ObjC enumeration omits pure Swift structs, enums, and protocol descriptors.

Loading both Foundation variants explicitly in one process caused duplicate `UVExceptionError`, `UVObjCExceptionHandler`, and `UVObjCSingleFireEvent` registrations. The reproduction script keeps the variants separate.

## 3. IPC has a property-list layer with XPC adapters

**Observed in runtime metadata:** `UVPropertyList` belongs to `PreviewsServices`, subclasses `NSObject`, and conforms to `BSXPCSecureCoding` and `NSSecureCoding`. It exposes:

- `initWithDictionary:`, `dictionary`
- `initWithData:`, `data`
- `initWithXpcDictionary:`, `encodeToXpcDictionary:`
- `initWithBSXPCCoder:`, `encodeWithBSXPCCoder:`
- `initWithCoder:`, `encodeWithCoder:`

`UVRawXPCCoder` and `UVRawXPCDecoder` also appear in runtime metadata. The SDK exports `PreviewsServiceConnection.send(message: UVPropertyList, replyHandler: …)` and a one-way overload. Host `Transport.sender` accepts a lazy property list and optional reply.

**Experiment:** create a synthetic dictionary containing strings, integer, boolean, nested dictionary, array, and bytes. Instantiate `UVPropertyList`, request `data`, then decode through both `UVPropertyList` and `NSPropertyListSerialization`.

**Result:** 159-byte binary property list, `bplist00` header, Foundation format 200, both round trips equal the input. The fixture is our own synthetic data. This does **not** show that every XPC message is transported as a binary-plist byte buffer: XPC-specific encoding remains a separate path.

**Observed through native Swift getters and ARM64 disassembly:**

| Exported getter | Returned key | Unslid address in host messaging image |
| --- | --- | --- |
| `MessageTypeKey` | `type` | `0x9661c` |
| `OneWayMessageKey` | `UVOneWayMessageKey` | `0x96600` |

These identify dictionary key constants. Required envelope fields, stream negotiation, message ordering, reply IDs, and XPC object attachments remain unknown.

## 4. Rendering includes bitmap, layer-host, and IOSurface paths

**Observed:** `AgentMessageType` exposes these enum cases:

`previewInstances`, `incrementalPreviewInstances`, `render`, `incrementalRender`, `display`, `incrementalDisplay`, `layerHost`, `incrementalLayerHost`, `captureIOSurface`, `incrementalCaptureIOSurface`.

These are recovered Swift case names. Raw wire discriminants must be confirmed separately; do not assign invented numeric IDs.

**Observed:** exported initializer/getter signatures describe these payloads:

| Type | Recovered fields |
| --- | --- |
| `RenderPayload` | `bitmapDescription`, `selectableRegions`, `snapshotCornerRadius`, `scaleFactor` |
| `BitmapDescription` | `data`, `width`, `height`, `bytesPerRow`, `bitmapInfo`, `bitsPerComponent`, `bitsPerPixel`, `colorSpace` |
| `LayerHostPayload` | `contextID`, `scaleFactor`, `width`, `height` |
| `StaticLayerHostPayload` | Optional `layerHostPayload` plus `renderPayload` |

**Additional static finding:** the private `BitmapDescription.Key.rawValue` getter at `0x4a8e4` also returns `byteOrder`, which the public initializer signature does not list. Static ARM64 string recovery yields the key order:

```
data, width, height, bytesPerRow, byteOrder,
bitmapInfo, bitsPerComponent, bitsPerPixel, colorSpace
```

The byte-order getter at `0x4a1f8` returns `little` and `big`. The property-list key witnesses at `0x8d6ac` and `0x8df88` recover the corresponding render and layer-host names in the table. These are static observations; payload decoding against an actual capture remains pending.

**Implication:** a portable image adapter must preserve row stride, channel/alpha information, component depth, byte order, and color space. Treating every payload as tightly packed RGBA would discard information. Layer hosting and IOSurface capture require platform-specific handling or an explicitly chosen bitmap fallback. The existence of these cases alone does not prove the exact rendering backend used by any particular preview session.

## 5. Launch, stream identity, and code loading are separate concerns

**Observed in host exported signatures:**

- `LaunchPayload` includes workspace ID, agent descriptor and role, bootstrap mode, environment, arguments, process and binary types, built target descriptions, and an optional host audit token.
- `HostAgentSystem.AgentEndpoint.Identity` contains a stream UUID and agent PID.
- `ForwardPayload` carries an agent message type, property-list payload, PID, and optional content domain, orientation, and scene identifier.
- `JITLoadCommand.LoadDylib` contains `path`, `linkage`, and optional `symbolsPath`.

**Observed in private key witnesses:** `JITLoadCommand` uses `discriminant` and `command` keys (`0x6fde4`); its load-dylib record uses `path`, `linkage`, and `symbolsPath` (`0x70528`). The linkage getter at `0x70084` returns `strong` and `weak`. The exact command discriminant values and all JIT command variants still need recovery.

**Observed in the OS SDK:** `PreviewsInjection.EntryPoint` has methods for an `NSXPCListenerEndpoint` plus context, host message streams with instance identifiers, shell message streams, update-payload decoding, static-output encoding, and update cancellation. These are Swift protocol requirements, not ObjC XPC protocol declarations; an ObjC class dump alone cannot recover the whole interface.

**Inferred architecture to validate with a live preview:** Xcode's orchestration modules prepare targets and launch parameters; service/transport layers connect host, agent, and shell streams; injected entry points load native code and produce static or hosted outputs. We have not established a complete call graph or temporal sequence.

## 6. Consequences for the original plan

1. Start with Xcode-shipped agents and frameworks plus OS runtime metadata. A cache-extracted `XCPreviewAgent.framework` is not the observed starting point on this machine.
2. Keep the future portable preview API separate from Apple's versioned native transport. The proposed WIT is a design sketch, not the Apple protocol.
3. SwiftUI is not demonstrated to compile to WASM by this investigation. A compatible Swift view implementation or restricted API subset remains substantial separate work.
4. Native dylib injection and JIT cannot be translated into WASM simply by replacing XPC with sockets. Source compilation, framework replacement, memory representation, and rendering all need explicit designs.
5. Do not freeze an RGBA-only frame contract before resolving bitmap metadata and non-bitmap output paths.

## Next evidence required

Capture a minimal macOS `#Preview` session under a debugger, then map the host transport's send/receive boundary to decoded synthetic and real envelopes. Trace the loader's JIT hook and the `EntryPoint` stream handlers. Confirm raw message discriminants, payload key optionality, request/reply sequencing, and surface transfer. Compare a basic `Text` preview with its image capture before designing a portable protocol or renderer.

## Ghidra verification and limits

Ghidra 12.1.2 imported the arm64 messaging image, ran its Swift/ObjC metadata analyzers, decompiled seven selected functions, and saved the local project. The selected key getters agree with the native getter results. The three payload encoders call the host Foundation property-list builder through optimized closures, consistent with the recovered serialization layer.

Full automatic analysis reached the configured 120-second limit and emitted unresolved-memory warnings. Selected function decompilations and post-analysis completed; the project must be treated as partially analyzed. Swift register roles and generic arguments are not fully recovered, so pseudocode alone is not a validated type or memory layout. Full pseudocode stays local.
