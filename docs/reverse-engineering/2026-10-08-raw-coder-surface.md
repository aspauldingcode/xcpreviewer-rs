# Raw coder and local surface references — 2026-10-08

Three final sealed experiments support local raw-coder behavior, IOSurface reference lifetime and the revised canvas hook on an owned helper. The [machine-readable evidence](../../research/evidence/raw-coder-surface-2026-10-08.json) publishes checks, environment identities and manifest anchors. No live preview envelope or complete canvas output is certified.

## Raw coder contract

The helper verifies the installed ObjC method encodings before calling `UVRawXPCCoder.encodeObject:forKey:` and `UVRawXPCDecoder.decodeObjectOfClass:forKey:`. Each control executes in two independent helper processes. All 28 control outcomes repeat after removing incidental exception addresses and class-cluster implementation names from comparison; wire bytes, exception name/phase and actual class-match flags remain checked.

| Owned control | Observed behavior |
| --- | --- |
| Nonempty NSData, six requested classes × three decoding keys | All 18 return the exact NSData payload from fixed XPC field `data` |
| Requested NSString, NSNumber, NSArray or NSDictionary | All 12 mismatches still return NSData; supplied class is not enforced in these controls |
| Encode using key `owned`; decode with `owned`, `alternate` or `data` | Same fixed field and bytes; provided key is ignored |
| Second write under a different key | Replaces the fixed `data` slot; last payload returned |
| Empty NSData or nil object | Zero-length XPC data encoded; decoder returns nil |
| Missing `data` or string-valued `data` | Decoder returns nil |
| NSString, NSNumber, BOOL NSNumber, NSArray, NSDictionary encoding | `NSInvalidArgumentException` during encode; object lacks `bytes` selector |

The property-list wrapper's behavior is therefore explained by a narrow raw-data slot, rather than a general keyed archive. This is a scoped inference from owned experiments. A selector containing `decodeObjectOfClass` does not by itself establish class enforcement. The observed image UUID remains `FFFB683F-5943-3C25-91B2-72D6E5174FA3`. These results are not a security assessment of arbitrary service inputs.

## IOSurface bytes and lifetime

The public [IOSurfaceCreateXPCObject](https://developer.apple.com/documentation/iosurface/iosurfacecreatexpcobject(_:)) and [IOSurfaceLookupFromXPCObject](https://developer.apple.com/documentation/iosurface/iosurfacelookupfromxpcobject(_:)) APIs provide the owned resource control. Apple documents that the XPC object holds a surface reference and lookup recreates a reference without destroying the port. The experiment checks the following order explicitly:

1. Allocate an owned single-plane BGRA surface; initialize the full allocation and write a deterministic CPU pattern under a surface lock.
2. Create its local XPC holder, then release the original surface reference.
3. Look up two surface references; confirm identity and exact initial bytes.
4. Release the XPC holder, mutate one byte through the first reference, then release that reference.
5. Read through the surviving second reference; independently check the expected mutation and unchanged row padding, then release it.

All four shapes (`1×1`, `3×2`, `17×3`, `33×7`) pass. Each runs twice in separate processes, with identical before/after payloads. This compares outputs across processes; it does **not** send the resource between processes. Python independently predicts each byte, and the streaming comparator checks the actual native snapshots against those expectations.

All four shapes have padded rows on this baseline. The published [3×2 golden](../../tools/re/fixtures/SurfaceOracle/manifest.json) has a 128-byte stride, 12 visible bytes per row and 116 initialized padding bytes per row. Its captured region is 256 bytes; the allocation is 16,384 bytes. Treating this as packed width×height×4 pixels would drop 232 row-padding bytes and misread the second row. The before/after files differ at exactly one byte and four bits, according to the prescribed XOR mutation. No padding or unused allocation bytes are read before initialization.

Open cases: cross-process transfer and peer exit, surface reuse, concurrent ownership/release, GPU completion/fences, multiple planes, other formats, orientation and color spaces. The local reference experiment supplies an attachment test primitive; it does not recover Apple's canvas attachment protocol.

## Native canvas and instrumentation

Native Refresh on the existing owned PreviewLab workspace builds and launches its mapped executable. UI inspection shows Baseline and Literal change window chrome but blank content. No accepted PNG or pixel-stability claim results. A one-second owned-process stack sample places the main thread in AppKit's event loop through SwiftUI, PreviewsInjection and XOJITExecutor; that sample does not identify the cause of blank content.

The original monitor remains pending in instrumentation attach during its 180-second observation and saves partial diagnostics. A revised ten-second cancellable attach test stops before session creation with `operation was cancelled`; it captures zero messages. No user Xcode, simulator or preview process is terminated, and no settings or system protections are changed.

The monitor now bounds synchronous Frida operations, records attach/load phases, retains a returned session before script creation/loading and attempts detach even when unload fails. Partial sessions no longer count as successfully instrumented processes. Cleanup status reflects pending threads/errors. The module observer defers runtime hook installation outside synchronous loader notifications; this is defensive scheduling, not a proven fix for the native attach blocker.

The deferred hook passes a separate owned-helper control: hook readiness precedes six known plist calls, all six typed payloads match, with zero script errors. The first readiness attempt failed because the helper waited for resume before loading the framework needed for the hook. That sealed failure is preserved. The corrected fixture preloads the framework before its resume gate. Hook diagnostics now save on failure too.

## Recursive continuation

The controller has 19 reviewed adapters and 19 MCP tools. The expanded suite passes 62 tests, covering raw-coder payload/class/key checks, exact surface geometry/padding, mutation identity, golden hashes, cancellation and cleanup after unload failure. Scoped claims and the evidence planner consume verified final runs. New planner outcomes keep raw coding narrow and require actual interprocess surface lifecycle work.

Continue with an owned sender/receiver resource oracle before claiming attachment replay. For the canvas path, distinguish process launch, instrumentation session creation, hook readiness, rendering and accepted pixels. Repeated identical bridge/attach failures should not consume the campaign budget; require a changed precondition or a discriminating control.
