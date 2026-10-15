# Portable preview refresh

An original, dependency-free JavaScript session for building and validating portable preview frames. Requires Node 18 or newer for the included tests. Run `npm test` (no installation required).

```js
import { createSession } from './index.js';
const session = createSession({
  build: async (source, signal) => render(source, signal),
  validate: async (candidate, source, signal) => inspect(candidate, signal),
});
await session.poll('preview source');
console.log(session.frame());
session.close();
```

`render` and `inspect` above are caller-provided functions. Both callbacks are required. Validation must return exactly `true` to accept a candidate; false, other values, and exceptions reject it. Callbacks may return values or promises. The build callback receives `(source, AbortSignal)`; validation receives `(candidate, source, AbortSignal)`.

## API

- `poll(source)` returns a promise. The first observed source and each changed source start an attempt. An unchanged source returns `{ changed: false, revision, generation }`, including after a failed attempt. Sources must be strings and are compared as complete strings without normalization.
- `refresh(source)` returns a promise and always starts an attempt, including unchanged or previously rejected source. Success returns `{ changed: true, revision, generation }` after validation and publication.
- `status()` synchronously returns `{ state, revision, generation, hasFrame, failure, failures }`. State is `idle`, `building`, `ready`, `failed`, or `closed`. Each failure record contains `generation`, `stage`, `code`, and `message`. Snapshots and failure records are copied; failure history survives recovery and close. While retrying, state is `building` and the prior failure remains until success.
- `frame()` synchronously returns `{ available: true, revision, value }` or `{ available: false, revision }`. A failed or pending attempt retains the accepted frame. Candidate values are caller-owned references, not cloned: callers should treat accepted values as immutable. The availability discriminator supports even an accepted `undefined` value.
- `close()` synchronously returns undefined, clears frame availability, aborts the active signal, and is idempotent. It preserves counters and failure history. Closed sessions remain inspectable. A late callback cannot publish, even if it ignores cancellation. Callback settlement is still required for its attempt promise to settle; close does not forcibly terminate callback work.

Counters start at zero. Every started build consumes one generation; only publication increments revision. A concurrent request rejects with `BUSY`, starts no build, and consumes no generation. Closed requests reject with `CLOSED`. Non-string source rejects with `TypeError` before consuming a generation. Operational failures reject with exported `RefreshError`, using `BUILD_FAILED` or `VALIDATION_FAILED`, and preserve the original exception in `cause`. A close racing with a pending callback produces `CLOSED` and does not record an ordinary rendering failure. Missing callbacks throw `TypeError` at session creation. No retry is automatic.

The session stores only the last observed source for polling, not a cache of all source strings. A request rejected because it is busy or closed never changes the observed source. Inspection remains available during callbacks. Independent sessions share no counters, frames, or failure history.

## Scope and verification

The built-in tests cover polling and retries, revision/generation accounting, validation ordering and rejection, concurrent requests, isolated sessions, and close during build or validation followed by either late success or late rejection. No native transport, Xcode Canvas compatibility, SwiftUI state preservation, compiler deadline, file watching, pixel-validation algorithm, or native resource lifetime is implemented. Each refresh is a new rendering attempt.

See `PROVENANCE.md` for the exact project input and separation limitation. This standalone slice does not pass either project's milestone or replace an existing reconstruction; integration requires separate review.
