# Libre Canvas local previewer

Run from the repository root:

```sh
python3 canvas.py examples/canvas-swiftui.swift --native-factory makePreview
```

Open the printed loopback URL. Requires a Mac with Xcode's Swift compiler/SDK, Python 3 with Pillow, Node.js, Rust/Cargo and the `wasm32-wasip1` Rust target. The decoder builds with the repository's locked dependencies, offline. No Simulator is started. Existing compiler/capture deadlines and exclusive native controller locking apply.

For an Xcode 27 `project.xcproj` package:

```sh
python3 canvas.py /path/to/Test.xcodeproj --native-factory makeMyPreview
```

This binds local target Swift files, the named factory, Swift language version and default actor isolation. Select ambiguous targets with `--target`. The editor saves the factory's actual source file. Other selected Swift files are watched too. `@main` is removed only in temporary compilation copies. Legacy `project.pbxproj`, packages, assets, build scripts, entitlements and non-Mac destination semantics are not integrated. Target source membership and selected language/isolation settings are re-read as project inputs change. Added/removed Swift files in target folders are discovered automatically. Moving the selected factory to a different file requires restarting to bind the new editor source; it is never silently redirected.

Controls: source syntax highlighting; auto save; auto refresh; explicit refresh; zoom; synchronized Light/Dark/Auto; native @2x Retina by default; optional view-only Mac window frame; PNG screenshot of the accepted canvas at backing resolution. Auto follows the browser host's appearance preference. Explicit SwiftUI colors retain their normal framework behavior. Titlebar buttons are painted decoration. The PNG includes that titlebar when enabled and excludes the editor and browser chrome. Zoom changes presentation, not exported resolution.

The native backend compiles an owned helper and calls public `SwiftUI.ImageRenderer`. The browser runs the original WASI frame decoder. Source changes rebuild a snapshot; this is **rebuild-and-refresh**, not in-process Swift injection. View interactions, persistent `@State`, animation/live sessions and Xcode-private lifecycle parity are not implemented. A failed compilation preserves the accepted frame. Stale edits return a conflict instead of overwriting an external edit.

A separate import-free WASM renderer executes the limited primary-color rectangle subset:

```sh
python3 canvas.py examples/canvas-primary.swift
```

It requires LLVM `clang`/`wasm-ld` and Node.js. Override tools with `--clang`, `--wasm-ld`, `--node`, or use `LLVM_BIN`. The browser verifies all output allocation bytes against the build oracle. Its @2x output repeats uniform rectangle pixels; it does not claim native text rendering or general SwiftUI support.

## Reproduce checks

```sh
python3 packages/canvas-dev/test_server.py
python3 packages/canvas-dev/test_project.py
python3 -m unittest discover -s tools/re/tests -p test_swiftui_watch.py
node --check packages/canvas-dev/app.js
node --check packages/canvas-dev/preview-worker.js
```

The Python tests use synthetic builders for server lifecycle/concurrency failures and source-binding/configuration checks. They are not native framework parity tests.

`browser-check.js` is a Playwright CLI `run-code --filename` function. First open a fresh native sample session in a disposable browser profile, then run it. It checks 600×400 point/1200×800 pixel output, highlighting, PNG download, dark mode, 1x and Auto media transitions. It saves PNGs under `/private/tmp`.

`browser-reload-check.js` **edits the bound file**. Run only on a disposable copy of `examples/canvas-swiftui.swift`. It checks native red-background edits, compile failure with full canvas readback preservation, recovery and titlebar-off output; source is restored in `finally`. Every async browser wait has Playwright's deadline. Do not run it on a user's project.

`compare_images.py REFERENCE NEW OUTPUT_DIRECTORY` converts embedded ICC profiles to sRGB, requires equal dimensions, and writes metrics plus an amplified difference image. The content crop at row 65 is specific to the supplied 1200×800 reference. It is not a general image-registration tool.

Run the bounded real-filesystem/native producer campaign on a Mac:

```sh
python3 packages/canvas-dev/native-file-check.py --output /private/tmp/canvas-native-files.json
```

It creates disposable source files, performs real atomic primary/extra-file replacements, checks every pixel in five @2x captures, deliberately rejects one compilation, exercises an adaptive view under light/dark environment, and checks observed top-level build processes exit and the watcher joins. The complete campaign has a 180-second budget, each state wait 45 seconds, and uses the native controller lock. It never writes a user project. It does not test browser delivery or private Canvas observers/resource lifetimes.

Pass `--project` to the native filesystem campaign to exercise Xcode27 target-folder discovery as well: it adds a new Swift file used by the factory, removes it to reject a build while retaining the good frame, then recreates it and asserts pixel recovery. Project manifest parsing and discovery enforce the same 1 MiB per-file, 8 MiB total and 128-source bounds as compilation.
