//! Dictionary receiver routing recovered from the connection event path.
//! Reply capability is caller-supplied; no native XPC or Swift ABI is invoked.
use crate::{service_property_list::ServicePropertyList, settings_xpc::XpcValue};
use std::collections::BTreeMap;

/// Original portable receiver interface. R is an opaque reply capability owned
/// by the caller's transport; it may represent a deferred callback or channel.
/// This trait imposes no native exactly-once or cancellation guarantee.
pub trait ServiceMessageReceiver<R> {
    fn receive(&mut self, message: ServicePropertyList);
    fn receive_with_reply(&mut self, message: ServicePropertyList, reply: R);
}

#[derive(Clone, Debug, PartialEq)]
pub enum ServiceReceiverMessage<R> {
    OneWay(ServicePropertyList),
    WithReply {
        message: ServicePropertyList,
        reply: R,
    },
}

/// Initialize the value-only local-construction profile before asking for a
/// reply capability. Missing, wrong-type and empty data reject before that call.
/// Nonempty malformed/non-dictionary plist bytes remain lazy receiver input.
///
/// None reports only rejected wire initialization. The caller can then report
/// InvalidType through its optional connection error handler; no reply is made.
/// This does not recognize NSError-shaped message dictionaries as reply errors.
pub fn prepare_service_dictionary<R>(
    fields: &BTreeMap<String, XpcValue>,
    create_reply: impl FnOnce() -> Option<R>,
) -> Option<ServiceReceiverMessage<R>> {
    prepare_initialized_message(
        ServicePropertyList::from_xpc_dictionary(fields),
        create_reply,
    )
}
/// Receipt-aware initialization from an observed native data byte pointer/slice.
/// Some(empty) is valid: initialization precedes reply-capability creation even
/// when later dictionary parsing falls back to empty. None skips the creator.
pub fn prepare_observed_service_data<R>(
    bytes: Option<&[u8]>,
    create_reply: impl FnOnce() -> Option<R>,
) -> Option<ServiceReceiverMessage<R>> {
    prepare_initialized_message(
        ServicePropertyList::from_observed_xpc_data(bytes),
        create_reply,
    )
}
fn prepare_initialized_message<R>(
    message: Option<ServicePropertyList>,
    create_reply: impl FnOnce() -> Option<R>,
) -> Option<ServiceReceiverMessage<R>> {
    let message = message?;
    Some(match create_reply() {
        Some(reply) => ServiceReceiverMessage::WithReply { message, reply },
        None => ServiceReceiverMessage::OneWay(message),
    })
}

impl<R> ServiceReceiverMessage<R> {
    /// Deliver to the selected receiver method, or drop local values if absent.
    /// Absence generates no default response or generic connection notification.
    /// Dropping an opaque Rust R does not prove native reply/right settlement.
    pub fn dispatch_to(self, receiver: Option<&mut dyn ServiceMessageReceiver<R>>) {
        let Some(receiver) = receiver else {
            return;
        };
        match self {
            Self::OneWay(message) => receiver.receive(message),
            Self::WithReply { message, reply } => receiver.receive_with_reply(message, reply),
        }
    }
}
