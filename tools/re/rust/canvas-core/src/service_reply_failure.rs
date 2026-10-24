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

/// TransportReply selects serialized data on its recovered macOS14.4+ path and
/// a dictionary on its legacy path. Cross-platform callers choose explicitly;
/// this enum neither detects the OS nor specifies numeric wire discriminants.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ReplyRepresentation {
    SerializedData,
    DeserializedDictionary,
}
/// Compose the dictionary wire initializer, NSError recognition and incoming
/// reply representation. This models the supplied observations only; decoder
/// must match the desired Foundation/profile behavior (including XML if needed).
///
/// Recognition's empty-dictionary fallback must not replace original serialized
/// bytes: a selected success can fail during later typed decoding. The legacy
/// dictionary path reads the getter again, matching its uncached conversion.
/// Raw description is requested only if the wire initializer rejects. No native
/// handler side effects, error-object bridging or target settlement is modeled.
pub fn classify_service_xpc_dictionary_with<E>(
    fields: &BTreeMap<String, crate::settings_xpc::XpcValue>,
    representation: ReplyRepresentation,
    mut decode: impl FnMut(&[u8]) -> Result<Value, E>,
    raw_description: impl FnOnce() -> String,
) -> (Option<LazyReply>, Option<ServiceReplyFailure>) {
    use crate::service_property_list::ServicePropertyList;
    let Some(property_list)=ServicePropertyList::from_xpc_dictionary(fields) else {
        return (None,Some(ServiceReplyFailure::Xpc(XpcFailure::InvalidType(raw_description()))));
    };
    let recognition_fields=property_list.dictionary_with(&mut decode);
    if let Some(error)=ServiceReplyError::recognize(&recognition_fields) {
        return (None,Some(ServiceReplyFailure::Remote(error)));
    }
    let payload=match representation {
        ReplyRepresentation::SerializedData => LazyReply::Serialized(property_list.data_with(|_| -> Result<Vec<u8>,()> {unreachable!("wire initializer stores bytes")})),
        ReplyRepresentation::DeserializedDictionary => LazyReply::Deserialized(property_list.dictionary_with(decode)),
    };
    (Some(payload),None)
}
