# Existing provider probes during native refresh and file changes

Static discovery remains paused. This changes the previous experiment's probe profile: three already-qualified PreviewsScenes collector/provider/registry entries are added to the existing preview-update and selected assignment-helper probes. No new function body, disassembly slice, destructor probe or broad discovery is introduced. The old seven-target destruction combination is not used.

## Actual execution

One native session on Xcode PID 45749 executes the guarded paused-Canvas Refresh AXButton, then real owned-source color modification and exact restoration. The actual button press succeeds and the original pin.fill/three header controls return. All **five selected probes remain silent** during the idle/manual intervals, including at least eight seconds after the button acknowledgement. This extends the earlier two-probe negative observation; it is not evidence that native refresh does no work or that its implementation has been identified.

Real source edit and restoration each produce:

| Selected entry | Matched intervals per source phase |
| --- | ---: |
| Collector, PreviewsScenes +0x29d34 | 6 |
| Providers, +0x3e4e0 | 12 |
| Registries, +0x3eb94 | 12 |
| Preview update, +0x3f694 | 18 |
| Assignment helper, PreviewsUI +0x19dd4, caller +0x3f978 | 18 |

Every observed collector interval contains this same **selected synchronous call tree**, with IDs matched and returns on the recorded thread:

```
collector
  providers -> return
  providers -> return
  registries
    preview-update -> assignment-helper -> return -> return
    preview-update -> assignment-helper -> return -> return
    preview-update -> assignment-helper -> return -> return
  registries -> return (no selected children)
return
```

These are observed calls, not six refresh cycles, receiver allocations, independent native tests, all executed instructions or a general callback/async contract. No receiver ownership or collector payload interpretation is measured. Same-thread nesting is checked; the thread is not independently requalified as main in this profile. Host receipt timestamps order retained messages, not an exact cross-thread native instruction timeline. Source writes precede phase markers; extremely early callbacks could precede a phase marker generally, although none do here.

## Qualification, cleanup and scope

Existing executable/source/image hash guards and loaded UUID checks pass. PreviewsScenes UUID is `afaf513ac1153755840e1d82b40e7d93`; PreviewsUI UUID is `0d87b0e2f4453035a9b6b1cf8230e015`. The exclusive controller lock covers the native session. The collector completes at 38.81 seconds of its 150-second deadline, exits zero, restores source bytes, unloads and detaches. Independent postflight verifies original source/project hashes, Xcode alive and controller availability. Owned project close/reopen setup uses an independent bounded lease before attachment and the previously qualified exact Open-dialog directory/project guards. Original header/pin UI is restored; no user edits are discarded or Xcode/simulator process terminated.

Provider entry reporting is capped at 1000 calls. Cap/overflow is not exercised here; retained count is 60 provider/registry/collector entries across both phases. The verifier rejects overflow. Collector status alone does not accept the observation; the semantic reader verifies the event/phase/UI boundaries and call trees. Eight synthetic corruptions reject; these are evidence-reader checks, not additional native runtime controls.

This is scoped native runtime verification of the selected source-change call tree and bounded manual-route absence, with actual UI action receipts. No simulated replay is counted as native. Static provenance is inherited from the existing qualified boundaries. No uninstrumented manual repeat, screenshot/pixel comparison, new IDE build notification, interactive-state continuity, native target destruction, observer cleanup or renderer/provider/transport resource release is established. Native resources used by our hooks being detached is not Canvas resource settlement. Header return is UI functionality only; there is no new WASM product implementation or full refresh parity.

Both the earlier two-probe manual checkpoint and this changed-profile result remain scoped negative controls. **Do not repeat unchanged five-probe manual-refresh runs.** The internal manual route is still unknown. Next useful work should exercise a different existing recovered native lifecycle/interaction/build contract or correlate a previously recovered refresh-request boundary, without broad static expansion or assuming cached headers mean rendering completion.

## Reproduction and artifacts

Use the existing native refresh experiment procedure with an owned paused PreviewLab fixture and add `--provider-probes` to `tools/re/native-canvas-refresh-runtime/session.py`. Use phase.py acknowledgements for idle-start/idle-end, refresh-start/native AXButton/refresh-return/refresh-settled, edit/edit-settled and restore/restore-settled. Observe final owned UI before stop. Keep idle >=3 seconds and post-button observation >=8 seconds; fail dependent work on any guard/acknowledgement failure. Use no ambiguous nested-menu retry. The collector's finally path restores only unchanged owned edits and refuses concurrent edits. Native UI remains operator/approved-controller driven; no autonomous UI driver was added.

Read retained evidence without invoking Xcode:

```
python3 tools/re/native-canvas-refresh-runtime/verify_providers.py research/evidence/canvas-runtime-provider-refresh-2026-11-03
python3 tools/re/native-canvas-refresh-runtime/check_provider_reader.py
```

`events.jsonl` is the original address-free native stream. ui.json and setup.json retain only selected owned controls/action acknowledgements; full AX trees/source/sidebar remain local with hashes. Executed original agent/session sources, assertions, reader controls and postflight are retained. Native full areas remain 0/9; tracked issues 1/26 (3.8%).
