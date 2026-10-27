# Local preview viewer

From the repository root, run `python3 tools/re/browser-preview/serve.py`, then open the printed loopback URL. Requires Python 3, Rust, and the installed `wasm32-wasip1` target. The offline build uses the locked workspace dependencies. A prebuilt owned executable can be supplied with `--wasm /absolute/path/canvas-frame.wasm`; `--port` selects a fixed local port.

Choose **Open sample** or open a captured RenderPayload binary plist. Files are read inside the browser and are not uploaded. Select a region using its outline or list entry, then adjust zoom. The server exposes only the six owned assets and accepts no file uploads. The worker has a ten-second deadline, a 256 MiB build-time linear-memory ceiling, bounded input/output, and exactly five stdin/stdout WASI imports. Unknown imports fail explicitly.

The Rust decoder, bitmap conversion and point-space geometry reuse the qualified reconstruction. The display packet (`XCPV` version 1), file bounds, zoom, region ordering, selection and error presentation are original UI policy. Accessibility blobs remain opaque; the viewer shows regions without interpreting those blobs. Unsupported pixel formats fail explicitly. Browser color conversion and alpha rounding are separate from native bitmap decoding; the opaque sample has byte-exact actual Canvas readback evidence.

This surface displays existing bitmap captures. It does not compile SwiftUI, invoke providers, render arbitrary native views, dispatch Apple interactions, or establish native Canvas parity. Both reconstruction milestones remain incomplete. Open `/?verify=1` for page-owned Canvas readback hash attributes used by the recorded manual browser verification.
