//! Project observed service reply categories into nullable callback values.
//! Caller supplies XPC category, descriptions and decoded dictionary results.
//! This is not an XPC/UVPropertyList decoder or connection lifecycle controller.
use crate::{payload_codec::Value, service_reply_error::{ServiceReplyError, split_dictionary_reply}, transport_reply::LazyReply};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum XpcFailure {
    ConnectionInvalidated(String),
    InvalidType(String),
    Unknown(String),
    ConnectionInterrupted,
    TerminationImminent,
}
/// Observations at the recovered XPC error classifier boundary. Invalidation
/// reason comes from the connection; unknown description comes from the event.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ObservedXpcError {
    ConnectionInvalidated { reason: Option<String> },
    ConnectionInterrupted,
    TerminationImminent,
    Other { description: Option<String> },
}
impl ObservedXpcError {
    pub fn classify(self) -> XpcFailure {
        match self {
            Self::ConnectionInvalidated {reason} => XpcFailure::ConnectionInvalidated(reason.unwrap_or_else(|| "<no description>".into())),
            Self::ConnectionInterrupted => XpcFailure::ConnectionInterrupted,
            Self::TerminationImminent => XpcFailure::TerminationImminent,
            Self::Other {description} => XpcFailure::Unknown(description.unwrap_or_else(|| "<no description>".into())),
        }
    }
}
#[derive(Clone, Debug, PartialEq)]
pub enum ServiceReplyInput {
    DecodedDictionary(BTreeMap<String, Value>),
    /// Actual initWithXpcDictionary returned nil; description is of raw XPC input.
    RejectedDictionary { description: String },
    /// An object whose XPC type is neither dictionary nor error.
    OtherType { description: String },
    Error(ObservedXpcError),
}
#[derive(Clone, Debug, PartialEq)]
pub enum ServiceReplyFailure {
    Remote(ServiceReplyError),
    Xpc(XpcFailure),
}
/// Non-dictionary and rejected-dictionary inputs become nil/error callbacks;
/// decoded dictionaries retain the recovered service error schema classifier.
/// This does not execute connection handlers/invalidation, bridge native error
/// objects, determine callback ordering, or establish target/resource settlement.
pub fn classify_service_reply(input: ServiceReplyInput) -> (Option<LazyReply>, Option<ServiceReplyFailure>) {
    match input {
        ServiceReplyInput::DecodedDictionary(fields) => {
            let (payload,error)=split_dictionary_reply(fields);
            (payload,error.map(ServiceReplyFailure::Remote))
        },
        ServiceReplyInput::RejectedDictionary {description} | ServiceReplyInput::OtherType {description} =>
            (None,Some(ServiceReplyFailure::Xpc(XpcFailure::InvalidType(description)))),
        ServiceReplyInput::Error(event) => (None,Some(ServiceReplyFailure::Xpc(event.classify()))),
    }
}
