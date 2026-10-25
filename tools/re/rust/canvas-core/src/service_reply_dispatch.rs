//! Connection notifications on the recovered send-with-reply path.
//! This portable adapter uses projected reply values. It is not an XPC event
//! handler, native cancellation controller or target/resource settlement signal.
use crate::{
    service_reply_failure::{ServiceReplyFailure, XpcFailure},
    transport_reply::{LazyReply, ReplyError},
};

/// Optional connection-level Void handlers, separate from each request's
/// completion. Rust ownership and callback types are reconstruction interfaces;
/// no native Swift ABI, queue, thread or lifetime guarantee is implied.
pub struct ServiceReplyNotifications<I, V> {
    pub interruption: Option<I>,
    pub invalidation: Option<V>,
}

impl<I: FnMut(), V: FnMut()> ServiceReplyNotifications<I, V> {
    /// Notify interruption/invalidation before forwarding the unchanged reply.
    /// Termination-imminent, invalid-type, unknown and remote NSError replies
    /// do not notify either handler. Missing handlers still allow completion.
    ///
    /// One local invocation consumes one completion closure. This does not prove
    /// native exactly-once delivery, delivery after cancellation or settlement.
    /// Panics, reentrant native destruction and concurrent delivery are outside
    /// this synchronous portable profile.
    pub fn dispatch<T>(
        &mut self,
        outcome: Result<LazyReply, ReplyError<ServiceReplyFailure>>,
        complete: impl FnOnce(Result<LazyReply, ReplyError<ServiceReplyFailure>>) -> T,
    ) -> T {
        match &outcome {
            Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
                XpcFailure::ConnectionInterrupted,
            ))) => {
                if let Some(handler) = &mut self.interruption {
                    handler();
                }
            }
            Err(ReplyError::Remote(ServiceReplyFailure::Xpc(
                XpcFailure::ConnectionInvalidated(_),
            ))) => {
                if let Some(handler) = &mut self.invalidation {
                    handler();
                }
            }
            _ => {}
        }
        complete(outcome)
    }

    /// Drop these two notification captures in source clear order. This is only
    /// the local notification-slot operation: it does not cancel a connection,
    /// clear a receiver/connection-error handler or touch per-request captures.
    pub fn clear_connection_notifications(&mut self) {
        self.interruption = None;
        self.invalidation = None;
    }
}
