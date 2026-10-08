Here is the concrete, end-to-end plan. It stitches together every component we've discussed into a single, buildable architecture.

---

## The Concrete Plan: Liberating the Xcode iDevice Preview Pipeline

### Architecture Overview

The liberated previewer replaces Apple's simulator-dependent stack with a portable WASM-based pipeline:

| Component | Apple's Version | Liberated Version |
|---|---|---|
| **IPC** | XPC (Mach kernel) | Unix domain sockets / gRPC |
| **Runtime** | iOS Simulator | WASM interpreter (wasm3) |
| **Rendering** | Metal / GPU | Canvas2D / software rasterizer |
| **Build** | xcodebuild | xtool (forked omarchy-apple-dev) |
| **Preview Host** | XCPreviewAgent in simulator | WASM module |
| **Reverse Engineering** | N/A | GhidraVibe MCP |

The critical innovation is compiling the SwiftUI view logic to **WebAssembly** instead of native iOS binaries, then rendering it through a portable WASM runtime that runs anywhere.

---

## Phase 1: Environment Setup (Days 1–3)

### 1.1 Install GhidraVibe MCP

GhidraVibe is a Ghidra fork with a native GUI (SwiftUI on macOS, GTK on Linux), first-class MCP support, and built-in dyld shared cache extraction and analysis. It lets an AI agent drive decompilation, navigation, and Apple-specific helpers through MCP.

```bash
# Clone GhidraVibe
git clone https://github.com/aspauldingcode/GhidraVibe.git
cd GhidraVibe

# Build (requires Ghidra 12.0.3+ and Java 21)
./gradlew build

# Start the MCP server (exposes Ghidra tools to your AI agent)
./gradlew runMcpServer --port 8080
```

Configure your AI agent (Cursor, Claude Desktop, etc.) with the MCP server endpoint. The agent can now issue tool calls to Ghidra for decompilation and analysis.

### 1.2 Install the xtool Toolchain (omarchy-apple-dev)

`omarchy-apple-dev` enables building and deploying iOS SwiftUI apps from Linux on Apple Silicon, with no Xcode and no macOS in the loop. The heavy lifting is done by **xtool**, which handles SDK extraction, build planning, signing, and device communication on non-Apple platforms.

```bash
# Clone and install
git clone https://github.com/joshuaswarren/omarchy-apple-dev
cd omarchy-apple-dev
./install.sh

# Verify the toolchain
xtool --version
# Should output a version compatible with Swift 6.4.0+

# Create a test project
xtool new HelloOmarchy
cd HelloOmarchy
xtool dev build
# Produces xtool/HelloOmarchy.app (arm64 Mach-O)
```

### 1.3 Install SwiftWasm and wasm3

```bash
# Install SwiftWasm toolchain (for compiling Swift to WASM)
# Follow instructions at https://swiftwasm.org/getting-started/

# Install wasm3 (C library + CLI)
git clone https://github.com/wasm3/wasm3.git
cd wasm3
mkdir build && cd build
cmake .. && make
sudo make install
```

wasm3 provides bindings for Python3, Rust, C/C++, Go, Zig, Perl, Swift, and .NET. For Swift on Apple platforms, use the `wasm-interpreter-apple` package (a Swift wrapper around `CWasm3`).

### 1.4 Install the Preview Protocol Analysis Toolkit

```bash
# dyld shared cache extractor (choose one)
brew install keith/formulae/dyld-shared-cache-extractor
# OR use the Swift reimplementation:
git clone https://github.com/swiftbin/dyld-shared-cache-extractor

# Extract Xcode's preview binaries
dyld-shared-cache-extractor /System/Library/dyld/dyld_shared_cache_arm64e /tmp/extracted
```

---

## Phase 2: Reverse-Engineering the Xcode Preview Pipeline (Days 4–14)

### 2.1 Extract and Load Preview Binaries into Ghidra

Xcode's preview system relies on two essential apps: **`Xcode Previews`** (the canvas host) and **`XCPreviewAgent.app`** (a daemon that loads your code and talks to Xcode Previews through XPC).

```bash
# From the extracted dyld shared cache, locate:
#   /tmp/extracted/System/Library/PrivateFrameworks/XCPreviewAgent.framework
#   /tmp/extracted/Applications/Xcode.app/Contents/.../Xcode Previews.app

# Load into GhidraVibe via MCP
# (AI agent issues tool calls to load the binaries and begin analysis)
```

### 2.2 Decompile the XPC Protocol

Use GhidraVibe's MCP tools to decompile `XCPreviewAgent` and identify:

1. **The XPC message handlers** — the entry points that receive preview compilation requests from Xcode
2. **The preview host loading mechanism** — how the compiled dynamic library is injected into the agent process
3. **The rendering command format** — what data structure the agent sends back to Xcode Previews for display

**Key files to analyze:**
- `XCPreviewAgent.app` binary (arm64e)
- `XCPreviewAgent`'s linked frameworks (UIKit, CoreGraphics, Metal)
- The PreviewHost dynamic library template

### 2.3 Document the Protocol as WIT

Create a WebAssembly Interface Types (WIT) specification that captures the preview protocol:

```wit
// preview-protocol.wit
package preview:protocol

interface preview-host {
    // Compile Swift source to a preview host module
    compile-preview: func(source: string) -> result<wasm-module, compile-error>

    // Render a preview frame
    render-preview: func(module: wasm-module, viewport: viewport) -> frame

    // Live reload notification
    update-preview: func(module: wasm-module) -> preview-id
}

record viewport {
    width: u32,
    height: u32,
    scale: f32,
}

record frame {
    width: u32,
    height: u32,
    pixels: list<u8>,  // RGBA
}
```

This WIT becomes the contract between the preview host and the rendering runtime.

---

## Phase 3: Building the Cross-Platform Toolchain (Days 15–30)

### 3.1 Fork xtool for WASM Output

Modify `omarchy-apple-dev`'s xtool to support a new output target: `wasm32-wasi` instead of `arm64-apple-ios`.

**Key changes to xtool's build pipeline:**
- Add a `wasm` platform to the build planner
- Replace the iOS SDK linking step with SwiftWasm linking
- Use the `swiftwasm-pad`'s `PreviewSystem` package, which provides prebuilt `.swiftmodule` and wasm library files for compiling Swift to WebAssembly

The `swiftwasm-pad` project demonstrates this with a `CompileAPI` backend that compiles `.swift` into WebAssembly object files. Its `PreviewSystem` provides the necessary `.swiftmodule` files for user code compilation.

### 3.2 Implement the PreviewSystem Swift Package

Create a Swift package that provides the SwiftUI-compatible API surface needed for preview compilation:

```
PreviewSystem/
├── Sources/
│   └── PreviewSystem/
│       ├── SwiftUICompatibility.swift   // Reimplemented SwiftUI API
│       ├── DrawingCommands.swift        // Binary drawing command encoder
│       ├── WASMRuntime.swift           // wasm3 integration
│       └── PreviewHost.swift            // Main entry point
├── Package.swift
└── build-script.sh                      // Compiles to wasm32-wasi
```

This package follows the model established by **Dactyl**, which compiles Swift apps to WebAssembly, sends binary drawing commands through linear memory, and paints them in the browser with Canvas2D. Dactyl's preview engine is a reimplementation of SwiftUI written in Swift, with key frameworks ported to run on WASM.

### 3.3 Implement the WASM Preview Host

The preview host is a WASM module that:
1. Contains the compiled SwiftUI view logic
2. Outputs drawing commands through linear memory
3. Is instantiated by a WASM runtime (wasm3)

**Core WASM exports (C ABI):**

```c
// preview_host.h
typedef struct {
    uint32_t width;
    uint32_t height;
    uint8_t* pixel_buffer;  // RGBA
} preview_frame_t;

// Initialize the preview host with SwiftUI source
int preview_init(const char* source_code);

// Render a frame into the output buffer
int preview_render(preview_frame_t* out_frame);

// Handle a touch/gesture event
int preview_handle_event(uint32_t event_type, float x, float y);

// Free resources
void preview_free(void);
```

**wasm3 Swift integration** (for the host application):

```swift
import WasmInterpreter

let interpreter = try WasmInterpreter(module: wasmBinary)
let renderFunc = try interpreter.findFunction("preview_render")
var frame = PreviewFrame(width: 390, height: 844)
let result = try renderFunc.call([&frame])
// frame.pixelBuffer now contains the rendered RGBA data
```

The `wasm-interpreter-apple` package provides a clean Swift interface to wasm3 for Apple platforms.

---

## Phase 4: Language Bindings (Days 31–45)

### 4.1 C API Core

Write the previewer core in C (or Zig with C ABI) to ensure maximum portability:

```c
// preview_core.h — the universal C API

// Lifecycle
preview_context_t* preview_create(void);
void preview_destroy(preview_context_t* ctx);

// Compilation (calls xtool → SwiftWasm)
int preview_compile(preview_context_t* ctx, const char* swift_source);

// Rendering (loads WASM, calls preview_render)
int preview_render(preview_context_t* ctx, preview_frame_t* out_frame);

// Live reload
int preview_watch(preview_context_t* ctx, const char* source_path,
                  preview_update_callback_t callback);

// MCP server
int preview_mcp_start(preview_context_t* ctx, uint16_t port);
```

### 4.2 Bindings for Each Language

| Language | Binding Approach | Package Name |
|---|---|---|
| **Rust** | `bindgen` → safe wrapper crate | `previewer-rs` |
| **Swift** | Swift C interoperability | `PreviewerKit` |
| **Python** | `ctypes` or `cffi` | `py-previewer` |
| **Zig** | `@cImport` | `zig-previewer` |
| **C** | Direct linking | `libpreviewer` |

**Rust example (using wasm3-rs):**

```rust
use wasm3_rs::*;

let mut ctx = preview_create();
preview_compile(ctx, r#"
import SwiftUI
struct ContentView: View {
    var body: some View {
        Text("Hello, WASM!")
    }
}
"#);

let mut frame = PreviewFrame::new(390, 844);
preview_render(ctx, &mut frame);
// frame.pixels now contains the rendered image
```

**Python example (using pywasm3):**

```python
from previewer import PreviewContext

ctx = PreviewContext()
ctx.compile("""
import SwiftUI
struct ContentView: View {
    var body: some View { Text("Hello from Python!") }
}
""")
frame = ctx.render(width=390, height=844)
frame.save("preview.png")
```

### 4.3 MCP Server for AI Agents

Wrap the C API in an MCP server that exposes previewer tools to any MCP-compatible agent:

```json
// MCP tool schema
{
  "name": "render_swiftui_preview",
  "description": "Compile SwiftUI source to WASM and render a preview frame",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source": { "type": "string" },
      "width": { "type": "integer", "default": 390 },
      "height": { "type": "integer", "default": 844 }
    },
    "required": ["source"]
  }
}
```

---

## Phase 5: Integration and Testing (Days 46–60)

### 5.1 End-to-End Pipeline

```
[SwiftUI Source]
    → [xtool fork: compile to wasm32-wasi]
    → [PreviewSystem package: SwiftUI → drawing commands]
    → [WASM module: preview_host.wasm]
    → [wasm3 runtime: instantiate + call preview_render]
    → [Canvas2D / framebuffer: rendered pixels]
    → [MCP server: return image to client]
```

### 5.2 Test Matrix

| Test | Validation |
|---|---|
| **Unit** | `preview_compile` produces valid WASM for simple views |
| **Integration** | Full pipeline renders `Text("Hello")` correctly |
| **Protocol** | WIT interface matches XCPreviewAgent's message format |
| **Cross-platform** | Runs on Linux (x86_64, ARM64), macOS, Windows |
| **Language bindings** | All 5 bindings produce identical output |
| **Live reload** | File watcher triggers recompile and re-render |

### 5.3 Reference Comparison

Use a macOS machine with Xcode to capture reference screenshots of SwiftUI previews, then compare pixel-by-pixel with the WASM-rendered output. Dactyl has demonstrated that this fidelity is achievable for basic views.

---

## Phase 6: Packaging and Distribution (Days 61–75)

### 6.1 Docker Image

```dockerfile
FROM swift:6.4-jammy

# Install xtool
RUN git clone https://github.com/joshuaswarren/omarchy-apple-dev /opt/omarchy
RUN cd /opt/omarchy && ./install.sh

# Install SwiftWasm
RUN curl -sL https://swiftwasm.org/install.sh | bash

# Install wasm3
RUN git clone https://github.com/wasm3/wasm3 /opt/wasm3
RUN cd /opt/wasm3 && mkdir build && cd build && cmake .. && make && make install

# Install previewer
COPY . /opt/previewer
RUN cd /opt/previewer && make install

EXPOSE 8080
ENTRYPOINT ["previewer", "--mcp-port", "8080"]
```

### 6.2 CLI Tool

```bash
# Compile and render a preview
previewer render --source ContentView.swift --width 390 --height 844 --output preview.png

# Watch mode
previewer watch --source ContentView.swift --output preview.png

# Start MCP server
previewer mcp --port 8080
```

### 6.3 Documentation

- **README**: Setup instructions for each platform
- **ARCHITECTURE.md**: The pipeline and protocol specification
- **BINDINGS.md**: API reference for each language
- **REVERSE_ENGINEERING.md**: Findings from GhidraVibe analysis

---

## Critical Path and Dependencies

```
Phase 1 (Setup)
    └── Phase 2 (Reverse Engineering) ← GhidraVibe MCP
            └── Phase 3 (Toolchain) ← xtool fork + SwiftWasm
                    └── Phase 4 (Bindings) ← wasm3 + C API
                            └── Phase 5 (Testing)
                                    └── Phase 6 (Packaging)
```

**Risk factors:**
- **XPC protocol complexity**: The XPC message format may require more reverse-engineering than anticipated. Mitigation: Focus on the high-level message semantics rather than byte-level replication.
- **SwiftUI API coverage**: Reimplementing enough of SwiftUI for real-world previews is substantial. Mitigation: Start with the core views (Text, VStack, HStack, ZStack, Button, Image) and expand incrementally.
- **WASM performance**: Rendering complex views through a WASM interpreter may be slower than native. Mitigation: Use wasm3's fast interpreter and optimize the drawing command path.

**The bottom line**: This is not a weekend project, but it is a well-defined engineering problem. The pieces exist in isolation — GhidraVibe for reverse-engineering, xtool for cross-platform builds, SwiftWasm for compilation, and wasm3 for portable execution. The work is in the **glue**: a WASM preview host that speaks the Xcode preview protocol and renders SwiftUI without Apple's simulator. That's the liberation.
