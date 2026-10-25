//! Recovered service envelope subset. Identifier is data;
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
pub enum Error {Plist(binary_plist::Error),Missing(&'static str),Type(&'static str),UnsupportedMessageType,Forward(forward_payload::Error),Process(crate::service_process::Error)}
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
    /// Absent when content decoding fails; root and identifier errors still reject.
    Capabilities(Option<CapabilitiesPayload>),
    Forward(ForwardPayload),
    Connect(crate::service_process::ProcessTarget),
    Stop(crate::service_process::ProcessTarget),
    Kill(crate::service_process::ProcessTarget),
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
            Value::String(kind)
                if ["ping", "capabilities", "connect", "stop", "kill"].contains(&kind.as_str()) =>
            {
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
                    content: match kind.as_str() {
                        "ping" => ServiceContent::Ping,
                        "capabilities" => ServiceContent::Capabilities(
                            CapabilitiesPayload::decode_dictionary(payload).ok(),
                        ),
                        _ => {
                            let target = crate::service_process::ProcessTarget::decode_dictionary(payload)
                            .map_err(Error::Process)?;
                            match kind.as_str() {
                                "connect" => ServiceContent::Connect(target),
                                "stop" => ServiceContent::Stop(target),
                                _ => ServiceContent::Kill(target),
                            }
                        }
                    },
                })
            }
            Value::String(_) => Err(Error::UnsupportedMessageType),
            _ => Err(Error::Type("messageType")),
        }
    }
    pub fn decode_binary(bytes: &[u8]) -> Result<Self, Error> {
        Self::decode(&binary_plist::decode(bytes).map_err(Error::Plist)?)
    }
    /// Ping and absent capabilities have no content-specific fields. Unknown fields are omitted
    /// on canonical output; the optional identifier belongs inside payload.
    pub fn to_value(&self) -> Value {
        let (kind, mut payload) = match &self.content {
            ServiceContent::Ping => ("ping", BTreeMap::new()),
            ServiceContent::Capabilities(capabilities) => (
                "capabilities",
                capabilities
                    .as_ref()
                    .map_or_else(BTreeMap::new, CapabilitiesPayload::to_dictionary),
            ),
            ServiceContent::Connect(target) => ("connect", target.to_dictionary()),
            ServiceContent::Stop(target) => ("stop", target.to_dictionary()),
            ServiceContent::Kill(target) => ("kill", target.to_dictionary()),
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

/// Reported peer capability value, not ambient runtime detection or a negotiated
/// permission. The native default initializer's XTP detection is not invoked.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CapabilitiesPayload {
    pub is_running_in_xtp: bool,
}
impl CapabilitiesPayload {
    /// The primitive Foundation compatibility profile: Bool or numeric zero/one.
    /// Arbitrary Objective-C objects and future runtime bridging are not modeled.
    pub fn decode_dictionary(fields: &BTreeMap<String, Value>) -> Result<Self, Error> {
        let value = fields
            .get("isRunningInXTP")
            .ok_or(Error::Missing("isRunningInXTP"))?;
        let is_running_in_xtp = match value {
            Value::Boolean(value) => *value,
            Value::Integer(0) => false,
            Value::Integer(1) => true,
            Value::Real(value) if *value == 0.0 => false,
            Value::Real(value) if *value == 1.0 => true,
            _ => return Err(Error::Type("isRunningInXTP")),
        };
        Ok(Self { is_running_in_xtp })
    }
    pub fn to_dictionary(&self) -> BTreeMap<String, Value> {
        BTreeMap::from([(
            "isRunningInXTP".into(),
            Value::Boolean(self.is_running_in_xtp),
        )])
    }
}
