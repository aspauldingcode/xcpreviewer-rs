# Free local reverse engineering toolkit

The repository now contains a bounded RE executor, an MCP server, native tracing fixtures and evidence validation. It uses the installed Xcode and GhidraVibe plus free Python packages. No paid analysis service or API key is required. A model controlling these tools has its own inference costs; this toolkit does not provide free model inference.

## Components and choices

| Component | Selected tool and implementation | Status |
| --- | --- | --- |
| Experiment controller | Python standard library, validated queue, dependency selection, exclusive lock, watchdog, checkpoint | Implemented |
| Agent interface | Local stdio MCP: 19 `re_*` tools | Implemented and protocol-tested |
| Static inventory | Xcode `nm`, `otool`, `swift-demangle`, SHA-256 and UUID collection | Implemented; 18 images/archives and eight SDK stubs on this baseline |
| Decompiler | Existing Ghidra 12.1.2; isolated headless project and selected Java post-script | Implemented; bounded partial-analysis handling |
| Interactive analysis tools | Existing GhidraVibe MCP extension and program engine | Local lifecycle, schema discovery, health gate and reviewed read-tool allowlist implemented; HTTP cache discovery and stdio health tested |
| Native debugger | Xcode LLDB Python API | Six owned calls, arguments, image UUIDs and offsets captured |
| Runtime instrumentation | Frida 17.23.1 and frida-tools 14.11.0 | Six owned native calls and six synthetic serialized plists captured |
| ObjC metadata | Owned clang helper, separate host and OS processes | Implemented |
| Swift investigation | Bounded Mach-O nominal/field descriptor reader, native key getters, Ghidra and LLDB | 351 nominal types and 998 fields on this image; unresolved symbolic/indirect references stay unknown |
| Payload decoding | Foundation/UVPropertyList probes and Python `plistlib` decoder | Implemented; bytes preserved as base64, not silently discarded |
| Local XPC coding | Owned ObjC helper, typed corpus, direct-data controls, prefix sweep and shrinker | 32 exact payload round trips; malformed-input fallback reproduced; no service connection |
| Message raw strings | Bounded ARM64 getter interpreter and Swift field descriptors | Ten static returns corroborated; live envelope validation remains open |
| Native reference | Owned SwiftUI `#Preview` source plus ImageRenderer executable | PNG capture implemented; this is not a canvas trace |
| Differential check | Pillow RGBA diff, explicit geometry/color-profile checks | Implemented and tested |
| Evidence provenance | Frozen sources, sealed hashes, external manifest anchors, SQLite/FTS evidence graph and scoped claims | Implemented |
| Actual Xcode control | Installed `xcrun mcpbridge`, owned macOS project, RenderPreview adapter | Discovery/build/controlled capture implemented; native build validated; Xcode schema request currently times out |
| Live canvas IPC / resource replay | Correlated requests/replies, IOSurface/XPC attachment lifetimes | Next campaign; not recovered yet |

Frida complements LLDB: interception can observe repeated serialization calls with less breakpoint overhead, while LLDB provides debug variables and instruction-level control. The fixture uses a narrow ObjC runtime API hook, avoiding guesses about Swift calling conventions. Frida 17's bare script API does not bundle language bridges; the current hook needs no extra bridge. More general ObjC or Swift instrumentation can use the upstream bridges and a pinned bundled script. Sources: [Frida JavaScript API](https://frida.re/docs/javascript-api/), [Frida bridges](https://frida.re/docs/bridges/), [LLDB Python API](https://lldb.llvm.org/use/tutorials/python-embedded-interpreter.html).

Other useful free tools are already available: `dyld_info` for Mach-O/cache metadata, `xctrace` for Instruments recordings, `simctl` for a later pinned simulator campaign, and native crash/unified logs. Existing GhidraVibe dyld helpers can locate and import cache images. [ipsw](https://github.com/blacktop/ipsw) is an optional additional cache/ObjC/Swift metadata toolbox ([cache guide](https://blacktop.github.io/ipsw/docs/guides/dyld/)); it is not installed or required here. Rizin/radare2, angr, Qiling and additional MCP wrappers are optional future alternatives, rather than dependencies for this campaign. Prefer one working path for each required capability.

## Setup and execution

From the repository root:

```sh
sh tools/re/bootstrap.sh
research/venv/bin/python tools/re/agent.py doctor
research/venv/bin/python tools/re/agent.py services start
research/venv/bin/python tools/re/agent.py run --max-experiments 8 --minutes 45
research/venv/bin/python tools/re/agent.py report
```

Bootstrap installs the pinned free packages into ignored `research/venv/`. The controller itself uses only the standard library; Frida, Pillow and schema-test dependencies are optional outside their respective operations. Ghidra and Xcode are not downloaded by bootstrap. This machine's existing GhidraVibe and Semeru/OpenJ9 21 installations are detected automatically. Other installations should supply ignored `research/local-config.json`, based on the example, with actual Ghidra and supported JDK paths. Do not copy placeholder paths unchanged. The current automatic service launcher targets the installed GhidraVibe packaging; ordinary Ghidra can use the headless adapter without the MCP services.

`services start` launches an owned loopback program engine and extension, with logs and process identities under `research/state/services/`. It reuses healthy services and does not install launch agents. `services status` inspects them; `services stop` stops only processes whose saved identities still match. Headless experiments use separate projects and do not mutate the interactive engine's active program. A healthy engine does not imply a program has been imported.

The seeded queue targets the measured Xcode/OS baseline. Changed versions require reviewed expectations and symbol/address updates. A session defaults to eight experiments, 45 minutes and 1 GiB of new artifacts. Each experiment has its own timeout and artifact limit. Artifact limits are sampled and can briefly overshoot. A process-group watchdog bounds the whole worker tree; Ghidra's internal 120-second analysis limit alone does not bound startup/import/save time. [Ghidra headless API](https://ghidra.re/ghidra_docs/api/ghidra/app/util/headless/HeadlessAnalyzer.html).

Successful matching runs are skipped on resume only when experiment/environment/source identities and sealed artifact hashes still match. Failed or incomplete observations cannot satisfy dependencies. Each experiment is attempted at most once per session. Changed probes produce new evidence directories. Runs remain under ignored `research/runs/`; `verify RUN_ID` checks a sealed run, and `next` lists ready work. Live PID recovery is conservative and refuses to kill an unidentified process.

## MCP interface

Use this generic stdio server command in an MCP-capable client, substituting the absolute checkout path:

```json
{
  "mcpServers": {
    "preview-re": {
      "command": "/absolute/checkout/research/venv/bin/python",
      "args": ["/absolute/checkout/tools/re/agent.py", "serve"]
    }
  }
}
```

The server advertises `re_doctor`, `re_status`, `re_report`, `re_next`, `re_run`, `re_verify`, `re_verify_anchor`, `re_compare`, `re_propose`, `re_index`, `re_search`, `re_graph`, `re_artifact`, `re_response`, `re_claim`, `re_plan`, `re_engine_tools`, `re_engine_read` and `re_campaign`. `re_run` runs one ready reviewed experiment. `re_propose` validates a fixed adapter, bounded parameters and the complete dependency graph; it cannot execute arbitrary shell commands. Proposing an experiment changes the reviewed queue, so inspect and commit useful proposals. The agent reads bounded summaries, proposes discriminating experiments and interprets results; the executor handles process control and evidence. It is not a self-improving background model daemon.

GhidraVibe tool schemas are discovered live. Every call is preceded by `vibe_health`; an unhealthy program engine fails the experiment. The older extension adapter defaults to health only. The program-engine adapter separately discovers actual GET/POST contracts, exposes a fixed read-only operation allowlist, requires explicit program identity, and bounds query sizes. Imports/function preparation are restricted to the saved repository-owned engine and performed by the reviewed connected adapter. Binary path, hash, UUID and function offset tie Frida events to decompilation and references. An optional `ghidra_mcp_command` array selects an existing local stdio bridge instead of HTTP. The bridge client supports JSON-lines and incoming Content-Length framing.

Xcode's separate built-in bridge is worth using for actual preview orchestration. Inspect it without project mutations:

```sh
research/venv/bin/python tools/re/xcode_tools.py
```

This lists schemas from an already running service and saves diagnostics locally. It does not enable settings, launch agents, fetch authentication tokens or select someone else's project. Only call a discovered preview tool after selecting the owned fixture project and checking its actual schema. The installed bridge's own `--help` describes its process-selection behavior.

## Verification and remaining work

```sh
research/venv/bin/python -m unittest discover -s tools/re/tests -v
research/venv/bin/python tools/re/compare_images.py --help
research/venv/bin/python tools/re/decode_plist.py --help
```

The original eight seeded experiments passed and their sealed artifact hashes verified; the [evidence index](../../research/evidence/agentic-toolkit-2026-10-08.json) records the runs. The original milestone passed 19 tests; the expanded suite now passes 52 tests. Tests cover strict queue validation, dependency cycles, timeout/process-tree cleanup, sampled artifact limits, exclusive ownership, interrupted-run recovery, source/environment changes, malformed results, tampered evidence, MCP requests, Ghidra health responses, image differences, local XPC payload checks and bounded static interpretation. Native experiments separately exercise real debugger/instrumentation/compiler tools.

The next scientific milestone is an owned **actual Xcode canvas session**: record launch and loaded-image identities, correlate one real request/reply, preserve attachment descriptors, validate its output, and repeat with one controlled change. Synthetic Frida plists and ImageRenderer images establish working tools; they do not establish Apple's wire protocol. Decoder replay, surface ownership, portable SwiftUI/WASM and a renderer remain separate subsequent work.

See the [full loop design](agentic-loop.md) and [controller prompt](agentic-loop-prompt.md). Git synchronization stays an explicit reviewed checkpoint on `development`, with verified milestones fast-forwarded to `master`; raw captures and proprietary binaries are never automatically published.

## Connected campaign and bounded retrieval

```sh
research/venv/bin/python tools/re/agent.py campaign
research/venv/bin/python tools/re/agent.py index
research/venv/bin/python tools/re/agent.py search UVPropertyList
research/venv/bin/python tools/re/agent.py plan
```

The four initial reviewed campaign experiments connect Frida to live Ghidra, exercise a seeded typed plist boundary corpus with exact byte comparisons, read static Swift metadata, and attempt real Xcode canvas variants. `plan` suggests counterexperiments from verified outcomes; it does not execute them, renew budgets, or retry unchanged failures automatically. Native preview tracing requires a newly observed process and a verified fixture build-root mapping before attachment; timing alone does not establish ownership. Late attachment and incomplete wire coverage remain explicit.

`re_index` indexes verified local runs. `re_search` returns small snippets; `re_artifact` retrieves exact pages. Large MCP results retain a content-addressed full original for `re_response`, while previews stay bounded to about 6,000 characters. Raw blobs and full decompilations stay outside prompts unless explicitly retrieved. `re_claim` evaluates declared observation checks, preserving scope, contradiction and inconclusiveness. Read the [verification contract, edge-case matrix and porting strategy](verification.md) before interpreting any passing result as compatibility.

Connected validation: four supported experiments (including a reviewed 32-case follow-up), one failed canvas tool attempt, and 40 passing automated tests. Native fixture build succeeds; Xcode MCP `tools/list` times out before capture. See the [current evidence index](../../research/evidence/connected-verification-2026-10-08.json). No complete live IPC oracle is available yet.

The next recursive checkpoint adds four supported XPC/static experiments and expands the suite to 52 tests. The controller exposes 16 adapters; the MCP interface remains 19 tools. Read the [coding boundary findings](2026-10-08-xpc-boundary.md), [final run anchors](../../research/evidence/xpc-boundary-2026-10-08.json) and [minimal malformed golden](../../tools/re/fixtures/XPCOracle/manifest.json). Three bounded bridge diagnostics still stall on schema discovery. Complete live IPC and attachment recovery remain open.
