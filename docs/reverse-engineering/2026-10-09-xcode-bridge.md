# Direct Xcode route and client interoperability

## Question and prediction

The prior bridge initialized but stalled during discovery. Competing explanations were discovery-specific failure, an unhandled reverse server request, or unavailable downstream Xcode service/access. If bypassing discovery with an explicitly selected Xcode session and handling reverse requests sufficed, a bounded `XcodeListWindows` call would return. Initialization alone would not satisfy that condition.

## Sealed observation

Run `20261009T151924Z-xcode-direct-read-route-f15cc7da` selected the single installed Xcode process and a fresh session identifier. It used a 12-second request deadline within the exclusive controller's 60-second experiment deadline. The native bridge returned initialize metadata, received the initialized notification and direct tool request, and returned no tool response. Four protocol messages were recorded, with no discovery call and no reverse server request. Adapter execution succeeded in reporting the timeout; the controller verdict remains **inconclusive**, not successful capture or proof that the tool is absent.

Artifacts and frozen sources verify against the [published manifest anchor](../../research/evidence/xcode-bridge-route-2026-10-09.json). Raw protocol messages and window responses remain local. Xcode 26.6 build 17F113 is the pinned environment for this run.

A separate read-only accessibility inspection found Xcode's pending permission prompt for `preview-reloop`, using Apple's signed local Python runtime. The prompt grants building, testing and modifying code through Xcode tools. No permission was granted; explicit user approval is requested under the computer-use confirmation policy. This UI observation is not part of the sealed protocol trace and does not yet establish the timeout's cause. The pending request may outlive its bounded client process.

## Implemented fixes and controls

The shared MCP client now responds to server ping requests and returns method-not-found for unsupported server methods before comparing client request IDs. Server and client IDs can collide. Previously, reverse requests could be mistaken for responses or silently dropped. MCP permits either party to initiate ping and requires an empty successful reply ([official protocol specification](https://modelcontextprotocol.io/specification/2024-11-05/basic/utilities/ping)).

An independent owned bridge deliberately collides server IDs with both initialization and tool-call IDs, waits for each required client reply and only then returns the client response. This passes without hanging. Tests also reject initialization-only readiness and ensure the planner never requeues an unchanged timeout. The diagnostic adapter records discovery/reverse-request distinctions and capped local message logs. The client closes owned subprocess pipes after shutdown.

All 87 automated tests pass in the permitted owned-subprocess context with ResourceWarning treated as an error. Toolkit now exposes 23 reviewed adapters and 19 research MCP tools. These controls establish client behavior, not a causal explanation of the native failure: no reverse request occurred in that native trace.

## Next discriminating control

After explicit approval, inspect the current prompt and permission state, then repeat the bounded direct read-only call in a fresh session. A returned tool result would establish service responsiveness under that changed state. Only then attempt the separate owned-project Canvas capture and its repeat/change controls. If access remains blocked, switch to independent renderer/portable feasibility work rather than repeating this unchanged route. O2 remains open; no Canvas pixels, wire semantics or milestone completion are claimed.
