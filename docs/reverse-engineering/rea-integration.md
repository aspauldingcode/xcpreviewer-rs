# REA integration

REA 6.2.0 is pinned as a local, optional discovery engine. It uses the existing free Ghidra 12.1.2 and JDK 21 installation; it does not require a paid analysis provider or a separate AI subscription. The research controller continues to run serially under its exclusive lock.

## Installation and registration

Run `sh tools/re/bootstrap-rea.sh`. The committed npm lock pins the dependency tree; installation disables lifecycle scripts and writes only to ignored `research/build/rea` and the repository's npm cache. REA requires a compatible Node runtime (this installation was tested with Node 24.19.0).

The user-authorized local setup registered REA in `/Users/8amps/.codex/config.toml`, preserving unrelated settings and saving `/Users/8amps/.codex/config.toml.rea.backup`. It installed REA's matching skill in `/Users/8amps/.agents/skills/reverse-engineer-anything`. These local files and the backup are not committed. A new MCP connection may be needed for the desktop session to discover the registration. The controller's private stdio connection works independently of desktop reconnection.

`tools/re/rea/codex-tools.json` records the selected 35 native/Apple/evidence tools from the measured 139-tool inventory. Codex uses a 30-second server startup deadline and a 360-second tool deadline. REA is explicitly bound to Ghidra, whose initial import has a 330-second deadline. This limits irrelevant tool schemas while keeping full local REA available through its CLI. No approval preferences are changed.

## Reviewed pilot

The `rea_native` adapter runs `native-rea-observer-pilot` from the ordinary campaign queue. It only accepts the previously pinned FoundationHost image (SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`). It opens one provider session for two wrappers (`0x42604`, `0x428d0`), obtains native function dossiers and inspects their selected direct calls. The independent Mach-O mapper compares every one of the eight selected instruction bytes, decodes their ARM64 BL immediates and checks destinations `0xedf78` and `0xee75c` against REA's references and flow. Entry identity, architecture, provider and analysis-profile consistency are mandatory. The pilot does not prove every function byte or pseudocode semantics.

Raw function output, schemas, timing, errors and cleanup results stay in ignored sealed runs. The frozen controller sources include the npm manifests and tool-selection file. Environment identity records the installed lock and a digest of REA's runtime code. The adapter explicitly closes its owned provider before closing its MCP client; any tool, identity, byte, flow or cleanup error fails acceptance.

The separate `owned-rea-engine-control` compiles a small reviewed ARM64 C fixture, locates its entry/leaf symbols and independently decodes the selected call before querying REA. This provides a discriminating engine control if large-image startup is blocked; it does not substitute for native Xcode evidence.

## Observed startup limitation

The native FoundationHost control failed at both the shortened 180-second startup bound and the documented 330-second bound. The sealed 330-second run returned `provider_timeout`; `close_binary` completed without an error. Do not repeat the same full-image import. A changed analysis profile/import method is required before retrying this native control. Registration and tool discovery do not establish successful decompilation of Xcode.

## Continuous loop use

Use one opened binary for a batch of related queries. Keep full local results; provide only the relevant addresses, hypotheses, byte checks, counterexamples and unresolved limitations to the agent. Do not re-import a large image for each question. REA's identity/profile-bound snapshots can reduce repeated imports when supported by the observed operations; a cached snapshot is static evidence and cannot establish a fresh live capture. The current adapter deliberately uses fresh imports for its integration control.

Use REA for discovery and navigation, LLVM plus mapped bytes for independent static verification, and owned runtime probes for lifecycle/transport claims. A tool-generated reconstruction report is evidence to examine, not permission to close an issue. Native attaches, Xcode approvals and Canvas wire capture retain their existing gates. REA cannot remove macOS consent requirements or establish missing private Swift runtime ABI contracts.

Do not repeat an unchanged startup failure. Retain diagnostics and switch to a smaller owned binary or another unblocked native oracle. Extend this adapter only with a reviewed target/query and explicit acceptance checks; never dispatch arbitrary REA runtime actions through the controller.

Upstream references: [REA](https://github.com/morluto/rea), [MCP contracts](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md), [installation](https://github.com/morluto/rea/blob/main/docs/installation.md). The installed package and observed schemas are authoritative for this pinned integration; upstream main can change independently.

## Accepted engine control

The corrected owned ARM64 control passes native decompilation and all four selected BL instruction bytes against an independently mapped image and decoded target. It explicitly closes Ghidra and its MCP client. All 159 tests pass, including every selected-byte corruption, identity/profile/reference/flow mismatch, wrong-endian architecture rejection and campaign acceptance. The earlier schema-alias failure and success-but-inconclusive check-path run remain sealed. See [sanitized evidence and all anchors](../../research/evidence/rea-integration-2026-10-09.json).
