//! Sequential bookkeeping projection of PreviewShellKit HostPreferenceResolver.
//! This does not execute its Future/Promise, send scene actions, wait on fences,
//! or reproduce callback reentrancy, cancellation or scheduling semantics.
use crate::scene_timing::{SceneTiming, SceneUpdateSeed};
use std::collections::BTreeSet;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DuplicatePreferenceSeed(pub SceneUpdateSeed);

/// Caller-owned pending seed domain; no global service or thread synchronization.
/// The native duplicate branch removes the old registration and returns a failed
/// Future. Here it removes the seed and returns an explicit error. Effects on a
/// native dropped promise and its observers are deliberately not modeled.
#[derive(Clone, Debug, Default)]
pub struct PreferenceHandshakeTracker {
    pending: BTreeSet<i64>,
}
impl PreferenceHandshakeTracker {
    pub fn begin(&mut self, seed: SceneUpdateSeed) -> Result<(), DuplicatePreferenceSeed> {
        if self.pending.remove(&seed.0) {
            return Err(DuplicatePreferenceSeed(seed));
        }
        self.pending.insert(seed.0);
        Ok(())
    }
    /// Matching resolution is consumed once; unknown/duplicate replies are not
    /// buffered. Timing is a presence-derived tag, not GPU/display completion.
    /// A new request reusing the same seed cannot distinguish an old matching
    /// reply; callers must maintain the correct seed domain/uniqueness policy.
    /// Native code succeeds its promise before removing the dictionary entry;
    /// this method only returns the post-handler state, with no callbacks.
    pub fn resolve(&mut self, seed: SceneUpdateSeed, timing: SceneTiming) -> Option<SceneTiming> {
        self.pending.remove(&seed.0).then_some(timing)
    }
    pub fn contains(&self, seed: SceneUpdateSeed) -> bool {
        self.pending.contains(&seed.0)
    }
    pub fn len(&self) -> usize {
        self.pending.len()
    }
    pub fn is_empty(&self) -> bool {
        self.pending.is_empty()
    }
}
