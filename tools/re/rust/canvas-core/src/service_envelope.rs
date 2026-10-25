//! Recovered ping/forward ServiceMessage value envelopes. Identifier is data;
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

/// Recovered outer content subset. Other native kinds remain unsupported.
#[derive(Clone, Debug, PartialEq)]
pub enum ServiceContent {
    Ping,
    Forward(ForwardPayload),
}
/// Value-only outer envelope. A ping is a message value, not a liveness result.
#[derive(Clone, Debug, PartialEq)]
pub struct ServiceEnvelope {
    pub identifier: Option<String>,
    pub content: ServiceContent,
}
impl ServiceEnvelope {
    /// Allocate from the existing process sequence. No send or reply is implied.
    pub fn new(content: ServiceContent) -> Self {
        Self {
            identifier: Some(crate::service_identifier::next_service_identifier()),
            content,
        }
    }
    pub fn decode(value: &Value) -> Result<Self, Error> {
        let Value::Dictionary(root) = value else {
            return Err(Error::Type("serviceMessage"));
        };
        let kind = root
            .get("messageType")
            .ok_or(Error::Missing("messageType"))?;
        match kind {
            Value::String(kind) if kind == "forward" => {
                let forward = ForwardServiceEnvelope::decode(value)?;
                Ok(Self {
                    identifier: forward.identifier,
                    content: ServiceContent::Forward(forward.forward),
                })
            }
            Value::String(kind) if kind == "ping" => {
                let payload = root.get("payload").ok_or(Error::Missing("payload"))?;
                let Value::Dictionary(payload) = payload else {
                    return Err(Error::Type("payload"));
                };
                let identifier = match payload.get(IDENTIFIER_KEY) {
                    None => None,
                    Some(Value::String(s)) => Some(s.clone()),
                    _ => return Err(Error::Type(IDENTIFIER_KEY)),
                };
                Ok(Self {
                    identifier,
                    content: ServiceContent::Ping,
                })
            }
            Value::String(_) => Err(Error::UnsupportedMessageType),
            _ => Err(Error::Type("messageType")),
        }
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    /// Ping has no content-specific fields. Unknown decoded fields are omitted
    /// on canonical output; the optional identifier belongs inside payload.
    pub fn to_value(&self) -> Value {
        let (kind, mut payload) = match &self.content {
            ServiceContent::Ping => ("ping", BTreeMap::new()),
            ServiceContent::Forward(forward) => {
                let Value::Dictionary(payload) = forward.to_value() else {
                    unreachable!()
                };
                ("forward", payload)
            }
        };
        if let Some(identifier) = &self.identifier {
            payload.insert(IDENTIFIER_KEY.into(), Value::String(identifier.clone()));
        }
        Value::Dictionary(BTreeMap::from([
            ("messageType".into(), Value::String(kind.into())),
            ("payload".into(), Value::Dictionary(payload)),
        ]))
    }
}
