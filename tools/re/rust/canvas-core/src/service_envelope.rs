//! Forward-only ServiceMessage value envelope. Message identifier is data;
//! decoding does not match replies, generate IDs, send, cancel or settle work.
use crate::{binary_plist,forward_payload::{self,ForwardPayload},payload_codec::Value};
use std::collections::BTreeMap;
pub const IDENTIFIER_KEY:&str="__unique_service_message_identifier";
#[derive(Clone,Debug,PartialEq)]
pub struct ForwardServiceEnvelope {
    pub identifier:Option<String>,
    pub forward:ForwardPayload,
}
#[derive(Clone,Debug,PartialEq,Eq)]
pub enum Error {Plist(binary_plist::Error),Missing(&'static str),Type(&'static str),UnsupportedMessageType,Forward(forward_payload::Error)}
impl ForwardServiceEnvelope {
    /// Allocate an identifier from the shared process sequence for a new
    /// forwarding request. This constructs a value and sends nothing.
    pub fn new(forward:ForwardPayload)->Self {
        Self {identifier:Some(crate::service_identifier::next_service_identifier()),forward}
    }
    /// Only the recovered forwarding subset. Unsupported outer kinds fail
    /// explicitly rather than being confused with the inner agent command.
    pub fn decode(value:&Value)->Result<Self,Error> {
        let Value::Dictionary(d)=value else {return Err(Error::Type("serviceMessage"));};
        let get=|k:&'static str|d.get(k).ok_or(Error::Missing(k));
        match get("messageType")? {Value::String(s) if s=="forward"=>{},Value::String(_)=>return Err(Error::UnsupportedMessageType),_=>return Err(Error::Type("messageType"))}
        let payload=get("payload")?;
        let Value::Dictionary(p)=payload else {return Err(Error::Type("payload"));};
        let identifier=match p.get(IDENTIFIER_KEY) {None=>None,Some(Value::String(s))=>Some(s.clone()),_=>return Err(Error::Type(IDENTIFIER_KEY))};
        let forward=ForwardPayload::decode(payload).map_err(Error::Forward)?;
        Ok(Self {identifier,forward})
    }
    pub fn decode_binary(bytes:&[u8])->Result<Self,Error> {Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)}
    /// Preserve the assigned or caller-supplied optional identifier.
    pub fn to_value(&self)->Value {
        let Value::Dictionary(mut payload)=self.forward.to_value() else {unreachable!()};
        if let Some(id)=&self.identifier {payload.insert(IDENTIFIER_KEY.into(),Value::String(id.clone()));}
        Value::Dictionary(BTreeMap::from([("messageType".into(),Value::String("forward".into())),("payload".into(),Value::Dictionary(payload))]))
    }
}
