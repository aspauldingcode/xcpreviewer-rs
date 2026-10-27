//! Serial reply-result completion after native first-result retention controls.
//! Not a transport, callback gate, cancellation API, or resource settlement signal.
/// Retains the first fully projected success/failure. Callers synchronize access.
/// Native Future diagnostics, observer scheduling and cancellation are outside
/// this profile. Returning a rejected value is original Rust ownership policy.
#[derive(Debug)]
pub struct ReplyCompletion<T, E> {
    result: Option<Result<T, E>>,
}
impl<T, E> ReplyCompletion<T, E> {
    pub const fn new() -> Self {
        Self { result: None }
    }
    pub fn result(&self) -> Option<&Result<T, E>> {
        self.result.as_ref()
    }
    /// Store the first outcome; otherwise return the proposed outcome unchanged.
    /// Project/decode a callback before calling this method. A completed result
    /// does not imply that later callbacks or their decoding cannot execute.
    pub fn try_complete(&mut self, outcome: Result<T, E>) -> Result<(), Result<T, E>> {
        if self.result.is_some() {
            Err(outcome)
        } else {
            self.result = Some(outcome);
            Ok(())
        }
    }
}
impl<T, E> Default for ReplyCompletion<T, E> {
    fn default() -> Self {
        Self::new()
    }
}
