# Execution status cleanup

Pinned arm64 PreviewsPipeline static qualification. Original reader and sanitized findings only; Apple instruction text remains temporary and local.

The reader verifies 1,440 instruction bytes, seven selected imported calls, native field/type reflection and three logical payload dispatch routes. A fresh copied-reader replay must reproduce the complete findings. Local symbolic references are resolved only after walking the relevant native chained-fixup page.

- `running` contains optional associated `ExecutionPoint.Output` named `staleOutput`. Absent output returns; present output delegates destruction through its type witness.
- `valid` contains `ExecutionPointUpdate<ExecutionPoint.Output>` named `update`. Cleanup is inlined in this witness, including associated-output destruction and a final reference release. Intermediate fields are not completely mapped; the standalone update destroy function is not called on this route.
- `failed` contains optional associated output plus Error. It conditionally destroys the output, then releases the following aligned error reference.

The reader checks the logical tag dispatch after the generic enum representation decoder. Decoder bytes are compared, but arbitrary/malformed representations, concrete runtime layout sizes and actual dynamic destructor effects are not exercised. No native private method/event, cancellation, zero reference count or final resource settlement is established. Full Canvas acceptance remains open.

Exploratory `types.py` shadowed Python's standard-library module and failed import; renaming the script resolved this. No absence claim follows from that failure. Previous locked-screen/Accessibility and Ghidra failures were not retried unchanged.

Run `python3 verify.py` against the pinned installed Xcode. Each disassembly has a twenty-second deadline; the replay has a fifty-five-second deadline and uses the repository's exclusive controller lock. Product code is unchanged; no Rust suite rerun is claimed.
