# Independent typed-pilot entity review — 2026-10-15

Reviewer `/root/refresh_spec_review` independently reviewed all 50 original predictions produced by `/root/canvas_evidence_review` against the existing ontology and the exact ten source reports. One bounded pass; no repaired predictions were scored.

Accepted **35/50**; rejected **15/50**; entity precision **70%**. The eligible denominator is **50**, including rejected predictions. The entity gate is **not qualified** (requires ≥90%). Relation denominator is zero and precision unavailable; no combined gate passes.

All source digests, exact Unicode mention/context spans, containment, line spans, ontology definition strings and bounded scope checks passed. These checks establish extraction provenance, not proposition truth or native target identity. Ten report Evidence entities and twenty explicit Claim entities fit their definitions. Five singular frame-result mentions fit Frame in context.

The timestamped Event definition is applied literally. The report narrative supplies relative ordering, but these predictions provide no explicit timestamp binding. Several mutation/assignment/use-count triggers additionally fall outside the listed Event kinds. Grouped frame, resource and process mentions are not silently split, narrowed or promoted. Original predictions are retained verbatim in the JSON, including all rejections.

| Candidate | Judgment | Reason |
|---|---|---|
| typed-pilot-001 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-002 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-003 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-004 | reject | Generic relative-order binding mutation, not an individually timestamped request, render, completion, cancellation or release. |
| typed-pilot-005 | reject | Explicit baseline/repeat plural frame group is proposed as one Frame; no singular result is selected. |
| typed-pilot-006 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-007 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-008 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-009 | reject | Binding mutation trigger is outside the enumerated Event definition and has no timestamp. |
| typed-pilot-010 | accept | Context identifies a concrete accepted rendering result with color, geometry or publication identity; Frame does not require every attribute in the mention. |
| typed-pilot-011 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-012 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-013 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-014 | reject | Content assignment is not one of the ontology Event kinds and is not timestamped. |
| typed-pilot-015 | accept | Context identifies a concrete accepted rendering result with color, geometry or publication identity; Frame does not require every attribute in the mention. |
| typed-pilot-016 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-017 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-018 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-019 | reject | Content assignment is not one of the ontology Event kinds and is not timestamped. |
| typed-pilot-020 | accept | Context identifies a concrete accepted rendering result with color, geometry or publication identity; Frame does not require every attribute in the mention. |
| typed-pilot-021 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-022 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-023 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-024 | reject | Each of two helpers creates a different surface. The canonical singular backing resource merges two resource identities without selecting a run. |
| typed-pilot-025 | reject | Use-count increment is outside the listed Event kinds and lacks a timestamp; relative ordering does not supply one. |
| typed-pilot-026 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-027 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-028 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-029 | reject | Both Mach resource names explicitly denotes two distinct attachments; one Resource identity cannot represent this group. |
| typed-pilot-030 | reject | Use-count decrement is not necessarily a resource release and is not an individually timestamped event. |
| typed-pilot-031 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-032 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-033 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-034 | reject | Refresh request is a plausible event trigger, but the report mention has no timestamp and cannot satisfy the existing timestamped Event definition. |
| typed-pilot-035 | accept | Context identifies a concrete accepted rendering result with color, geometry or publication identity; Frame does not require every attribute in the mention. |
| typed-pilot-036 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-037 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-038 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-039 | reject | Timeout trigger is plausible cancellation/completion behavior, but this report mention lacks a timestamp or an explicit timestamp binding. |
| typed-pilot-040 | accept | Context identifies a concrete accepted rendering result with color, geometry or publication identity; Frame does not require every attribute in the mention. |
| typed-pilot-041 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-042 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-043 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-044 | reject | The two-control context does not select one receive-only name/right identity; a role label alone cannot resolve a singular Resource. |
| typed-pilot-045 | reject | Destruction is a plausible release trigger, but refers to envelopes across controls without an individual timestamp or selected occurrence. |
| typed-pilot-046 | accept | Title identifies this scoped source report, satisfying Evidence; no native target identity is inferred. |
| typed-pilot-047 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-048 | accept | Explicit report proposition correctly typed as Claim; acceptance establishes extraction fidelity, not truth or independent runtime verification. |
| typed-pilot-049 | reject | Both explicitly groups two abort requests and supplies neither individual timestamp nor occurrence identity. |
| typed-pilot-050 | reject | A root and detached child are two process roles, not one owned workspace/process lifetime; workspace/session identity is absent. |

This convenience sample is balanced by report and dominated by Evidence/Claim types; precision does not generalize to runtime extraction. No raw evidence was rerun and no native/UI/compile, product, Git, delegation, fusion or attestation action occurred. Both output files were written while holding the repository Controller lock.
