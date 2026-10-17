# Public ImageRenderer color-mode oracle: endpoints pass, gray predictions fail

Two separately reviewed owned experiments ran in one wake under the unchanged18:11:07UTC native deadline. They use public ImageRenderer APIs without an Xcode workspace, visible window, UI input or display capture. Each had one compile, output control and fixture; neither was repeated. Both completed with outer/target exit0, scoped drain/remaining0 and no abort/emergency. REA6.2.0 bound and closed each owned arm64 artifact. No executable or Apple binary is published.

## Endpoint experiment: accepted within its narrow contract

Fresh renderers use nonLinear/linear/extendedLinear modes and opaque red/blue/red inputs. Both CGImage drawing and render callbacks target an explicit float32 little-endian linear-sRGB premultiplied RGBA context:17×9,288-byte stride,4,096-byte initialized allocation. All18 full allocations match independent IEEE endpoint expectations, including2,592padding and27,072tail bytes:73,728bytes accepted normally and under Python optimization. Final red restores initial complete bytes per mode/route; this is fresh-renderer input restoration, not interactive state reset.

Measured CGImage metadata, constant across these endpoint phases/routes:

| Mode | bpc / bpp | Stride | Color-space name | Bitmap info |
| --- | --- | --- | --- | --- |
| nonLinear |8 /32 |68 |kCGColorSpaceSRGB |1 |
| linear |8 /32 |68 |kCGColorSpaceLinearSRGB |1 |
| extendedLinear |16 /64 |136 |kCGColorSpaceExtendedLinearSRGB |4353 |

These are API metadata observations. Raw CGImage provider bytes were not captured or qualified. The common target's exact endpoint bytes do not establish arbitrary color or transfer-curve equivalence.

## Dependent gray experiment: retained falsification, not accepted goldens

The mode metadata motivates a separate quarter/half/quarter gray control using Color(.sRGBLinear) in linear and extendedLinear modes. Before execution, its consumer allowed only complete allocations matching exact binary0.25/0.5, plus normalized8-bit64/255 or128/255 alternatives for linear mode. ExtendedLinear required exact quarter/half. Restoration remained mandatory. Synthetic tests covered both exact and quantized callback countermodels before execution.

Actual process completion succeeded, but strict normal/-O content admission rejects. All49,152bytes were compared against the unchanged finite candidates:3 extendedLinear CGImage-draw allocations match;9 allocations reject. Every padding byte(1,728), unused-tail byte(18,048), alpha1 word and complete restored quarter allocation independently passes. First-pixel RGB observations below are rounded for readability; the sealed buffers and diagnostics retain exact bytes/values.

| Mode / route | Quarter input | Half input |
| --- | --- | --- |
| linear / CGImage draw |0.5372549295 |0.7372549176 |
| linear / callback |0.2500107586 |0.4999917150 |
| extendedLinear / CGImage draw |0.25 |0.5 |
| extendedLinear / callback |0.2500107586 |0.4999917150 |

These observations falsify the predeclared gray byte expectations. They are not replacement expected values, accepted compatibility goldens or proof of a conversion cause. No expectation was relaxed and no native retry occurred. The initial synthetic mode-fault injection became a no-op after reducing three modes to two; it was corrected before execution. Independent review also caught an invalid Swift initializer label before compile; the invalid source and correction record are retained. Neither failure triggered native execution of that invalid source.

Independent source/plan and final reviews approved endpoint acceptance and retention of the gray falsification. Nine synthetic test methods pass in each interpreter mode across the two probes, including36 endpoint and37 gray negative faults plus a gray countermodel and post-lock deadline tests. Successful native completion never overrides failed pixel admission. The sampled observers tracked1 identity per fixture; their scope excludes unseen escapes and provides no general reliability claim.

Both milestones remain open. CGImage provider bytes, display/ICC fidelity, fractional alpha, arbitrary extended range, Canvas lifecycle/transport, state refresh and product compatibility remain unqualified. Private capture bridge remains offline; generic Xcode input quarantine and clean-room product isolation remain active. Next discriminate source-color resolution versus destination conversion using an independent owned public Quartz/NSColor reference; do not adopt these observed gray values as a fitted implementation rule.

`seal.json` pins both subexperiments, their receipts, failed fixtures and diagnostic tools. `verify-frozen.py` checks integrity, accepts endpoint bytes, confirms gray rejection and recomputes all gray candidate comparisons offline. No native execution occurs during frozen verification.
