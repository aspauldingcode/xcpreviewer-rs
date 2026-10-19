# Separate verifier review

The verifier accepted the initial twenty-case pending/dispatch model but independently reproduced an expiry reversal: begin rejected at11 against deadline10, then cleanup reported timely after clock1. Publication was blocked until expiry and invalid/regressing clocks latched permanently. The earlier source is retained as settlement-before-clock-latch.mjs. Additional boundary, regression, NaN and throwing-clock controls now pass.

The coordinator initially also lacked a recheck inside the dispatch microtask; the earlier source is retained as settlement-before-dispatch-recheck.mjs. Expanded stop-before-dispatch controls reject it.

The verifier independently ran all25 corrected cases, both retained prototypes and six mutants and approved the corrected source for evidence-only publication. It explicitly required native eligibility to remain false and the native UI cleanup block to stay in force because trusted callback settlement is not bounded/cancellable provider proof.
