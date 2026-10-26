# Property-list value box wire codec and typed access

Recovered1,284 selected MessagingHost/FoundationHost bytes. Exact metadata/imports,
whole-dictionary witness moves/copies, raw key String, required/optional member
lookup paths and String dynamic-cast specialization are pinned; complete selected
instructions match LLVM/Mach-O. PlistValueBox has one plist field. Its native
PropertyList contains serializableDictionary:[String:Any], establishing the outer
dictionary boundary. Copying a whole PropertyList does not mean arbitrary raw
non-dictionary roots are accepted by the wire adapter.

Box wire initialization/encoding move/copy the entire PropertyList. They do not
require or type its value member. Empty and unknown-only dictionaries are valid;
unknown fields and arbitrary supported nested plist values remain intact. Typed
getValue/getOptionalValue later delegate to PropertyList.unarchiveValue versus
unarchiveOptionalValue with raw key value. Required missing fails; optional missing
returns nil. A present value reaches typed conversion in both paths; a conversion
error propagates as failure rather than optional absence. String specialization
uses swift_dynamicCast to String; empty String is present. Native diagnostic text,
error context/wrapping and private getter execution are not reproduced.

Original PlistValueBox retains the dictionary, provides from_value for one encoded
value, and delegates present-value access through required_with/optional_with.
These original callback APIs preserve caller errors; they do not implement every
native PropertyListRepresentable conversion or native error wrapper. Generic
optional constructor/nil omission is not reconstructed. Missing callbacks are not
called. decode_boxes validates the entire array, preserving order/duplicates and
reporting the failing index. Original plist-box/control-state-boxes inspectors
return complete wire dictionaries; typed String inspectors return original
isPresent/value reports. Summaries are bounded and never dump opaque contents.

Raw canonically equivalent outer dictionary-key collisions are outside the
portable supported domain (explicit CanonicalKeyCollision), while native Swift
bridging may collapse them. This is a tool-domain restriction, not claimed native
rejection parity. Existing Unicode16 qualification is inherited. Nested opaque
values are retained. Native HashableBox equality/hash/identity/lifetime, full
control-state transport/correlation and resource settlement remain unverified.
This implements the inner representable codec only; configured-request-projections
still accepts original host-opaque state values rather than silently changing its
input contract to boxed wire values.

347 Rust tests pass. Three new tests cover complete public compositions, delegated
error/missing/present-false behavior, owned outputs, constructor wrapping, explicit
outer collision/late-array boundaries and complete CLI/summary behavior.29 original
public Foundation compositions (18 accepts/11 rejects),47 actual WASI invocations
and18 Foundation reparses agree on complete type-sensitive values and bounded
summaries. Empty/unknown boxes, Bool/Int/Data/Date/nested values, duplicate boxes,
malformed late entries, required/optional empty/long String and wrong types covered.
The collision restriction is separately tested in Rust, not mislabeled as a native
rejection control. No private box method invoked. Disposable source/focused/public
composition/WASI replay passes; full347-test output retained separately.

No implementation verification failures. Initial copy-only observation was refined
using the actual outer PropertyList dictionary metadata before implementation.
Earlier symbol inventory identifies LocalizationOverride.localeIdentifier as an
optional String; that field remains deferred in favor of this protocol gap. REA
command/catalog identity matched; session closed/provider null. Controller lock
held. Raw Apple assembly/symbols remain local/ignored. No native process action,
Xcode MCP or system change. Both milestone contracts remain incomplete.

Next: useful native HashableBox/control-state codec mapping and service consumers,
structured preview identity, remaining request/localization/context fields and
actual lifecycle/rendering/transport/provider/resource correlation.
