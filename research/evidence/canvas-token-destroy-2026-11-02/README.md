# Token destruction and constructor failure policy

Pinned arm64 PreviewsFoundationHost static qualification. Original reader, hashes and sanitized findings only. Raw Apple code remains temporary and local.

The reader verifies 148 instruction bytes, three selected calls, native field/case metadata and sixteen constructor constant bytes. Token destruction delegates generic callback destruction, then releases the following aligned onceGuarantee reference. The complete body has no explicit cancel call. Callback destructor effects and released guarantee effects remain opaque; no automatic-cancellation presence or absence is established.

The concrete constructor stores failureMode at state-owner offset +0x60. Its representation contains payload ordinal 1 and marker 2. The full native enum-tag accessor returns payload + 2 for an empty-case marker, yielding logical case 3: `softAssert`. Reading marker 2 alone would incorrectly identify `softAssertDebugOnly`.

Failure-mode cleanup releases closure context for marker 0, bridge storage for marker 1 and returns for other markers. The constructor-selected empty case has no payload reference release in this helper. Previously recovered state-owner deinit can invoke configured policy while waiting, but actual last ownership, deinit, assertion delivery, cancellation and final resource settlement remain unobserved. Policy implementation behavior is not qualified by its name.

The initial exploratory tag range was incomplete; final verification includes its select and return. No published policy claim relies on marker alone. REA aligned/no open session; prior UI/Ghidra failures not retried unchanged. Run `python3 verify.py` with pinned Xcode and exclusive controller lock. Disassembly bounds twenty seconds per range; fresh copied-reader replay fifty-five seconds. No native private call, GUI/system change, product change or Rust-test rerun. Full acceptance remains open.
