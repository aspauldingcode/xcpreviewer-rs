# SwiftUI source capture

On a Mac, capture an ordinary SwiftUI view factory and open the resulting file in the reconstructed [browser viewer](../browser-preview/README.md):

```sh
python3 tools/re/swiftui-preview/capture.py tools/re/swiftui-preview/Sample.swift \
  --width 320 --height 200 --scale 2 --output /tmp/swiftui-preview.bplist
```

Serve the captured file without a file-picker step:

```sh
python3 tools/re/browser-preview/serve.py --sample /tmp/swiftui-preview.bplist
```

Open the printed loopback URL and choose **Open sample**. Recapture after editing the source, then choose Open sample again to load the new frame. Failed compilation/rendering keeps the last good payload available.

The default source contract is an accessible zero-argument `makePreview() -> some View` factory. `--factory Namespace.function` selects another explicit name. Alternatively, select an accessible PreviewProvider type with `--provider Namespace.Type`. The compiler enforces PreviewProvider conformance and the wrapper reads its public `previews` value on the main actor. `--factory` and `--provider` are mutually exclusive. The complete returned view is rendered as one composition; grouped previews are not enumerated or split into variants, and preview modifiers such as device/layout/display name do not configure the capture.

```sh
python3 tools/re/swiftui-preview/capture.py MyView.swift \
  --provider MyView_Previews --width 320 --height 200 --output /tmp/provider.bplist
```

The command compiles the supplied source and evaluates the selected factory or provider getter in an owned Mac process; use source you intend to run. It captures one initial frame with public SwiftUI ImageRenderer, converts it into an owned sRGB premultiplied BGRA bitmap and writes the recovered RenderPayload schema. The browser performs the reconstructed decoding and bitmap conversion in WASM. An optional `--reference-png /tmp/reference.png` exports the native renderer's diagnostic image.

The producer requires macOS13 or newer and the installed Swift compiler/SDK. This is a Mac producer feeding a portable viewer; it does not compile SwiftUI in WASM. The generated capture executable targets macOS13; newer view APIs need normal availability guards. Visual compatibility behavior follows that deployment target and the current native environment. Only a single source file and standard SDK imports are supported. There is no project/package build inference, automatic PreviewProvider selection, device frame, selectable view hierarchy, interactive event forwarding, state migration or native Canvas session. Views backed by platform views may not appear in ImageRenderer. Source-level selectable regions are intentionally empty.

Explicit size/scale controls bound the rendered frame; the view receives that display scale and is clipped to that size. Limits are original product policy: 1 MiB source, 2,048 points per dimension, scales 1 through 4, 32 MiB pixels, 64 MiB artifacts, 30-second compile and at most 8-second render. `--runtime-seconds` can shorten the render deadline. Timeout terminates only the process group created by this invocation. Compiler/render/validation failures preserve the existing payload. Payload writes are atomic; optional PNG writes are individually atomic and are not a transaction with the payload. Concurrent last-writer ordering, dynamic resource/environment capture and native provider lifecycle are separate work.

The JSON receipt records explicit factory/provider selection, compiler identity, exact source/generated-renderer hashes, dimensions and payload/native-image hashes. The format and bitmap boundary reuse qualified reconstruction behavior; the choice of public renderer, factory contract, clipping, limits and file publication are original implementation policy. Both reconstruction milestones remain incomplete.

## Discover active #Preview declarations

```sh
python3 tools/re/swiftui-preview/discover.py MyView.swift
```

On macOS14 or newer, this separate command compiles the source with the installed Swift macro plugin, finds actual generated PreviewRegistry conformances and invokes their public MainActor makePreview methods. JSON lists runtime display names, source line/column, registry identifiers and compiler/source hashes. Entries sort by line/column. File IDs describe the temporary PreviewDiscovery module and Source.swift; the top-level source path identifies the actual supplied file. Registry names are compiler-generated identifiers, not stable saved IDs. Only active declarations for this Mac target and the observed expansion format are covered. PreviewProvider types are not automatically enumerated.

Discovery executes owned source initializers and registry constructors; use source you intend to run. It does not intentionally invoke stored view-body closures. Native controls include bodies that would trap if invoked. A checked reflected Optional<String> display-name field is required; missing or incompatible name fields fail explicitly. Each compiler phase has a 30-second deadline; the owned executable has at most 8 seconds. Source is bounded to 1 MiB, collected compiler/runtime output is checked against 8 MiB and discovered registries against 64. Timeouts cancel only the process group created by the command.

Listing does not invoke preview bodies. A separate, runtime-qualified capture option below extracts the selected body; registry discovery and rendering remain separate execution stages.

## Capture a plain #Preview

```sh
python3 tools/re/swiftui-preview/discover.py MyView.swift
python3 tools/re/swiftui-preview/capture.py MyView.swift --preview-index 0 \
  --width 320 --height 200 --scale 2 --output /tmp/registry.bplist
python3 tools/re/browser-preview/serve.py --sample /tmp/registry.bplist
```

The index is zero-based in the discovery output sorted by source position. Capture performs discovery again, verifies the original source/compiler fingerprints and invokes the selected generated registry in a new owned process. Discovery constructs all active registries to read names, while only the selected view-body closure is called for capture. Source initializers and constructor side effects therefore run in separate discovery/capture processes. Changes to source can change indices and generated names; names are not persistent identifiers.

This path requires an arm64 Mac and the specifically qualified macOS 26.5.1 SwiftUI/DeveloperToolsSupport runtime UUID pair. The executable targets macOS14. Runtime UUIDs, exported symbol offsets, body size/stride/alignment, field offset, destructor, closure type/code identity and closure size are checked before invoking the private body closure/getter. Unmatched profiles fail instead of using guessed layouts. The original assembly adapter and public dyld identity helper contain no copied Apple instruction bytes. After extraction, a copied public View is rendered with ImageRenderer through the same bitmap/WASM path. The native body value is destroyed once before its copied View is rendered. Native receipt fields and adapter-source hashes identify this path.

Only the observed single-preview structure with no explicit traits is accepted. Trait-bearing, parameterized and other preview structures fail; device/layout/variant metadata and interactive state are not applied. Unsupported selection/runtime/shape, compilation or rendering preserves the last good payload and optional PNG. Each compile phase remains bounded to 30 seconds and each owned native stage to the configured deadline (at most 8 seconds). The installed compiler macro plugin needs normal host process access; an enclosing restricted sandbox may block its own sandbox initialization. No Xcode app or simulator process is modified. Native Canvas/session/resource settlement and both milestones remain open.

## Recapture after source edits

```sh
python3 tools/re/swiftui-preview/watch.py MyView.swift --preview-index 0 \
  --output /tmp/registry.bplist --width 320 --height 200 --scale 2
python3 tools/re/browser-preview/serve.py --sample /tmp/registry.bplist
```

Run the server in another terminal. Enable **Follow sample** in the viewer to display published captures automatically, or choose **Open sample** after a `published` JSON event for a one-time load. All factory/provider/preview-index, size, scale, native deadline and optional reference-PNG options are shared with capture.py. `--once` captures one snapshot and exits. Stop with Ctrl-C; an active compiler/render/discovery process group created by this command is killed and reaped.

The watcher polls content every 0.25 seconds and waits for 0.5 seconds of unchanged content before attempting a revision. `--interval` (0.05–10 seconds) and `--debounce` (0–10 seconds) adjust this policy. It compiles one immutable source snapshot at a time. If source bytes differ when capture returns, the scratch output is discarded and the latest revision is considered next. Failed or missing source revisions preserve the last good output; a failed revision is attempted again only after content changes or the watcher restarts. JSON events distinguish capturing, published, superseded, capture-error and source-error. A continuous stream of edits can postpone publication indefinitely.

Content comparison immediately before replacement is not a filesystem transaction with concurrent edits; an edit after the comparison is observed on a subsequent poll. Optional PNG and payload are individually atomic, not a pair transaction. One watcher should own a given output path. This is original reconstruction policy for the single-file Mac producer, not recovered Xcode scheduling, hot reload, interactive state preservation, project dependency watching or native Canvas lifecycle behavior.
