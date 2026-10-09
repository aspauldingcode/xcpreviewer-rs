# ServiceMessage optional identifier path

Target identity is unchanged from the [codec key checkpoint](2026-10-09-codec-boundaries.md). Four bounded read-only disassembly runs select public entrypoints, the content closure, the messageType/payload initializer and the payload getter. [Sanitized evidence and manifest anchors](../../research/evidence/service-identifier-path-2026-10-09.json) verify all artifacts and frozen sources.

## Static path

The public propertyListValue getter constructs a PropertyList from a content closure. That closure obtains messageType and calls the payload getter before building the outer dictionary. The recovered outer keys are messageType/payload; the identifier is handled inside the payload path.

At `0x5ed18`, the payload getter calls PropertyList.archiveValue after selecting the singleton PayloadKey witness and Swift.String metadata/conformance. The generic archive API takes an optional value. The messageType/payload initializer selects the same PayloadKey witness and calls PropertyList.unarchiveOptionalValue with Swift.String metadata/conformance at `0x5fc3c`. On the successful path, the returned two-word value is stored at the output base before content dispatch (`0x5fcb4`). This agrees with the nominal optional String identifier field and the prior returned key string `__unique_service_message_identifier`.

This is a static encode/decode path for an optional identifier, not proof of actual request/reply matching. There is no observed response propagation, generation, reuse, completion, null representation or wrong-type behavior.

## Falsification and limits

The initial exact-site query expected a closure name immediately followed by `in`; the demangler inserts the closure signature. It selected only one initializer instead of two functions, and the sealed run remains inconclusive. A corrected anchored selector includes the observed signature and returns the closure plus initializer, excluding partial-apply thunks. Public entrypoint selection returns two functions; the dependent payload getter selection returns one.

Controller checks establish function selection counts. The call-site analysis above is separately scoped analyst interpretation of those sealed artifacts, not an executed value-level hypothesis. The existing 109-test implementation checkpoint remains unchanged; the new campaign entries validate against the reviewed queue validator. No Xcode windows were opened; raw Apple disassembly stays local.

Next obtain absent/present/wrong-type identifier controls through a safe native codec boundary and independent expectations, then inspect response propagation and live envelope correlation. No fabricated Swift ABI declarations or protection changes are warranted. R2/P1/P2 and both milestones remain open.
