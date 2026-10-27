//! Serial reply state from native success/failure/cancellation controls.
//! Local state only: no transport cancellation, callback gate or resource settlement.
#[derive(Debug, PartialEq)]
pub enum ReplyTermination<T, E, C> {
    Completed(Result<T, E>),
    Canceled(C),
}
/// Retains the first completion or cancellation context. Callers synchronize access.
/// Native diagnostics, observer scheduling and transport effects are outside this
/// profile. Returning rejected values is original Rust ownership policy.
#[derive(Debug)]
pub struct ReplyCompletion<T, E, C = ()> {
    termination: Option<ReplyTermination<T, E, C>>,
}
impl<T, E> ReplyCompletion<T, E> {
    pub const fn new() -> Self {
        Self { termination: None }
    }
}
impl<T, E, C> ReplyCompletion<T, E, C> {
    /// None includes running and canceled states; inspect termination to distinguish.
    pub fn result(&self) -> Option<&Result<T, E>> {
        match &self.termination {
            Some(ReplyTermination::Completed(result)) => Some(result),
            _ => None,
        }
    }
    /// None means running. Cancellation context is caller-owned, not native ABI.
    pub fn termination(&self) -> Option<&ReplyTermination<T, E, C>> {
        self.termination.as_ref()
    }
    /// Store the first outcome; otherwise return the proposed outcome unchanged.
    /// Decode a callback before calling this method. A finished/canceled result
    /// does not imply that later callbacks or their decoding cannot execute.
    pub fn try_complete(&mut self, outcome: Result<T, E>) -> Result<(), Result<T, E>> {
        if self.termination.is_some() {
            Err(outcome)
        } else {
            self.termination = Some(ReplyTermination::Completed(outcome));
            Ok(())
        }
    }
    /// Record cancellation while running; otherwise return the context unchanged.
    /// This sends no cancellation request, releases no backend captures, and does
    /// not interrupt target work. Use Default for a custom context type.
    pub fn try_cancel(&mut self, context: C) -> Result<(), C> {
        if self.termination.is_some() {
            Err(context)
        } else {
            self.termination = Some(ReplyTermination::Canceled(context));
            Ok(())
        }
    }
}
impl<T, E, C> Default for ReplyCompletion<T, E, C> {
    fn default() -> Self {
        Self { termination: None }
    }
}
