//! Outgoing nullable response selection after the caller's connection gate.
//! NSError projection and Foundation serialization are supplied by the caller.
use crate::{
    payload_codec::Value, service_property_list::ServicePropertyList,
    service_reply_error::ServiceReplyError, settings_xpc::XpcValue,
};
use std::collections::BTreeMap;

/// Select a payload before considering an error. The caller supplies its live
/// connection observation; false skips projection and produces no response.
/// Missing or unprojectable errors likewise produce no response. No empty
/// response or EmptyReply error is synthesized on this outbound route.
/// This boolean is not a native weak-reference load or a lifetime guarantee.
pub fn select_service_response_with<E>(
    connection_available: bool,
    payload: Option<ServicePropertyList>,
    error: Option<E>,
    project_error: impl FnOnce(E) -> Option<ServiceReplyError>,
) -> Option<ServicePropertyList> {
    if !connection_available {
        return None;
    }
    if let Some(payload) = payload {
        return Some(payload);
    }
    let error = project_error(error?)?;
    Some(ServicePropertyList::Dictionary(error.to_dictionary()))
}

/// Encode the selected response into the supplied reply dictionary and call
/// send. Returning Some reports only that this local send function ran; T may
/// itself report failure. It does not prove delivery, acknowledgement or target
/// settlement. None leaves the reply dictionary unchanged and skips send.
///
/// The measured portable coder always writes a data entry, including empty
/// bytes on serialization failure. Its resulting XPC entry count is nonzero,
/// so the native error encoder's count-zero fallback is not entered in this
/// profile. Arbitrary native objects and alternate coders remain caller-owned.
pub fn send_service_response_with<E, D, T>(
    connection_available: bool,
    payload: Option<ServicePropertyList>,
    error: Option<E>,
    reply: &mut BTreeMap<String, XpcValue>,
    project_error: impl FnOnce(E) -> Option<ServiceReplyError>,
    encode: impl FnOnce(&BTreeMap<String, Value>) -> Result<Vec<u8>, D>,
    send: impl FnOnce(&BTreeMap<String, XpcValue>) -> T,
) -> Option<T> {
    let response =
        select_service_response_with(connection_available, payload, error, project_error)?;
    response.encode_to_xpc_dictionary_with(reply, encode);
    Some(send(reply))
}
