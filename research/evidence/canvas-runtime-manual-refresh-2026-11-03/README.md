# Native manual refresh contrasted with real source edits

Static discovery remains paused. This uses only two previously qualified entry probes: PreviewsScenes preview-update at 0x3f694 and the PreviewsUI assignment helper at 0x19dd4, filtered to caller 0x3f978 in PreviewsScenes. No additional function discovery or decompilation was required.

## Actual observations

| Phase | Run A | Run B |
| --- | --- | --- |
| At least three seconds idle | Zero selected callbacks | Zero selected callbacks |
| Manual action | Nested menu-path executor rejects Refresh Canvas under the Canvas toggle; **no successful manual action** | Actual AXPress of enabled Refresh Canvas button on paused owned Canvas succeeds |
| Before subsequent source edit | Zero selected callbacks | Zero selected callbacks, including at least eight seconds after the acknowledged press |
| Actual blue-to-black source modification | 18 preview-update entry/return pairs, each containing a selected assignment-helper pair | Same 18 paired updates/helpers |
| Actual source restoration | 18 paired updates/helpers | Same 18 paired updates/helpers |
| Final owned UI | Original pin.fill and three header controls | Original pin.fill and three header controls |

The collector receives each selected helper entry/return inside a preview-update interval, on the matching thread and with the qualified caller offset. IDs are matched and every interval returns. Events are timestamped at host receipt, not exact instruction execution time or a total ordering across all native threads.

The failed menu route in A is an automation interface failure, not an Xcode refresh failure. It was not retried unchanged. The project was safely closed/reopened through the already-qualified owned Open dialog to obtain a paused Canvas with an actual AXButton. The independent bounded setup lease was released before B attached. B's button press is actual native UI execution; its original three header controls reappear. **Neither manual interval exercises these two selected private-method probes.** Real-file controls then demonstrate both probes can fire in the same attached sessions. This does not prove manual refresh performs no work, establish its internal route, or exclude delayed/coalesced activity outside the bounded interval. File-phase callbacks are temporally correlated with the edits, not a complete provenance proof for every call. No uninstrumented manual-action repeat was performed here; hook effects are not excluded.

The color source writes and their restoration actually occurred and are hash-guarded against concurrent edits. No pixel screenshot/comparison is taken here: header return is not verified color rendering, interactive state preservation, asynchronous completion, new build notification, object destruction or resource release. The visible historical Build Succeeded label is not counted as a new build result. Existing prior native rendered-color evidence is separate and not rerun by these reader commands.

## Target, cleanup and evidence levels

Both collectors verify Xcode PID 45749's executable, exact owned source hash, shipped image hashes and loaded PreviewsScenes/PreviewsUI UUIDs. They hold an exclusive controller lock, use cancellable attach/load/unload/detach operations and a 150-second native-session deadline. A completes at 51.85 seconds; B at 38.14 seconds. Both native collectors exit zero after all protocol phases, restore source bytes, unload and detach; this is an observational collector status and does not turn A's failed menu action into a success. Independent postflight verifies original source/project hashes, Xcode alive and controller availability. No Xcode/simulator process termination, system-protection/signing change or helper-library injection.

- Static reconstruction: existing entry/callsite qualification only; no new body recovered.
- Simulated replay: none counted as native evidence. Eight synthetic artifact corruptions test the reader only.
- Native runtime verification: actual source writes, selected paired/nested calls, bounded absence intervals and actual button/menu action receipts as scoped above.
- Working functionality: original header/pin UI restored. No new WASM feature or complete refresh/render/resource contract acceptance.

Original address-free streams and selected owned UI receipts are retained in a/ and b/. Full AX menus/source/sidebar remain local, identified by hashes. A's post-failure phase acknowledgements were not appended to its raw UI protocol; the canonical full phase sequence is the collector stream. File writes happen before their phase receipt, so an extremely early callback could precede the phase marker; this limitation is not excluded generally, although no such callback occurs in these retained runs. The source-write/phase markers and UI acknowledgements are host boundaries, not proof of synchronous native completion.

## Reproduction

Guard the owned PreviewLab fixture, current executable/PID, source/project bytes and available controller before proceeding. Run `tools/re/native-canvas-refresh-runtime/session.py --output NEW_DIRECTORY --pid CURRENT_PID --source OWNED_SOURCE`. Wait for ready. Use `phase.py NEW_DIRECTORY LABEL`, which requires a fresh acknowledged phase and a live collector:

1. idle-start, wait at least three seconds, idle-end.
2. refresh-start; native AXPress on the observed enabled Refresh Canvas button of the paused owned fixture; refresh-return; wait at least eight seconds; refresh-settled. Record actual UI output or failure. Do not retry the failed ambiguous nested-menu route.
3. edit; wait for the observation window; edit-settled. The collector changes the guarded blue literal to black.
4. restore; wait; restore-settled. The collector restores exact original bytes.
5. Observe owned UI, touch NEW_DIRECTORY/stop, require unload/detach and independently verify source/project hashes, target and controller.

If not paused, use the previously qualified guarded Close Project/Open setup only on the owned fixture; cancel any save/discard modal, never discard user work. UI remains operator/approved-native-controller driven; these tools do not supply an autonomous UI driver. On failure/deadline, preserve outputs and restore only owned changes. The collector's finally restoration refuses concurrent edits. Negative guards other than the actual A menu failure were not newly exercised natively here.

Read retained observations without touching Xcode:

```
python3 tools/re/native-canvas-refresh-runtime/verify.py research/evidence/canvas-runtime-manual-refresh-2026-11-03/a
python3 tools/re/native-canvas-refresh-runtime/verify.py research/evidence/canvas-runtime-manual-refresh-2026-11-03/b --button
python3 tools/re/native-canvas-refresh-runtime/check_reader.py
```

Native complete areas remain 0/9; tracked issues 1/26 (3.8%). Next test should instrument an already recovered refresh/provider route appropriate to the manual action, retaining these selected-method zero results. Do not infer manual refresh parity from the positive file-edit control or expand broad static discovery.
