/** An operational error with a stable machine-readable code. */
export class RefreshError extends Error {
  constructor(code, message, options) {
    super(message, options);
    this.name = 'RefreshError';
    this.code = code;
  }
}

/** Create an independent portable preview session. Both callbacks are required. */
export function createSession({ build, validate } = {}) {
  if (typeof build !== 'function' || typeof validate !== 'function') {
    throw new TypeError('build and validate callbacks are required');
  }
  let closed = false;
  let active = null;
  let observed = false;
  let lastSource;
  let accepted;
  let available = false;
  let revision = 0;
  let generation = 0;
  let currentFailure = null;
  const failures = [];

  function status() {
    return {
      state: closed ? 'closed' : active ? 'building' : currentFailure ? 'failed' : available ? 'ready' : 'idle',
      revision,
      generation,
      hasFrame: available,
      failure: currentFailure && { ...currentFailure },
      failures: failures.map(failure => ({ ...failure })),
    };
  }

  async function attempt(source, force) {
    if (closed) throw new RefreshError('CLOSED', 'Session is closed');
    if (active) throw new RefreshError('BUSY', 'A rendering attempt is already running');
    if (typeof source !== 'string') throw new TypeError('source must be a string');
    if (!force && observed && source === lastSource) {
      return { changed: false, revision, generation };
    }
    observed = true;
    lastSource = source;
    const operation = { generation: ++generation, controller: new AbortController() };
    active = operation;
    let stage = 'build';
    try {
      const candidate = await build(source, operation.controller.signal);
      if (closed) throw new RefreshError('CLOSED', 'Session closed before publication');
      stage = 'validation';
      const valid = await validate(candidate, source, operation.controller.signal);
      if (closed) throw new RefreshError('CLOSED', 'Session closed before publication');
      if (valid !== true) throw new RefreshError('VALIDATION_FAILED', 'Validation must return true');
      accepted = candidate;
      available = true;
      revision += 1;
      currentFailure = null;
      return { changed: true, revision, generation: operation.generation };
    } catch (cause) {
      // Closing is terminal, including when callbacks ignore cancellation or reject late.
      if (closed) throw new RefreshError('CLOSED', 'Session closed before publication', { cause });
      const code = stage === 'build' ? 'BUILD_FAILED' : 'VALIDATION_FAILED';
      const error = new RefreshError(code, stage === 'build' ? 'Build failed' : 'Validation failed', { cause });
      currentFailure = { generation: operation.generation, stage, code, message: error.message };
      failures.push(currentFailure);
      throw error;
    } finally {
      if (active === operation) active = null;
    }
  }

  return Object.freeze({
    poll: source => attempt(source, false),
    refresh: source => attempt(source, true),
    status,
    frame: () => available ? { available: true, revision, value: accepted } : { available: false, revision },
    close() {
      if (closed) return;
      closed = true;
      accepted = undefined;
      available = false;
      active?.controller.abort();
    },
  });
}
