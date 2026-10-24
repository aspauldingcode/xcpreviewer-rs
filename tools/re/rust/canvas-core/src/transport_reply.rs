//! Incoming reply selection and lazy dictionary decoding recovered from the
//! pinned TransportReply.makeEncodedReplyHandler and LazyPropertyList getter.
//! This is a value adapter, not a transport, promise or settlement detector.
//! Native NSError humanReadable conversion and Foundation XML/coercion behavior
//! are outside this portable binary-plist subset.
use crate::{binary_plist, payload_codec::Value};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq)]
pub enum LazyReply {
    /// Original encoded bytes, retained without parsing at callback selection.
    Serialized(Vec<u8>),
    Deserialized(BTreeMap<String, Value>),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DecodeError {
    Plist(binary_plist::Error),
    NonDictionary,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ReplyError<E> {
    /// The caller's projected error; native humanReadable bridging is not modeled.
    Remote(E),
    EmptyReply,
}
impl LazyReply {
    /// Resolve a dictionary on demand. The bounded binary reader's limits and
    /// malformed-input policy remain original reconstruction choices. Native
    /// Foundation also accepts formats not supported here (including XML).
    pub fn property_list(&self) -> Result<BTreeMap<String, Value>, DecodeError> {
        match self {
            Self::Deserialized(fields) => Ok(fields.clone()),
            Self::Serialized(bytes) => match binary_plist::decode(bytes).map_err(DecodeError::Plist)? {
                Value::Dictionary(fields) => Ok(fields),
                _ => Err(DecodeError::NonDictionary),
            },
        }
    }
}
/// Mirror native nullable callback precedence: a present payload wins even if
/// an error is also supplied. Absent payload uses the error, or EmptyReply.
/// Selection does not parse bytes, claim exactly-once delivery or settle work.
pub fn select_reply<E>(payload: Option<LazyReply>, error: Option<E>) -> Result<LazyReply, ReplyError<E>> {
    match payload {
        Some(payload) => Ok(payload),
        None => Err(error.map_or(ReplyError::EmptyReply, ReplyError::Remote)),
    }
}

/// Distinguish callback selection, lazy parsing and typed payload failures.
/// Error variants are an original portable diagnostic interface.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TypedReplyError<E, D> {
    Reply(ReplyError<E>),
    Decode(DecodeError),
    Payload(D),
}
/// Convert a successful lazy reply into a typed value, matching the recovered
/// throwing contramap sequence: resolve PropertyList, then decode its type.
/// Remote/empty/parse failures never invoke the caller's payload decoder.
pub fn decode_reply_with<T, E, D>(
    payload: Option<LazyReply>,
    error: Option<E>,
    decode: impl FnOnce(&Value) -> Result<T, D>,
) -> Result<T, TypedReplyError<E, D>> {
    let reply = select_reply(payload, error).map_err(TypedReplyError::Reply)?;
    let fields = reply.property_list().map_err(TypedReplyError::Decode)?;
    decode(&Value::Dictionary(fields)).map_err(TypedReplyError::Payload)
}
/// The native Void success transform ignores LazyPropertyList without parsing.
/// Acknowledgement reports only callback-level success, never target settlement.
pub fn acknowledge_reply<E>(payload: Option<LazyReply>, error: Option<E>) -> Result<(), ReplyError<E>> {
    select_reply(payload, error).map(|_| ())
}
