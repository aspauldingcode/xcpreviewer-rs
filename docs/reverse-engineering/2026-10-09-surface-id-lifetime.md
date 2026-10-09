# Owned global surface-ID lookup after final release

The existing audit-verified delayed-reuse fixture now samples global IOSurfaceLookup(ID), separately from imported task-local Mach-name lookup. It waits for receiver success and exit, accounts for sender rights, drops sender Mach rights, checks live lookup while CF aliases remain, drops those aliases, then samples lookup immediately and after a requested 100ms sleep. Each lookup temporarily retains and releases its returned object.

## Results and falsification

The registered immediate-null prediction fails in two of 16 executions, both separate-storage cases: the first ID still resolves while the second returns null. Live lookup controls resolve both expected IDs. The native helper exits successfully, but the fail-closed verifier refuses to promote those outcomes. This run is sealed and conservatively inconclusive; it contradicts universal immediate disappearance within the reviewed scope.

A separately registered delayed control accepts either null or the expected ID for the immediate observation and requires null for both IDs at the requested 100ms followup. Four shapes × reuse/separate × two repeats all pass. In this second campaign all immediate lookups were also null. Therefore it does **not** establish that the delay caused disappearance, nor reproduce a positive-immediate-to-null transition in one execution. The first campaign's transient positive result may involve asynchronous teardown, lookup effects or ID recycling; those explanations are not distinguished here.

The supporting campaign verifies 80 independent full-byte comparisons totaling 51,200 bytes, including row padding and seed wraparound. The initial campaign retains 70 comparisons totaling 40,320 bytes; the two failed lifecycle observations prevent their repetitions from passing. Receiver audit identity, actual wait status, coalesced/independent import-right counts, retired Mach-name lookup and CF-alias pixel survival checks remain in force.

All 110 tests pass. New negative controls reject absent values, boolean/integer substitutions, failed live controls, unreleased sender aliases, invalid immediate IDs and changed delay metadata. Both sealed manifests and frozen sources verify; [sanitized observations and anchors](../../research/evidence/surface-id-lifetime-2026-10-09.json) retain failures as well as successes. No Xcode windows opened.

## Acceptance limits

This measures lookup reachability under owned CPU controls, not physical memory reclamation or kernel residency. There is no arbitrary global-ID recycling exclusion, allocation-pressure control, GPU completion, live Canvas acknowledgement or complete release proof across all failure paths. The requested sleep is a controlled input, not a measured timing bound for resource destruction. R1/R2 and both milestones remain open.

Next obtain an independent identity/reclamation or completion observable; do not repeat the falsified immediate-null expectation as a success gate. The [prior imported-name checkpoint](2026-10-09-retired-name.md) remains a distinct boundary while CF aliases live.
