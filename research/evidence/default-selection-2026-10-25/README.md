# Recursive default-selection calculation

Recovered PreviewOverridesConfiguration.defaultSelection starts with the node's
single default ID or multi-default set. It then iterates a fixed snapshot of
those initial IDs, looks up matching child configurations and unions each
child's recursively calculated defaults. IDs contributed by a child do not
activate sibling children at the parent. Empty initial multi-defaults traverse
no children; unresolved/empty IDs remain selected. The variants array is not
consulted for membership validation. Style list/range does not change the single
ID calculation. Child lookup uses the qualified canonical ID equality profile.

776 selected bytes independently match LLVM: complete getter and specialized
formUnion helper against the current pinned MessagingHost SHA/UUID. Selection
layout/tag branches, singleton insertion, multi-set union, initial reference
retention, fixed snapshot iteration, dictionary lookup/missing branch, recursive
getter call and accumulator union checked. The recursive union writes the stack
accumulator while the loop continues using the retained initial set. This is
membership recovery, not a fixed-point walk through newly selected siblings.
No native private getter or selection method is invoked.

The library adds default_selection() returning an owned VariantIdSet without
mutating the configuration. Parent representatives survive equivalent child
IDs. Portable child traversal uses deterministic initial ID-set order. Native
Set traversal is unordered: in eight fixed public native Set/formUnion process
controls, the selected canonical membership stayed identical while both the
composed and decomposed sibling representative spellings were observed. Parent
spelling survived in all eight. Portable order chooses one deterministic
sibling representative; native representation parity is not claimed. Finite
public controls qualify these profiles, not every possible native Set layout.

The inspector adds default-selection mode. It first validates/decodes the entire
override tree, including unselected children, then calculates defaults. A malformed
unselected child is therefore still a decode failure. Summaries show at most
eight selected IDs, totals/shown counts and existing escaped256-scalar limits.
Canonical output is the complete calculated String array in portable order.
That array is a derived result format, not an Apple transport payload. Existing
configuration inspection/canonical wire-value modes remain unchanged.

All 305 Rust tests pass, including three new complete-control, immutable-input/
owned-result and actual CLI/summary tests. 24 original public Foundation
configuration/default-set compositions yield 20 accepts and four rejects. The
composition uses actual public Swift Set/dictionary lookup/formUnion, adopting
the documented portable child traversal order for full expected output. It does
not call the private getter. Controls distinguish selected versus unselected
children, no sibling cascade versus proper nested descent, canonical child-key
lookup, parent/sibling representative policy, unresolved/empty/range defaults,
multi-empty, long/many IDs and decode failures. Actual WASI executes 24 canonical
cases plus 20 summaries (44 invocations), explicit standard I/O, no filesystem
preopens/inherited environment. Complete calculated arrays agree type-sensitively
under the explicit ordering policy; 20 WASI outputs pass public Foundation
reparse and accepted summaries match native Rust bytes. Disposable replay checks
source, three focused tests, all Foundation/WASI controls and eight unordered
native Set probes. Unordered observations are validated by membership and allowed
representatives rather than demanding identical random order. Full 305-test output
is retained separately. No new verification failures occurred.

Ambiguous raw child-key bridging, decode depth bounds, portable sibling error
order and Unicode-version qualification remain inherited explicit restrictions.
Unchanged prior native probes were not rerun. REA package/path/catalog align;
no target open/provider binding. Private module and unsettled Ghidra inventory
limitations remain recorded without unchanged retries or private ABI guesses.
Raw Apple disassembly remains local ignored files; published probes/data/code
are original and sanitized.

This calculation does not apply overrides, resolve rendered effects, execute
native selection, render/refresh Canvas, correlate transport replies, register
peer dispatch or establish resource settlement. Native private getter parity,
upstream/downstream selection behavior and all lifecycle/resource contracts
remain open. Both milestone contracts remain incomplete.
