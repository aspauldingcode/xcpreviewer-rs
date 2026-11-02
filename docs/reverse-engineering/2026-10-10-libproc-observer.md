# Public libproc owned-process observation

The previous full-extent comparison failed three times on bounded process inventory. A changed observer now passes two owned-control campaigns. Default `ps` remains available and unreliable on this host; selecting the new backend is explicit. This repairs an execution prerequisite, not the native Canvas release or transport contract.

## Predictions and independence

The helper uses public `proc_listallpids`, `proc_pidinfo(PROC_PIDTBSDINFO)` and `proc_pidpath`. It inventories only ancestry/lifetime metadata and reads executable paths for selected roots, matching known lifetimes and their descendants. It never reads process arguments or sends signals. Each invocation runs in a separate owned subprocess with the original two-second deadline.

Apple's [public process-information definition](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/proc_info.h) declares the parent/group, status and microsecond start-time fields. The helper compiles against the installed SDK public headers. It checks birth identity before and after fetching executable paths. Missing path identity for a still-live candidate fails the helper. Missing live roots fail the Python adapter. Malformed, duplicate and invalid identities also fail; Unicode filesystem bytes retain their identity.

Independent expectations use owned spawn PIDs, `os.getppid`, `os.getpgid` and dyld's `_NSGetExecutablePath`. The first experiment falsified a harness assumption: Xcode's Python `sys.executable` launcher resolves to a different file from its running app executable. That failed seal remains retained. The corrected comparison uses dyld rather than accepting the libproc result as its own expected path.

Twenty unchanged own-process samples pass in each supporting campaign. The final explicit controller-injection campaign has a maximum sample duration of 0.016826 seconds. A detached `setsid` child cannot publish its delayed marker after the owned timeout wrapper returns. Normal exit zero and exit seven retain their distinct outcomes. Mutated birth and executable identities receive no destructive signals. These mutations test guards; they do not demonstrate actual kernel PID reuse.

The first controller-injection attempt retained another failure: its negative test mocked `kill(pid, 0)` as though a nonexistent test root were live. The corrected control forwards read-only liveness checks and rejects destructive signals. Neither failure was discarded or counted as support.

## Explicit execution and limits

`execute(..., observer=observer.snapshot)`, `OwnedTree(..., snapshotter=observer.snapshot)` and `Controller(process_observer=observer.snapshot)` fix observer selection for the whole owned-tree lifetime. They preserve default behavior for existing callers. Cleanup still requires full lifetime/executable equality, and deliberately excludes escaped/replaced identities it cannot establish. It does not prove arbitrary descendants escaping between observations or physical resource reclamation.

`tools/re/libproc-loop.py` builds the owned helper, records compiler/source/binary identities, and runs a reviewed bounded graph round with the exclusive controller lock. `--config research/loop/extent-runner.json` selects the dependent extent comparison. The optional `--only` mode uses the existing bounded campaign controller when graph integration is unavailable. This does not alter macOS protections, Apple signatures, TCC or Xcode approval state.

The accompanying machine-readable receipt retains pinned seals, failure reasons and verification outcomes. Delivery acceptance remains review-pending; R1, R2 and both milestone contracts remain open.

## Dependent full extent comparison

With the independently controlled libproc prerequisite, the formerly blocked frozen CLI corpus completed in 166.388 seconds under its original 180-second deadline. All 80 raw public native callback allocations match bit for bit: 1,310,720 bytes, including 1,536 padding bytes and 1,035,264 unused-tail bytes across 40 cases with two fresh executions each. Dimensions are 1×1, 13×7 and 64×64 with compact/padded strides. Four further transparent frames match independent predictions.

All 84 raw allocations match independent Fraction predictions (1,376,256 bytes), and all 84 PNGs independently decode to the explicitly projected straight-alpha sRGB RGBA values (274,656 decoded bytes). Pixel, padding, tail and PNG corruption controls fail their respective verifiers. Eight actual source/configuration/runtime/cache/precommit failures preserve the last-good published pointer and payloads; owned stages are cleaned.

This supports the pinned frozen CLI on the measured macOS LLVM/V8 route against the separately sealed public native callback target. It does not verify the concurrently edited mutable CLI, native Canvas screenshots, native PNG/getter behavior, a browser, state migration, arbitrary SwiftUI or every cross-platform host. No issue or milestone is closed.

Final isolated proposed implementation: 330 tests pass in 35.978 seconds. Default-call regression and dependency-only validation failures are retained in the receipt; no unrelated working changes were included in this suite.
