//! Checked sequential projection of owned native BSAction reply admission.
//! No timer, dispatch queue, native object, wire message or callback is created.
//! Timeout/invalidation codes are scoped to the measured BaseBoard profile.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ActionError {
    pub domain: String,
    pub code: i64,
}
impl ActionError {
    pub fn local_timeout() -> Self {
        Self {
            domain: "BSActionErrorDomain".into(),
            code: 2,
        }
    }
    pub fn local_invalidation() -> Self {
        Self {
            domain: "BSActionErrorDomain".into(),
            code: 5,
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ReplyOutcome<T> {
    Success(T),
    Failure(ActionError),
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AlreadyClosed;
/// Caller-owned single reply gate. Native duplicate sendResponse traps; this
/// adapter instead returns AlreadyClosed and drops its rejected owned outcome.
/// It models admission/post-state only, not native scheduling or quiescence.
#[derive(Clone, Debug)]
pub struct ActionReplyGate {
    pending: bool,
}
impl Default for ActionReplyGate {
    fn default() -> Self {
        Self { pending: true }
    }
}
impl ActionReplyGate {
    pub fn can_send_response(&self) -> bool {
        self.pending
    }
    pub fn finish<T>(
        &mut self,
        outcome: ReplyOutcome<T>,
    ) -> Result<ReplyOutcome<T>, AlreadyClosed> {
        if !self.pending {
            return Err(AlreadyClosed);
        }
        self.pending = false;
        Ok(outcome)
    }
    /// Caller reports a deadline event. This method does not start/cancel timers
    /// or establish that target operations have stopped producing effects.
    pub fn expire<T>(&mut self) -> Option<ReplyOutcome<T>> {
        self.finish(ReplyOutcome::Failure(ActionError::local_timeout()))
            .ok()
    }
    /// Produces one local invalidation outcome while pending; subsequent calls
    /// are silent. No native cancellation or resource release is performed.
    pub fn invalidate<T>(&mut self) -> Option<ReplyOutcome<T>> {
        self.finish(ReplyOutcome::Failure(ActionError::local_invalidation()))
            .ok()
    }
}
