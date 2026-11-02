# Execution update and erased-point ownership

Pinned arm64 PreviewsPipeline and PreviewsFoundationHost source qualification. This package contains original readers, hashes and sanitized findings; Apple instruction text stays temporary and local.

The reader compares 1,064 instruction bytes with bounded disassembler output, binds thirteen selected direct calls, checks reflection field order and imported field types, and reproduces complete findings in a fresh copied-reader workspace.

ExecutionPointUpdate destroys generic output through its type witness. The qualified tail destroys UpdateSeed, advances by its size/alignment, loads the reflected ConcurrentInvalidationHandle field and releases it. The other complex update fields are byte-verified but not fully mapped here.

AnyExecutionPoint destroys its box reference, the SendableAnyHashable identity payload and two identity String backing values. If concrete generic box deallocation runs, it destroys its stored generic value through that value's witness before class deallocation. A reference release alone does not prove that deallocation runs.

ConcurrentInvalidationHandle deinit releases name backing storage and a state reference. Its deallocating variant additionally frees class storage. The complete bounded bodies contain no explicit invalidate or observer call. Effects of the released state object and generic payload destructors remain opaque: this does not prove cancellation is absent or present.

No private native method was called. Actual reference counts, cancellation, session invalidation, callback delivery and transport/OS resource settlement were not observed. ExecutionPointStatus cleanup remains unqualified. Prior locked-screen/Accessibility and Ghidra limitations were not retried unchanged. Full recovery acceptance remains open.

Run `python3 verify.py` on the pinned installed Xcode with access to the repository's exclusive controller lock. Disassembly has a twenty-second bound per range; fresh replay has a fifty-five-second bound. Raw output remains under temporary directories and is excluded from this package.
