# Owned native unfulfilled-policy controls

Run from the repository root:

```sh
python3 tools/re/native-canvas-failure-runtime/run.py --output /private/tmp/canvas-policy-fresh
```

This intentionally triggers **one SIGTRAP in an owned child**, alongside five returning controls. Xcode and simulators are not attached or terminated. Output must be new. Existing compiler/ARM64 native prerequisites and the pinned PreviewsFoundationHost profile are required. Each compiler stage is bounded to 30 seconds, each owned native child to eight seconds; the runtime controller lock is exclusive.

Only already recovered marker-2 representations are admitted: softAssertDebugOnly payload 0, softAssert payload 1, fatalError payload 2. Each gets an observer/context/owned FD, with unfulfilled owner release or fulfilled-before-release as a positive control. The default handle used for setup is explicitly invalidated before release. No arbitrary test callback or log-associated value is constructed by this runner.

The assertion reader checks actual process status, native diagnostic, callback/deinit ordering, weak context/FD outcomes and matched PIDs. A future soft-assert process failure is a different observed outcome, not permission to claim it returned. Raw fatal stderr may contain stack/register dumps: retain it locally; publish only selected diagnostics and sanitized evidence. See [qualified results and excluded log attempt](../../../research/evidence/canvas-runtime-failure-policy-2026-11-02/README.md).
