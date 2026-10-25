# Correct remote-title Unicode prefix boundary

Follow-up to the sealed remote leaf codec commit. The serial exclusive controller lock remained held across the extra control and correction. The predecessor and all unchanged implementation pins are verified; unrelated staged work remains untouched. No Xcode MCP/private bridge, guessed private Swift ABI, private remote decoder invocation, user Xcode/simulator operation, protection/signing change, purchase or Apple binary publication occurred.

## Falsified assumption

The initial codec used Rust str.starts_with for the literal [Remote] plus trailing space. A targeted public Swift String.hasPrefix control returned false when combining acute U+0301, variation selector U+FE0F or ZWJ U+200D immediately followed that space, while byte-prefix matching returned true. Swift rejects a partial character boundary. The initial codec could therefore omit a required second prefix. The source independently binds the native call to the exact Swift String.hasPrefix export in predecessor evidence; this is not a guessed private behavior.

The earlier sealed source/wire findings remain historical. Its generalized prefix/idempotence claim is narrowed here: normalization is idempotent for the ordinary tested titles, but a leading combining scalar can cause another prefix on a later native-style decode. Prior byte-prefix source is identifiable by commit in failures.json/predecessor.json. No initial observation is rewritten as a passing result.

## Exhaustive public runtime observation

Original generate.swift evaluates (prefix + scalar + x).hasPrefix(prefix) for every valid Unicode scalar from0 through0x10ffff, excluding surrogates:1,112,064 actual public Swift API observations. It coalesces all rejected scalar values into334 sorted disjoint ranges, covering2,619 scalars. Complete ranges and seven explicit normalized controls are captured in observations.json. The controls include combining mark, variation selector, ZWJ, spacing mark, ordinary ASCII, emoji and a newline boundary. Replays compare the complete native result, then compare every generated Rust range and the independently encoded golden binary plist. This measures the immediate suffix-scalar boundary in this fixed trailing-space prefix context; it is not a general Unicode grapheme segmenter, a proof for arbitrary string algorithms or all future runtime versions. Compiler/host OS versions are recorded in results.json.

These ranges are sanitized public API observations of character values, not Apple code, private metadata or a binary dump. The generator uses only public Swift/Foundation APIs and its owned process. Native compile/run deadlines are30s; observed full enumeration is subsecond on this host. No user process or persistent service is touched.

## Portable correction

Original remote_prefix.rs first matches the fixed bytes, then checks the first following scalar against the measured rejection ranges using a bounded binary search. Empty suffix accepts. A rejected suffix scalar makes the leaf decoder prepend another [Remote] space, matching the captured Swift result. Ordinary emoji and control boundaries stay accepted. This preserves the supported canonical Value profile while correcting native character-boundary behavior for the measured runtime; native Any/NSNumber coercions and underlying wrappers remain unsupported.

A golden original binary plist encodes the complete observed ranges using independent Python plistlib. New Rust regression covers both endpoints and adjacent valid scalars for every range, plus a normal emoji boundary. All223 Rust tests pass offline. A compiled wasm32-wasip1 control actually executes the corrected codec for combining/variation/ZWJ/spacing-mark and normal boundaries. Node WASI preview1 uses no filesystem preopens or inherited environment. Replay compiles/runs the public exhaustive native oracle, compares the entire observed table and fixture, reruns all tests and actual WASI controls, then removes its disposable artifacts. Rust build/test bounds60s, WASI10s and outer replay180s apply.

The prior leaf codec remains otherwise unchanged: title/optional fields, signed opaque option bits, severity and asymmetric omitted flags are still source-guided. Public Foundation wire parsing from the prior checkpoint is distinct from private decoder execution. Native Canvas, wrapper/diagnostic/coercion contracts and resource/target settlement remain open. Both milestone flags remain false. Next underlying wrapper or another missing protocol/resource boundary, preserving Unicode/runtime version scope.
