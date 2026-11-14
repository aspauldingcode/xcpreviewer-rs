# Libre Canvas local previewer

Requires **macOS27+ and an Apple SDK27+**. Native builds use the installed Xcode compiler; older deployment/SDK floors are rejected. Python3/Pillow, Node.js, Cargo and `wasm32-wasip1` are needed for the local server and original WASI decoder.

```sh
python3 canvas.py examples/canvas-counter.swift --native-factory makeMyPreview
```

Open the printed loopback URL. Native mode defaults to an owned persistent AppKit/SwiftUI host. Browser clicks become native left mouse-down/up events in that process; SwiftUI owns the counter state. Use `--snapshot` to select the public ImageRenderer reference producer instead. No Simulator or Xcode session is launched.

- **UI** and **Canvas** each have independent Light/Dark/Auto controls. Auto reads the browser's live `prefers-color-scheme`. Canvas selection changes native SwiftUI appearance/environment and the painted titlebar together. UI-only changes do not rebuild the canvas.
- @2x is enabled by default. The live host rejects insufficient native backing instead of upscaling1x pixels. CSS zoom/Fit affects presentation; PNG export preserves backing pixels and includes enabled window chrome.
- Desktop titlebar/buttons are view-only decoration; hardware/AppKit material parity is not claimed. Installed iPhone/iPad/Watch profiles supply screen geometry; local mask PDFs are not distributed. Mobile profiles use **Mac SwiftUI**: UIKit widgets, safe areas, status bars and exact device-body artwork are not implemented.
- Source editing/save conflicts, filesystem watching, last-good frames, Swift highlighting, explicit refresh and auto refresh are supported. Rebuilds reset state; tested native state persists across clicks within one host. Animation/timer streaming, drag/touch/keyboard/IME and full Xcode input parity remain open.

Xcode27 project binding:

```sh
python3 canvas.py /path/to/Test.xcodeproj --native-factory makeMyPreview
# An explicitly selected zero-argument View constructor also works:
python3 canvas.py /path/to/Test.xcodeproj --native-factory RootView
```

The new `project.xcproj` JSON format is supported, including target membership, Swift language/default isolation settings, source additions/removals and selected settings refresh. Choose ambiguous targets with `--target`. Legacy `project.pbxproj`, assets, packages, scripts, entitlements and complete destination semantics remain pending. An iOS-only source API does not become available on the Mac just by selecting an iPhone frame.

`@main` and balanced plain `#Preview` registrations are removed only from owned compilation copies. The original source is preserved. A file can follow one unambiguous plain `#Preview { factory() }` when the former factory name disappears. Project binding refuses to silently move the editor to another file. The parser is a bounded lexical adapter, not a general Swift parser.

Portable import-free WASM primary-color subset:

```sh
python3 canvas.py examples/canvas-primary.swift
```

Requires LLVM `clang`/`wasm-ld` and Node.js. Override with `--clang`, `--wasm-ld`, `--node`, or `LLVM_BIN`. The complete browser allocation is verified against the build oracle. Solid rectangle2x output repeats uniform pixels; this does not implement native text or general SwiftUI in WASM.

## Checks and evidence

```sh
python3 packages/canvas-dev/test_server.py
python3 packages/canvas-dev/test_project.py
python3 packages/canvas-dev/test_device_profiles.py
python3 packages/canvas-dev/test_live_host.py
python3 -m unittest discover -s tools/re/tests -p test_swiftui_watch.py
node --check packages/canvas-dev/app.js
```

Synthetic builders/catalogs and owned child-I/O controls are labeled separately from native rendering. `native-file-check.py --project --output /private/tmp/project-refresh.json` performs bounded native filesystem changes only in disposable copies. `browser-theme-check.js` exercises independent themes with an adaptive native fixture on port57949; `browser-counter-check.js` exercises the sample counter and selected iPhone mask on port57948. They are Playwright CLI `run-code --filename` functions. The reconnect check uses intercepted API faults and navigates away before removing interception. Reload checks edit files: run only on disposable samples.

[Final OS/SDK27 evidence](../../research/evidence/libre-canvas-27-2026-11-14/README.md) distinguishes measured behavior, failures and open contracts. Native operations use the exclusive controller lock and bounded owned-process deadlines; only owned helpers are closed. Native input is authenticated, coordinate-bounded and tied to the accepted host identity. No full Canvas or all-target milestone is closed by these checks.
