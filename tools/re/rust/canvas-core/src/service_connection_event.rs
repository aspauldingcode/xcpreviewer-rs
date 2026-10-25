//! Non-dictionary connection events, separate from per-request replies.
//! Callers supply the recovered XPC Kind after native type classification.
use crate::{service_reply_dispatch::ServiceReplyNotifications, service_reply_failure::XpcFailure};

/// Connection-level handlers on the recovered event path. This owns Rust
/// callbacks only; it does not model a native weak connection, transport queue,
/// receiver or resource lifetime. The caller must route dictionary events to
/// the receiver separately and skip dispatch if its connection no longer exists.
pub struct ServiceConnectionEvents<I, V, E> {
    pub notifications: ServiceReplyNotifications<I, V>,
    pub connection_error: Option<E>,
}

impl<I: FnMut(), V: FnMut(), E: FnMut(XpcFailure)> ServiceConnectionEvents<I, V, E> {
    /// Dispatch one projected non-dictionary event. Interrupted/invalidated use
    /// only their specific optional Void handlers. Absence does not fall back to
    /// connection_error. Termination-imminent, invalid-type and unknown pass the
    /// unchanged Kind to connection_error when present.
    ///
    /// This route has no request completion. Returning does not acknowledge a
    /// message, cancel the connection or prove target/resource settlement.
    pub fn dispatch_error(&mut self, error: XpcFailure) {
        match error {
            XpcFailure::ConnectionInterrupted => {
                if let Some(handler) = &mut self.notifications.interruption {
                    handler();
                }
            }
            XpcFailure::ConnectionInvalidated(_) => {
                if let Some(handler) = &mut self.notifications.invalidation {
                    handler();
                }
            }
            other => {
                if let Some(handler) = &mut self.connection_error {
                    handler(other);
                }
            }
        }
    }
}
