# Executable Xcode Canvas RSE graph loop

The graph runner implements bounded execution of the [RSE task graph](canvas-rse-task-graph.md)
through the existing reviewed adapters, including `rea_native`. It does not
generate native ABI calls, start agents, or publish releases. The reasoning
agent still designs new experiments and reviews scientific coverage.

## Entry points

```sh
# Inspect eligible tasks and receive the actual pinned Caveman FULL instructions.
research/venv/bin/python tools/re/agent.py graph-loop

# Execute up to four graph-selected reviewed experiments within one shared budget.
research/venv/bin/python tools/re/agent.py graph-loop --execute

# Resume a recorded wake, retaining its original deadline and expenditure.
research/venv/bin/python tools/re/agent.py graph-loop --execute --resume WAKE_ID
```

The controller MCP server also exposes `re_graph_loop` and `re_graph_loop_run`.
The latter automatically resumes a running interrupted wake. An explicitly new
invocation after a finished wake creates a new bounded wake; it does not bypass
failure memory or track prerequisites. No new scheduler is installed.

`research/loop/graph-runner.json` contains explicit task-to-experiment bindings,
limits and the installed Caveman skill path/hash. Bind only reviewed campaign
experiments within the task's allowed completion IDs. New adapters follow the
existing queue/schema review. REA keeps its pinned provider/profile and owned
cleanup rules. Blocked native/REA/browser routes stay blocked.

## Persistent state

`research/state/graph-loop.json` stores wake IDs, original deadlines, immutable
configuration hashes, round contracts, selected issue/scope, frozen spec and
environment hashes, manifests, anchor hashes, verification results and failure
fingerprints. Every wake carries the loaded Caveman FULL instructions. The
reasoning agent must apply them to user messages; Python verifies and serves
those instructions but does not rewrite generated prose. Code/docs use normal
precise language.

One controller lock covers selection, execution and checkpoint writes. Each round
is written before execution. Interrupted rounds are reconciled against new sealed
runs and charged to the original budget; they are never silently retried or
accepted. Ambiguous or absent execution records produce `reconciliation-required`
and block automatic new wakes until the checkpoint is explicitly reconciled.
Existing recovery refuses to act on a still-live recorded process of uncertain
ownership.

The budget covers all rounds: four round slots, four experiments, fifteen wall
clock minutes and 1 GiB of measured run artifacts. The runner passes remaining
time/bytes to each adapter, reserves five seconds for verification, and charges
sealed failures as well as successes. Source freezing, environment inspection,
checkpoint I/O and cleanup may consume time; existing adapter/process cleanup
can exceed the nominal execution deadline while terminating owned resources.
Limits prevent launching further work and never authorize skipping cleanup.

Fresh-process verification checks the separately retained manifest hash, complete
artifact consistency, frozen experiment identity and recomputed declared checks.
Successful research is overlaid in memory only after **every bound experiment**
has a matching verified result. A changed experiment spec invalidates its local
completion. Original quarantine entries and conflicting external anchors take
precedence. Shared campaign, delivery attestations and continuous checkpoint are
not automatically rewritten.

Failures persist across wakes. An unchanged task/spec/prerequisite/environment
fingerprint requires a relevant change before execution. Other eligible tasks
can proceed. If only blockers remain, the runner returns resumable prerequisites.

## Independent delivery review

Mechanical success is `scoped-support`, with delivery still `review-pending`.
The runner never invents a reviewer or creates acceptance attestations.
Completion additionally requires every native and portable delivery node to pass
the existing anchored-evidence/dependency gate and have an independent review
artifact sealed in a supporting run. This records an external review assertion;
the runner cannot itself establish that a human or model reviewed honestly.

An attestation adds:

```json
{
  "contract_reviewed": true,
  "runs": ["ACCEPTED_RUN_ID"],
  "coverage_path": "output/coverage.json",
  "independent_review": {
    "run_id": "ACCEPTED_RUN_ID",
    "path": "output/independent-review.json"
  }
}
```

The sealed coverage artifact declares a nonempty unique `required_checks` list.
The sealed review artifact has `issue`, nonempty `reviewer_id`, `independent: true`,
`verdict: "accepted"`, matching `coverage_path`, and a `coverage` list containing
exactly those IDs with `accepted: true`. Missing, duplicate or extra review rows,
corrupt evidence, stale anchors or unmet dependencies prevent completion. The
reviewer must reconcile that declared list with the actual delivery contract;
passing an incomplete self-declared list does not prove full Xcode compatibility.

## Validation

Tests use real sealed temporary artifacts and a separate verifier process.
They cover multiple required experiments, interruption and resume, shared limits,
unchanged failures, changed specs, corrupted artifacts, anchor conflicts,
quarantine, lock exclusion, skill identity and independent-review gates.
These are runner controls, not native Canvas or portable product acceptance.

The evidence storage/retrieval implementation remains `reloop.evidence.Store`.
The broader typed knowledge-graph pilot in the design is separate future work;
this implementation builds the task execution graph.
